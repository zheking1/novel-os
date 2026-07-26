import hashlib
import logging
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value

logger = logging.getLogger("novel_os_mcp.services.canon")


class CanonService:
    def __init__(self, db: Database):
        self._db = db

    @staticmethod
    def _content_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in {"draft", "active", "deprecated", "archived"}:
            raise ValueError("status must be draft, active, deprecated, or archived")

    @staticmethod
    def _validate_review_status(review_status: str) -> None:
        if review_status not in {"pending", "approved", "rejected", "needs_review"}:
            raise ValueError("review_status must be pending, approved, rejected, or needs_review")

    async def upsert_document(
        self,
        project_id: str,
        doc_type: str,
        key: str,
        title: str,
        content: str,
        username: str,
        status: str = "active",
        scope: dict[str, Any] | None = None,
        review_status: str = "approved",
        source_type: str = "manual",
        source_id: str | None = None,
        related_rule_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        change_reason: str | None = None,
    ) -> dict[str, Any]:
        doc_type = doc_type.strip()
        key = key.strip()
        title = title.strip()
        if not doc_type:
            raise ValueError("doc_type is required")
        if not key:
            raise ValueError("key is required")
        if not title:
            raise ValueError("title is required")
        self._validate_status(status)
        self._validate_review_status(review_status)
        content_hash = self._content_hash(content)

        async with self._db.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
                if user is None:
                    raise ValueError(f"User not found: {username}")

                current = await conn.fetchrow(
                    """
                    SELECT id, version
                    FROM canon_documents
                    WHERE project_id = $1 AND doc_type = $2 AND key = $3
                    FOR UPDATE
                    """,
                    project_id,
                    doc_type,
                    key,
                )
                if current is None:
                    version = 1
                    row = await conn.fetchrow(
                        """
                        INSERT INTO canon_documents (
                          project_id, doc_type, key, title, content, content_hash, status, version,
                          scope, review_status, source_type, source_id, related_rule_ids, metadata,
                          created_by, updated_by
                        )
                        VALUES (
                          $1, $2, $3, $4, $5, $6, $7, 1,
                          $8::jsonb, $9, $10, $11, $12::text[], $13::jsonb,
                          $14, $14
                        )
                        RETURNING id::text, doc_type, key, title, content, content_hash, status, version,
                                  scope, review_status, source_type, source_id, related_rule_ids,
                                  metadata, created_by::text, updated_by::text, created_at, updated_at
                        """,
                        project_id,
                        doc_type,
                        key,
                        title,
                        content,
                        content_hash,
                        status,
                        json_dumps(scope or {}),
                        review_status,
                        source_type,
                        source_id,
                        related_rule_ids or [],
                        json_dumps(metadata or {}),
                        user["id"],
                    )
                    document_id = row["id"]
                else:
                    version = int(current["version"]) + 1
                    document_id = str(current["id"])
                    row = await conn.fetchrow(
                        """
                        UPDATE canon_documents
                        SET title = $4,
                            content = $5,
                            content_hash = $6,
                            status = $7,
                            version = $8,
                            scope = $9::jsonb,
                            review_status = $10,
                            source_type = $11,
                            source_id = $12,
                            related_rule_ids = $13::text[],
                            metadata = $14::jsonb,
                            updated_by = $15,
                            updated_at = now()
                        WHERE project_id = $1 AND doc_type = $2 AND key = $3
                        RETURNING id::text, doc_type, key, title, content, content_hash, status, version,
                                  scope, review_status, source_type, source_id, related_rule_ids,
                                  metadata, created_by::text, updated_by::text, created_at, updated_at
                        """,
                        project_id,
                        doc_type,
                        key,
                        title,
                        content,
                        content_hash,
                        status,
                        version,
                        json_dumps(scope or {}),
                        review_status,
                        source_type,
                        source_id,
                        related_rule_ids or [],
                        json_dumps(metadata or {}),
                        user["id"],
                    )

                await conn.execute(
                    """
                    INSERT INTO canon_document_versions (
                      project_id, document_id, version, title, content, content_hash, status,
                      scope, review_status, source_type, source_id, related_rule_ids, metadata,
                      change_reason, created_by
                    )
                    VALUES (
                      $1, $2, $3, $4, $5, $6, $7,
                      $8::jsonb, $9, $10, $11, $12::text[], $13::jsonb,
                      $14, $15
                    )
                    ON CONFLICT (document_id, version) DO NOTHING
                    """,
                    project_id,
                    document_id,
                    version,
                    title,
                    content,
                    content_hash,
                    status,
                    json_dumps(scope or {}),
                    review_status,
                    source_type,
                    source_id,
                    related_rule_ids or [],
                    json_dumps(metadata or {}),
                    change_reason,
                    user["id"],
                )
        return row_to_dict(row)

    async def list_documents(
        self,
        project_id: str,
        doc_types: list[str] | None = None,
        statuses: list[str] | None = None,
        review_status: str | None = None,
        query: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, doc_type, key, title, status, version, scope, review_status,
                   source_type, source_id, related_rule_ids, metadata,
                   created_by::text, updated_by::text, created_at, updated_at
            FROM canon_documents
            WHERE project_id = $1 AND is_deleted = false
              AND ($2::text[] IS NULL OR doc_type = ANY($2::text[]))
              AND ($3::text[] IS NULL OR status = ANY($3::text[]))
              AND ($4::text IS NULL OR review_status = $4)
              AND (
                $5::text IS NULL
                OR search_vector @@ plainto_tsquery('simple', $5)
                OR title ILIKE '%' || $5 || '%'
                OR key ILIKE '%' || $5 || '%'
              )
            ORDER BY
              CASE WHEN $5::text IS NULL THEN 0 ELSE ts_rank(search_vector, plainto_tsquery('simple', $5)) END DESC,
              updated_at DESC
            LIMIT $6 OFFSET $7
            """,
            project_id,
            doc_types,
            statuses,
            review_status,
            query.strip() if query else None,
            limit,
            offset,
        )
        return rows_to_dicts(rows)

    async def get_document(
        self,
        project_id: str,
        document_id: str | None = None,
        doc_type: str | None = None,
        key: str | None = None,
    ) -> dict[str, Any]:
        row = await self._fetch_document(project_id=project_id, document_id=document_id, doc_type=doc_type, key=key)
        return row_to_dict(row)

    async def archive_document(
        self,
        project_id: str,
        username: str,
        document_id: str | None = None,
        doc_type: str | None = None,
        key: str | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        async with self._db.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
                if user is None:
                    raise ValueError(f"User not found: {username}")
                current = await self._fetch_document_for_update(
                    conn=conn,
                    project_id=project_id,
                    document_id=document_id,
                    doc_type=doc_type,
                    key=key,
                )
                version = int(current["version"]) + 1
                row = await conn.fetchrow(
                    """
                    UPDATE canon_documents
                    SET status = 'archived',
                        version = $3,
                        updated_by = $4,
                        updated_at = now()
                    WHERE project_id = $1 AND id = $2
                    RETURNING id::text, doc_type, key, title, content, content_hash, status, version,
                              scope, review_status, source_type, source_id, related_rule_ids,
                              metadata, created_by::text, updated_by::text, created_at, updated_at
                    """,
                    project_id,
                    current["id"],
                    version,
                    user["id"],
                )
                await conn.execute(
                    """
                    INSERT INTO canon_document_versions (
                      project_id, document_id, version, title, content, content_hash, status,
                      scope, review_status, source_type, source_id, related_rule_ids, metadata,
                      change_reason, created_by
                    )
                    VALUES (
                      $1, $2, $3, $4, $5, $6, 'archived',
                      $7::jsonb, $8, 'archive', $9, $10::text[], $11::jsonb,
                      $12, $13
                    )
                    """,
                    project_id,
                    current["id"],
                    version,
                    current["title"],
                    current["content"],
                    current["content_hash"],
                    json_dumps(ensure_json_value(current["scope"]) or {}),
                    current["review_status"],
                    str(current["id"]),
                    current["related_rule_ids"] or [],
                    json_dumps(ensure_json_value(current["metadata"]) or {}),
                    reason,
                    user["id"],
                )
        return row_to_dict(row)

    async def list_document_versions(
        self,
        project_id: str,
        document_id: str | None = None,
        doc_type: str | None = None,
        key: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        document = await self._fetch_document(project_id=project_id, document_id=document_id, doc_type=doc_type, key=key)
        rows = await self._db.fetch(
            """
            SELECT id::text, document_id::text, version, title, content, content_hash, status,
                   scope, review_status, source_type, source_id, related_rule_ids, metadata,
                   change_reason, created_by::text, created_at
            FROM canon_document_versions
            WHERE project_id = $1 AND document_id = $2
            ORDER BY version DESC
            LIMIT $3
            """,
            project_id,
            document["id"],
            limit,
        )
        return rows_to_dicts(rows)

    async def restore_document(
        self,
        project_id: str,
        version: int,
        username: str,
        document_id: str | None = None,
        doc_type: str | None = None,
        key: str | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        async with self._db.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
                if user is None:
                    raise ValueError(f"User not found: {username}")
                current = await self._fetch_document_for_update(
                    conn=conn,
                    project_id=project_id,
                    document_id=document_id,
                    doc_type=doc_type,
                    key=key,
                )
                source = await conn.fetchrow(
                    """
                    SELECT *
                    FROM canon_document_versions
                    WHERE project_id = $1 AND document_id = $2 AND version = $3
                    """,
                    project_id,
                    current["id"],
                    version,
                )
                if source is None:
                    raise ValueError(f"Canon document version not found: {version}")
                next_version = int(current["version"]) + 1
                row = await conn.fetchrow(
                    """
                    UPDATE canon_documents
                    SET title = $3,
                        content = $4,
                        content_hash = $5,
                        status = $6,
                        version = $7,
                        scope = $8::jsonb,
                        review_status = $9,
                        source_type = 'restore',
                        source_id = $10,
                        related_rule_ids = $11::text[],
                        metadata = $12::jsonb,
                        updated_by = $13,
                        updated_at = now()
                    WHERE project_id = $1 AND id = $2
                    RETURNING id::text, doc_type, key, title, content, content_hash, status, version,
                              scope, review_status, source_type, source_id, related_rule_ids,
                              metadata, created_by::text, updated_by::text, created_at, updated_at
                    """,
                    project_id,
                    current["id"],
                    source["title"],
                    source["content"],
                    source["content_hash"],
                    source["status"],
                    next_version,
                    json_dumps(ensure_json_value(source["scope"]) or {}),
                    source["review_status"],
                    str(source["id"]),
                    source["related_rule_ids"] or [],
                    json_dumps(ensure_json_value(source["metadata"]) or {}),
                    user["id"],
                )
                await conn.execute(
                    """
                    INSERT INTO canon_document_versions (
                      project_id, document_id, version, title, content, content_hash, status,
                      scope, review_status, source_type, source_id, related_rule_ids, metadata,
                      change_reason, created_by
                    )
                    VALUES (
                      $1, $2, $3, $4, $5, $6, $7,
                      $8::jsonb, $9, 'restore', $10, $11::text[], $12::jsonb,
                      $13, $14
                    )
                    """,
                    project_id,
                    current["id"],
                    next_version,
                    source["title"],
                    source["content"],
                    source["content_hash"],
                    source["status"],
                    json_dumps(ensure_json_value(source["scope"]) or {}),
                    source["review_status"],
                    str(source["id"]),
                    source["related_rule_ids"] or [],
                    json_dumps(ensure_json_value(source["metadata"]) or {}),
                    reason,
                    user["id"],
                )
        return row_to_dict(row)

    async def _fetch_document(
        self,
        project_id: str,
        document_id: str | None = None,
        doc_type: str | None = None,
        key: str | None = None,
    ):
        if document_id:
            row = await self._db.fetchrow(
                """
                SELECT id, id::text AS id_text, doc_type, key, title, content, content_hash, status, version,
                       scope, review_status, source_type, source_id, related_rule_ids, metadata,
                       created_by::text, updated_by::text, created_at, updated_at
                FROM canon_documents
                WHERE project_id = $1 AND id = $2::uuid
                """,
                project_id,
                document_id,
            )
        elif doc_type and key:
            row = await self._db.fetchrow(
                """
                SELECT id, id::text AS id_text, doc_type, key, title, content, content_hash, status, version,
                       scope, review_status, source_type, source_id, related_rule_ids, metadata,
                       created_by::text, updated_by::text, created_at, updated_at
                FROM canon_documents
                WHERE project_id = $1 AND doc_type = $2 AND key = $3
                """,
                project_id,
                doc_type,
                key,
            )
        elif key:
            row = await self._db.fetchrow(
                """
                SELECT id, id::text AS id_text, doc_type, key, title, content, content_hash, status, version,
                       scope, review_status, source_type, source_id, related_rule_ids, metadata,
                       created_by::text, updated_by::text, created_at, updated_at
                FROM canon_documents
                WHERE project_id = $1 AND key = $2
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                project_id,
                key,
            )
        else:
            raise ValueError("document_id or doc_type + key or key is required")
        if row is None:
            raise ValueError("Canon document not found")
        result = dict(row)
        result["id"] = result.pop("id_text")
        return result

    async def _fetch_document_for_update(
        self,
        conn,
        project_id: str,
        document_id: str | None = None,
        doc_type: str | None = None,
        key: str | None = None,
    ):
        if document_id:
            row = await conn.fetchrow(
                """
                SELECT *
                FROM canon_documents
                WHERE project_id = $1 AND id = $2::uuid
                FOR UPDATE
                """,
                project_id,
                document_id,
            )
        elif doc_type and key:
            row = await conn.fetchrow(
                """
                SELECT *
                FROM canon_documents
                WHERE project_id = $1 AND doc_type = $2 AND key = $3
                FOR UPDATE
                """,
                project_id,
                doc_type,
                key,
            )
        elif key:
            row = await conn.fetchrow(
                """
                SELECT *
                FROM canon_documents
                WHERE project_id = $1 AND key = $2
                ORDER BY updated_at DESC
                LIMIT 1
                FOR UPDATE
                """,
                project_id,
                key,
            )
        else:
            raise ValueError("document_id or doc_type + key or key is required")
        if row is None:
            raise ValueError("Canon document not found")
        return row
