import logging
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value

logger = logging.getLogger("novel_os_mcp.services.memory")


class MemoryService:
    def __init__(self, db: Database, embedding_service: Any = None, vector_index: Any = None):
        self._db = db
        self._embedding_service = embedding_service
        self._vector_index = vector_index

    async def search(
        self,
        project_id: str,
        query: str,
        source_types: list[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search memory chunks. Tries semantic search first, falls back to keyword."""
        # Try semantic search if embedding service available
        if self._embedding_service and self._vector_index:
            try:
                results = await self.semantic_search(project_id, query, source_types, limit)
                if results:
                    return results
            except Exception:
                logger.debug("Semantic search unavailable, falling back to keyword", exc_info=True)

        # Keyword search (fallback)
        rows = await self._db.fetch(
            """
            SELECT id::text, source_type, source_id::text, chunk_key, content, metadata,
                   ts_rank(search_vector, plainto_tsquery('simple', $2)) AS rank
            FROM memory_chunks
            WHERE project_id = $1
              AND search_vector @@ plainto_tsquery('simple', $2)
              AND ($3::text[] IS NULL OR source_type = ANY($3::text[]))
            ORDER BY rank DESC, created_at DESC
            LIMIT $4
            """,
            project_id,
            query,
            source_types,
            limit,
        )
        return rows_to_dicts(rows)

    async def semantic_search(
        self,
        project_id: str,
        query: str,
        source_types: list[str] | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Semantic search using embeddings + Qdrant vector similarity."""
        from .config import Settings
        settings = Settings()
        collection = settings.qdrant_memory_collection

        # Get query embedding
        query_vector = await self._embedding_service.embed_single(project_id, query)
        if not query_vector:
            return []

        # Search Qdrant
        qdrant_results = await self._vector_index.search(
            collection=collection,
            vector=query_vector,
            limit=limit * 2,  # Over-fetch for filtering
            project_id=project_id,
        )
        if not qdrant_results:
            return []

        # Extract point IDs and fetch from PostgreSQL
        point_ids = [r["id"] for r in qdrant_results]
        scores = {r["id"]: r["score"] for r in qdrant_results}

        if not point_ids:
            return []

        # Fetch matching memory chunks by qdrant_point_id
        rows = await self._db.fetch(
            """
            SELECT id::text, source_type, source_id::text, chunk_key, content, metadata,
                   qdrant_point_id
            FROM memory_chunks
            WHERE project_id = $1
              AND qdrant_point_id = ANY($2::text[])
              AND ($3::text[] IS NULL OR source_type = ANY($3::text[]))
            """,
            project_id,
            point_ids,
            source_types,
        )

        # Merge results with scores
        results = []
        for row in rows:
            rd = row_to_dict(row)
            rd["score"] = scores.get(rd.get("qdrant_point_id", ""), 0.0)
            results.append(rd)

        # Sort by score descending
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:limit]

    async def vectorize_chunk(
        self,
        project_id: str,
        chunk_id: str,
        content: str,
    ) -> bool:
        """Generate embedding for a memory chunk and store in Qdrant."""
        if not self._embedding_service or not self._vector_index:
            return False

        try:
            from .config import Settings
            settings = Settings()
            collection = settings.qdrant_memory_collection

            # Get embedding
            vector = await self._embedding_service.embed_single(project_id, content)
            if not vector:
                return False

            # Store in Qdrant
            await self._vector_index.upsert_memory_point(
                collection=collection,
                point_id=chunk_id,
                vector=vector,
                payload={"project_id": project_id, "chunk_id": chunk_id},
            )

            # Mark as indexed in PostgreSQL
            await self._db.execute(
                """
                UPDATE memory_chunks
                SET qdrant_collection = $3, qdrant_point_id = $4
                WHERE id = $1 AND project_id = $2
                """,
                chunk_id, project_id, collection, chunk_id,
            )
            return True
        except Exception:
            return False

    async def vectorize_pending_chunks(
        self,
        project_id: str,
        batch_size: int = 10,
    ) -> dict[str, Any]:
        """Vectorize all pending memory chunks for a project."""
        if not self._embedding_service or not self._vector_index:
            return {"vectorized": 0, "failed": 0, "skipped": True}

        # Get pending chunks
        rows = await self._db.fetch(
            """
            SELECT id::text, content
            FROM memory_chunks
            WHERE project_id = $1
              AND qdrant_point_id IS NULL
            ORDER BY created_at
            LIMIT $2
            """,
            project_id, batch_size,
        )

        vectorized = 0
        failed = 0
        for row in rows:
            success = await self.vectorize_chunk(
                project_id=project_id,
                chunk_id=row["id"],
                content=row["content"],
            )
            if success:
                vectorized += 1
            else:
                failed += 1

        return {"vectorized": vectorized, "failed": failed, "skipped": False}

    async def get_state(self, project_id: str, entity_type: str, name: str) -> dict[str, Any] | None:
        row = await self._db.fetchrow(
            """
            SELECT e.id::text AS entity_id, e.entity_type, e.name, e.aliases, e.profile,
                   e.lifecycle_status, e.importance, e.tags,
                   e.first_seen_chapter_no, e.last_seen_chapter_no,
                   e.first_seen_volume_no, e.last_seen_volume_no,
                   e.source_type AS entity_source_type, e.source_id AS entity_source_id,
                   e.metadata AS entity_metadata,
                   s.id::text AS snapshot_id, s.state, s.effective_chapter_no, s.expire_chapter_no,
                   s.effective_volume_no, s.expire_volume_no, s.duration_type, s.expires_on_event,
                   s.confidence, s.source_type, s.source_id, s.change_reason, s.metadata, s.created_at
            FROM state_entities e
            LEFT JOIN LATERAL (
              SELECT id, state, effective_chapter_no, expire_chapter_no,
                     effective_volume_no, expire_volume_no, duration_type, expires_on_event,
                     confidence, source_type, source_id, change_reason, metadata, created_at
              FROM state_snapshots
              WHERE project_id = e.project_id AND entity_id = e.id AND is_current = true
              ORDER BY created_at DESC
              LIMIT 1
            ) s ON true
            WHERE e.project_id = $1 AND e.entity_type = $2 AND e.name = $3
            """,
            project_id,
            entity_type,
            name,
        )
        return row_to_dict(row)

    async def _resolve_entity(
        self,
        conn,
        project_id: str,
        entity_id: str | None = None,
        entity_type: str | None = None,
        name: str | None = None,
        create_if_missing: bool = False,
    ):
        if entity_id:
            entity = await conn.fetchrow(
                """
                SELECT id, id::text AS entity_id, entity_type, name
                FROM state_entities
                WHERE project_id = $1 AND id = $2
                """,
                project_id,
                entity_id,
            )
            if entity is None:
                raise ValueError(f"Entity not found: {entity_id}")
            return entity
        if not entity_type or not name:
            raise ValueError("entity_id or entity_type+name is required")
        if create_if_missing:
            return await conn.fetchrow(
                """
                INSERT INTO state_entities (project_id, entity_type, name)
                VALUES ($1, $2, $3)
                ON CONFLICT (project_id, entity_type, name)
                DO UPDATE SET updated_at = now()
                RETURNING id, id::text AS entity_id, entity_type, name
                """,
                project_id,
                entity_type,
                name,
            )
        entity = await conn.fetchrow(
            """
            SELECT id, id::text AS entity_id, entity_type, name
            FROM state_entities
            WHERE project_id = $1 AND entity_type = $2 AND name = $3
            """,
            project_id,
            entity_type,
            name,
        )
        if entity is None:
            raise ValueError(f"Entity not found: {entity_type}:{name}")
        return entity

    async def upsert_entity(
        self,
        project_id: str,
        entity_type: str,
        name: str,
        aliases: list[str] | None = None,
        summary: str | None = None,
        description: str | None = None,
        portrait_url: str | None = None,
        profile: dict[str, Any] | None = None,
        lifecycle_status: str = "active",
        importance: str = "medium",
        tags: list[str] | None = None,
        first_seen_chapter_no: int | None = None,
        last_seen_chapter_no: int | None = None,
        first_seen_volume_no: int | None = None,
        last_seen_volume_no: int | None = None,
        source_type: str = "manual",
        source_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO state_entities (
              project_id, entity_type, name, aliases, summary, description, portrait_url,
              profile, lifecycle_status, importance, tags,
              first_seen_chapter_no, last_seen_chapter_no, first_seen_volume_no, last_seen_volume_no,
              source_type, source_id, metadata
            )
            VALUES (
              $1, $2, $3, COALESCE($4::text[], ARRAY[]::text[]),
              $5, $6, $7,
              $8::jsonb, $9, $10,
              COALESCE($11::text[], ARRAY[]::text[]),
              $12, $13, $14, $15,
              $16, $17, $18::jsonb
            )
            ON CONFLICT (project_id, entity_type, name)
            DO UPDATE SET aliases = CASE WHEN $4::text[] IS NULL THEN state_entities.aliases ELSE EXCLUDED.aliases END,
                          summary = COALESCE(EXCLUDED.summary, state_entities.summary),
                          description = COALESCE(EXCLUDED.description, state_entities.description),
                          portrait_url = COALESCE(EXCLUDED.portrait_url, state_entities.portrait_url),
                          profile = state_entities.profile || EXCLUDED.profile,
                          lifecycle_status = EXCLUDED.lifecycle_status,
                          importance = EXCLUDED.importance,
                          tags = CASE WHEN $11::text[] IS NULL THEN state_entities.tags ELSE EXCLUDED.tags END,
                          first_seen_chapter_no = COALESCE(EXCLUDED.first_seen_chapter_no, state_entities.first_seen_chapter_no),
                          last_seen_chapter_no = COALESCE(EXCLUDED.last_seen_chapter_no, state_entities.last_seen_chapter_no),
                          first_seen_volume_no = COALESCE(EXCLUDED.first_seen_volume_no, state_entities.first_seen_volume_no),
                          last_seen_volume_no = COALESCE(EXCLUDED.last_seen_volume_no, state_entities.last_seen_volume_no),
                          source_type = EXCLUDED.source_type,
                          source_id = COALESCE(EXCLUDED.source_id, state_entities.source_id),
                          metadata = state_entities.metadata || EXCLUDED.metadata,
                          updated_at = now()
            RETURNING id::text, entity_type, name, aliases, summary, description, portrait_url,
                      profile, lifecycle_status, importance, tags,
                      first_seen_chapter_no, last_seen_chapter_no, first_seen_volume_no, last_seen_volume_no,
                      source_type, source_id, metadata, created_at, updated_at
            """,
            project_id,
            entity_type,
            name,
            aliases,
            summary,
            description,
            portrait_url,
            json_dumps(profile or {}),
            lifecycle_status,
            importance,
            tags,
            first_seen_chapter_no,
            last_seen_chapter_no,
            first_seen_volume_no,
            last_seen_volume_no,
            source_type,
            source_id,
            json_dumps(metadata or {}),
        )
        return row_to_dict(row)

    async def list_entities(
        self,
        project_id: str,
        entity_type: str | None = None,
        lifecycle_status: str | None = None,
        query: str | None = None,
        tags: list[str] | None = None,
        include_archived: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT e.id::text, e.entity_type, e.name, e.aliases, e.summary, e.description, e.portrait_url,
                   e.profile, e.lifecycle_status,
                   e.importance, e.tags, e.first_seen_chapter_no, e.last_seen_chapter_no,
                   e.first_seen_volume_no, e.last_seen_volume_no, e.source_type, e.source_id,
                   e.metadata, e.created_at, e.updated_at,
                   s.id::text AS current_snapshot_id, s.state AS current_state
            FROM state_entities e
            LEFT JOIN LATERAL (
              SELECT id, state
              FROM state_snapshots
              WHERE project_id = e.project_id AND entity_id = e.id AND is_current = true
              ORDER BY created_at DESC
              LIMIT 1
            ) s ON true
            WHERE e.project_id = $1
              AND ($2::text IS NULL OR e.entity_type = $2)
              AND ($3::text IS NULL OR e.lifecycle_status = $3)
              AND ($4::text IS NULL OR e.name ILIKE ('%' || $4 || '%') OR $4 = ANY(e.aliases))
              AND ($5::text[] IS NULL OR e.tags && $5::text[])
              AND ($6::boolean = true OR e.lifecycle_status <> 'archived')
            ORDER BY e.entity_type, e.name
            LIMIT $7 OFFSET $8
            """,
            project_id,
            entity_type,
            lifecycle_status,
            query,
            tags,
            include_archived,
            limit,
            offset,
        )
        return rows_to_dicts(rows)

    async def get_entity(
        self,
        project_id: str,
        entity_id: str | None = None,
        entity_type: str | None = None,
        name: str | None = None,
    ) -> dict[str, Any] | None:
        async with self._db.acquire() as conn:
            entity = await self._resolve_entity(
                conn,
                project_id=project_id,
                entity_id=entity_id,
                entity_type=entity_type,
                name=name,
                create_if_missing=False,
            )
            row = await conn.fetchrow(
                """
                SELECT e.id::text, e.entity_type, e.name, e.aliases, e.summary, e.description, e.portrait_url,
                       e.profile, e.lifecycle_status,
                       e.importance, e.tags, e.first_seen_chapter_no, e.last_seen_chapter_no,
                       e.first_seen_volume_no, e.last_seen_volume_no, e.source_type, e.source_id,
                       e.metadata, e.created_at, e.updated_at,
                       s.id::text AS current_snapshot_id, s.state AS current_state,
                       s.effective_chapter_no, s.expire_chapter_no, s.effective_volume_no,
                       s.expire_volume_no, s.duration_type, s.expires_on_event,
                       s.confidence, s.change_reason
                FROM state_entities e
                LEFT JOIN LATERAL (
                  SELECT id, state, effective_chapter_no, expire_chapter_no,
                         effective_volume_no, expire_volume_no, duration_type, expires_on_event,
                         confidence, change_reason
                  FROM state_snapshots
                  WHERE project_id = e.project_id AND entity_id = e.id AND is_current = true
                  ORDER BY created_at DESC
                  LIMIT 1
                ) s ON true
                WHERE e.project_id = $1 AND e.id = $2
                """,
                project_id,
                entity["id"],
            )
        return row_to_dict(row)

    async def bulk_patch_entities(
        self,
        project_id: str,
        entity_ids: list[str],
        patch: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not entity_ids:
            return []
        allowed = {
            "aliases",
            "profile",
            "lifecycle_status",
            "importance",
            "tags",
            "first_seen_chapter_no",
            "last_seen_chapter_no",
            "first_seen_volume_no",
            "last_seen_volume_no",
            "source_type",
            "source_id",
            "metadata",
        }
        unknown = set(patch) - allowed
        if unknown:
            raise ValueError(f"Unsupported entity patch fields: {', '.join(sorted(unknown))}")
        rows = await self._db.fetch(
            """
            UPDATE state_entities
            SET aliases = CASE WHEN $3::text[] IS NULL THEN aliases ELSE $3::text[] END,
                profile = profile || $4::jsonb,
                lifecycle_status = COALESCE($5::text, lifecycle_status),
                importance = COALESCE($6::text, importance),
                tags = CASE WHEN $7::text[] IS NULL THEN tags ELSE $7::text[] END,
                first_seen_chapter_no = COALESCE($8::int, first_seen_chapter_no),
                last_seen_chapter_no = COALESCE($9::int, last_seen_chapter_no),
                first_seen_volume_no = COALESCE($10::int, first_seen_volume_no),
                last_seen_volume_no = COALESCE($11::int, last_seen_volume_no),
                source_type = COALESCE($12::text, source_type),
                source_id = COALESCE($13::text, source_id),
                metadata = metadata || $14::jsonb,
                updated_at = now()
            WHERE project_id = $1 AND id = ANY($2::uuid[])
            RETURNING id::text, entity_type, name, aliases, profile, lifecycle_status,
                      importance, tags, first_seen_chapter_no, last_seen_chapter_no,
                      first_seen_volume_no, last_seen_volume_no, source_type, source_id,
                      metadata, created_at, updated_at
            """,
            project_id,
            entity_ids,
            patch.get("aliases") if "aliases" in patch else None,
            json_dumps(patch.get("profile", {})),
            patch.get("lifecycle_status"),
            patch.get("importance"),
            patch.get("tags") if "tags" in patch else None,
            patch.get("first_seen_chapter_no"),
            patch.get("last_seen_chapter_no"),
            patch.get("first_seen_volume_no"),
            patch.get("last_seen_volume_no"),
            patch.get("source_type"),
            patch.get("source_id"),
            json_dumps(patch.get("metadata", {})),
        )
        return rows_to_dicts(rows)

    async def upsert_snapshot(
        self,
        project_id: str,
        state: dict[str, Any],
        entity_id: str | None = None,
        entity_type: str | None = None,
        name: str | None = None,
        chapter_no: int | None = None,
        chapter_id: str | None = None,
        source_commit_id: str | None = None,
        is_current: bool = True,
        effective_chapter_no: int | None = None,
        expire_chapter_no: int | None = None,
        effective_volume_no: int | None = None,
        expire_volume_no: int | None = None,
        duration_type: str = "persistent",
        expires_on_event: str | None = None,
        confidence: float | None = None,
        source_type: str = "manual",
        source_id: str | None = None,
        change_reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with self._db.acquire() as conn:
            async with conn.transaction():
                entity = await self._resolve_entity(
                    conn,
                    project_id=project_id,
                    entity_id=entity_id,
                    entity_type=entity_type,
                    name=name,
                    create_if_missing=True,
                )
                if chapter_id is None and chapter_no is not None:
                    chapter = await conn.fetchrow(
                        "SELECT id FROM chapters WHERE project_id = $1 AND chapter_no = $2",
                        project_id,
                        chapter_no,
                    )
                    chapter_id = str(chapter["id"]) if chapter else None
                if is_current:
                    await conn.execute(
                        """
                        UPDATE state_snapshots
                        SET is_current = false
                        WHERE project_id = $1 AND entity_id = $2
                        """,
                        project_id,
                        entity["id"],
                    )
                row = await conn.fetchrow(
                    """
                    INSERT INTO state_snapshots (
                      project_id, entity_id, chapter_id, state, is_current, source_commit_id,
                      effective_chapter_no, expire_chapter_no, effective_volume_no, expire_volume_no,
                      duration_type, expires_on_event, confidence, source_type, source_id,
                      change_reason, metadata
                    )
                    VALUES (
                      $1, $2, $3, $4::jsonb, $5, $6,
                      $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17::jsonb
                    )
                    RETURNING id::text, entity_id::text, chapter_id::text, state, is_current,
                              source_commit_id::text, effective_chapter_no, expire_chapter_no,
                              effective_volume_no, expire_volume_no, duration_type, expires_on_event,
                              confidence, source_type, source_id, change_reason, metadata, created_at
                    """,
                    project_id,
                    entity["id"],
                    chapter_id,
                    json_dumps(state),
                    is_current,
                    source_commit_id,
                    effective_chapter_no,
                    expire_chapter_no,
                    effective_volume_no,
                    expire_volume_no,
                    duration_type,
                    expires_on_event,
                    confidence,
                    source_type,
                    source_id,
                    change_reason,
                    json_dumps(metadata or {}),
                )
        result = row_to_dict(row)
        result["entity_type"] = entity["entity_type"]
        result["name"] = entity["name"]
        return result

    async def list_snapshots(
        self,
        project_id: str,
        entity_id: str | None = None,
        entity_type: str | None = None,
        name: str | None = None,
        current_only: bool = False,
        current_chapter_no: int | None = None,
        include_expired: bool = True,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT s.id::text, s.entity_id::text, e.entity_type, e.name, s.chapter_id::text,
                   s.state, s.is_current, s.source_commit_id::text,
                   s.effective_chapter_no, s.expire_chapter_no, s.effective_volume_no,
                   s.expire_volume_no, s.duration_type, s.expires_on_event, s.confidence,
                   s.source_type, s.source_id, s.change_reason, s.metadata, s.created_at
            FROM state_snapshots s
            JOIN state_entities e ON e.id = s.entity_id
            WHERE s.project_id = $1
              AND ($2::uuid IS NULL OR s.entity_id = $2)
              AND ($3::text IS NULL OR e.entity_type = $3)
              AND ($4::text IS NULL OR e.name = $4)
              AND ($5::boolean = false OR s.is_current = true)
              AND (
                $7::boolean = true OR $6::int IS NULL OR
                (s.effective_chapter_no IS NULL OR s.effective_chapter_no <= $6)
              )
              AND (
                $7::boolean = true OR $6::int IS NULL OR
                (s.expire_chapter_no IS NULL OR s.expire_chapter_no >= $6)
              )
            ORDER BY s.created_at DESC
            LIMIT $8
            """,
            project_id,
            entity_id,
            entity_type,
            name,
            current_only,
            current_chapter_no,
            include_expired,
            limit,
        )
        return rows_to_dicts(rows)

    async def get_snapshot_at_chapter(
        self,
        project_id: str,
        entity_name: str,
        chapter_no: int,
    ) -> dict[str, Any]:
        """Get the state snapshot that was effective at a specific chapter."""
        row = await self._db.fetchrow(
            """
            SELECT s.id::text, s.entity_id::text, e.entity_type, e.name, s.chapter_id::text,
                   s.state, s.is_current,
                   s.effective_chapter_no, s.expire_chapter_no,
                   s.duration_type, s.change_reason, s.source_type, s.metadata,
                   s.created_at
            FROM state_snapshots s
            JOIN state_entities e ON e.id = s.entity_id
            WHERE s.project_id = $1
              AND e.name = $2
              AND (s.effective_chapter_no IS NULL OR s.effective_chapter_no <= $3)
              AND (s.expire_chapter_no IS NULL OR s.expire_chapter_no >= $3)
            ORDER BY s.effective_chapter_no DESC NULLS LAST, s.created_at DESC
            LIMIT 1
            """,
            project_id,
            entity_name,
            chapter_no,
        )
        if not row:
            return {"found": False, "entity_name": entity_name, "chapter_no": chapter_no}

        result = row_to_dict(row)
        result["found"] = True
        return result

    async def get_entity_state_timeline(
        self,
        project_id: str,
        entity_name: str,
        start_chapter: int = 1,
        end_chapter: int | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get the state change timeline for an entity across chapters."""
        rows = await self._db.fetch(
            """
            SELECT DISTINCT ON (s.effective_chapter_no, s.chapter_id)
                   s.id::text, s.effective_chapter_no, s.expire_chapter_no,
                   s.state, s.change_reason, s.source_type, s.duration_type,
                   s.created_at
            FROM state_snapshots s
            JOIN state_entities e ON e.id = s.entity_id
            WHERE s.project_id = $1
              AND e.name = $2
              AND ($3::int IS NULL OR s.effective_chapter_no >= $3 OR s.effective_chapter_no IS NULL)
              AND ($4::int IS NULL OR s.effective_chapter_no <= $4)
            ORDER BY s.effective_chapter_no, s.chapter_id, s.created_at DESC
            LIMIT $5
            """,
            project_id,
            entity_name,
            start_chapter,
            end_chapter,
            limit,
        )
        return rows_to_dicts(rows)

    async def upsert_relationship(
        self,
        project_id: str,
        relation_type: str,
        source_entity_id: str | None = None,
        source_entity_type: str | None = None,
        source_name: str | None = None,
        target_entity_id: str | None = None,
        target_entity_type: str | None = None,
        target_name: str | None = None,
        attitude: str | None = None,
        intensity: float | None = None,
        known_by_source: bool = True,
        known_by_target: bool = True,
        known_by_reader: bool = True,
        status: str = "active",
        source_chapter_no: int | None = None,
        source_chapter_id: str | None = None,
        source_commit_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with self._db.acquire() as conn:
            async with conn.transaction():
                source = await self._resolve_entity(
                    conn,
                    project_id,
                    entity_id=source_entity_id,
                    entity_type=source_entity_type,
                    name=source_name,
                    create_if_missing=True,
                )
                target = await self._resolve_entity(
                    conn,
                    project_id,
                    entity_id=target_entity_id,
                    entity_type=target_entity_type,
                    name=target_name,
                    create_if_missing=True,
                )
                if source_chapter_id is None and source_chapter_no is not None:
                    chapter = await conn.fetchrow(
                        "SELECT id FROM chapters WHERE project_id = $1 AND chapter_no = $2",
                        project_id,
                        source_chapter_no,
                    )
                    source_chapter_id = str(chapter["id"]) if chapter else None
                row = await conn.fetchrow(
                    """
                    INSERT INTO entity_relationships (
                      project_id, source_entity_id, target_entity_id, relation_type,
                      attitude, intensity, known_by_source, known_by_target, known_by_reader,
                      status, source_chapter_no, source_chapter_id, source_commit_id, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14::jsonb)
                    ON CONFLICT (project_id, source_entity_id, target_entity_id, relation_type)
                    DO UPDATE SET attitude = EXCLUDED.attitude,
                                  intensity = EXCLUDED.intensity,
                                  known_by_source = EXCLUDED.known_by_source,
                                  known_by_target = EXCLUDED.known_by_target,
                                  known_by_reader = EXCLUDED.known_by_reader,
                                  status = EXCLUDED.status,
                                  source_chapter_no = COALESCE(EXCLUDED.source_chapter_no, entity_relationships.source_chapter_no),
                                  source_chapter_id = COALESCE(EXCLUDED.source_chapter_id, entity_relationships.source_chapter_id),
                                  source_commit_id = COALESCE(EXCLUDED.source_commit_id, entity_relationships.source_commit_id),
                                  metadata = entity_relationships.metadata || EXCLUDED.metadata,
                                  updated_at = now()
                    RETURNING id::text, source_entity_id::text, target_entity_id::text, relation_type,
                              attitude, intensity, known_by_source, known_by_target, known_by_reader,
                              status, source_chapter_no, source_chapter_id::text, source_commit_id::text,
                              metadata, created_at, updated_at
                    """,
                    project_id,
                    source["id"],
                    target["id"],
                    relation_type,
                    attitude,
                    intensity,
                    known_by_source,
                    known_by_target,
                    known_by_reader,
                    status,
                    source_chapter_no,
                    source_chapter_id,
                    source_commit_id,
                    json_dumps(metadata or {}),
                )
        result = row_to_dict(row)
        result["source"] = {"entity_type": source["entity_type"], "name": source["name"]}
        result["target"] = {"entity_type": target["entity_type"], "name": target["name"]}
        return result

    async def list_relationships(
        self,
        project_id: str,
        entity_id: str | None = None,
        entity_type: str | None = None,
        name: str | None = None,
        relation_type: str | None = None,
        status: str | None = "active",
        include_reader_hidden: bool = True,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT r.id::text, r.source_entity_id::text, se.entity_type AS source_entity_type,
                   se.name AS source_name, r.target_entity_id::text,
                   te.entity_type AS target_entity_type, te.name AS target_name,
                   r.relation_type, r.attitude, r.intensity, r.known_by_source,
                   r.known_by_target, r.known_by_reader, r.status, r.source_chapter_no,
                   r.source_chapter_id::text, r.source_commit_id::text, r.metadata,
                   r.created_at, r.updated_at
            FROM entity_relationships r
            JOIN state_entities se ON se.id = r.source_entity_id
            JOIN state_entities te ON te.id = r.target_entity_id
            WHERE r.project_id = $1
              AND (
                $2::uuid IS NULL OR r.source_entity_id = $2 OR r.target_entity_id = $2
              )
              AND (
                $3::text IS NULL OR
                ((se.entity_type = $3 OR te.entity_type = $3) AND
                 ($4::text IS NULL OR se.name = $4 OR te.name = $4))
              )
              AND ($5::text IS NULL OR r.relation_type = $5)
              AND ($6::text IS NULL OR r.status = $6)
              AND ($7::boolean = true OR r.known_by_reader = true)
            ORDER BY r.updated_at DESC
            LIMIT $8
            """,
            project_id,
            entity_id,
            entity_type,
            name,
            relation_type,
            status,
            include_reader_hidden,
            limit,
        )
        return rows_to_dicts(rows)

    async def recent_summaries(self, project_id: str, before_chapter_no: int, count: int) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT c.chapter_no, c.title, s.content, s.metadata
            FROM chapters c
            JOIN chapter_summaries s ON s.chapter_id = c.id AND s.summary_type = 'chapter'
            WHERE c.project_id = $1 AND c.chapter_no < $2
            ORDER BY c.chapter_no DESC
            LIMIT $3
            """,
            project_id,
            before_chapter_no,
            count,
        )
        return list(reversed(rows_to_dicts(rows)))

    async def rebuild_projection(
        self,
        project_id: str,
        from_chapter_no: int | None = None,
        batch_size: int = 100,
    ) -> dict[str, Any]:
        """Rebuild state projection in batches to avoid memory issues at scale."""
        if from_chapter_no is None:
            async with self._db.acquire() as conn:
                await conn.execute(
                    "UPDATE state_snapshots SET is_current = false WHERE project_id = $1",
                    project_id,
                )

        total_commits = 0
        total_entities = 0
        total_snapshots = 0
        last_chapter_no = from_chapter_no or 0

        while True:
            batch = await self._db.fetch(
                """
                SELECT cc.id AS commit_id, c.id AS chapter_id, c.chapter_no, cc.payload
                FROM chapter_commits cc
                JOIN chapters c ON c.id = cc.chapter_id
                WHERE cc.project_id = $1 AND cc.accepted = true
                  AND c.chapter_no > $2
                ORDER BY c.chapter_no, cc.commit_no
                LIMIT $3
                """,
                project_id,
                last_chapter_no,
                batch_size,
            )
            if not batch:
                break

            async with self._db.acquire() as conn:
                async with conn.transaction():
                    for commit in batch:
                        payload = commit["payload"] or {}
                        changes = []
                        changes.extend(payload.get("character_state_changes", []))
                        changes.extend(payload.get("world_state_changes", []))
                        for change in changes:
                            entity_type = change.get("entity_type") or change.get("type") or "character"
                            name = change.get("name") or change.get("entity") or change.get("character")
                            state = change.get("state") or change.get("changes") or change
                            if not name:
                                continue
                            entity = await conn.fetchrow(
                                """
                                INSERT INTO state_entities (project_id, entity_type, name, aliases, summary, description, tags,
                                                            importance, lifecycle_status, profile,
                                                            first_seen_chapter_no, last_seen_chapter_no)
                                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11, $12)
                                ON CONFLICT (project_id, entity_type, name)
                                DO UPDATE SET
                                    profile = state_entities.profile || EXCLUDED.profile,
                                    summary = COALESCE(EXCLUDED.summary, state_entities.summary),
                                    description = COALESCE(EXCLUDED.description, state_entities.description),
                                    tags = CASE WHEN $7 IS NULL THEN state_entities.tags ELSE EXCLUDED.tags END,
                                    importance = COALESCE(EXCLUDED.importance, state_entities.importance),
                                    last_seen_chapter_no = GREATEST(COALESCE(EXCLUDED.last_seen_chapter_no, 0), COALESCE(state_entities.last_seen_chapter_no, 0)),
                                    first_seen_chapter_no = LEAST(COALESCE(EXCLUDED.first_seen_chapter_no, 999999), COALESCE(state_entities.first_seen_chapter_no, 999999)),
                                    updated_at = now()
                                RETURNING id
                                """,
                                project_id,
                                entity_type,
                                name,
                                change.get("aliases", []),
                                change.get("summary"),
                                change.get("description"),
                                change.get("tags"),
                                change.get("importance", "medium"),
                                change.get("lifecycle_status", "active"),
                                json_dumps(change.get("profile", {})),
                                change.get("first_seen_chapter_no") or chapter_no,
                                change.get("last_seen_chapter_no") or chapter_no,
                            )
                            await conn.execute(
                                "UPDATE state_snapshots SET is_current = false WHERE project_id = $1 AND entity_id = $2",
                                project_id,
                                entity["id"],
                            )
                            await conn.execute(
                                """
                                INSERT INTO state_snapshots (
                                  project_id, entity_id, chapter_id, state, is_current, source_commit_id,
                                  effective_chapter_no, expire_chapter_no, effective_volume_no, expire_volume_no,
                                  duration_type, expires_on_event, confidence, source_type, source_id,
                                  change_reason, metadata
                                )
                                VALUES (
                                  $1, $2, $3, $4::jsonb, true, $5,
                                  $6, $7, $8, $9,
                                  $10, $11, $12, $13, $14,
                                  $15, $16::jsonb
                                )
                                """,
                                project_id,
                                entity["id"],
                                commit["chapter_id"],
                                json_dumps(state),
                                commit["commit_id"],
                                change.get("effective_chapter_no") or change.get("effective_chapter") or commit["chapter_no"],
                                change.get("expire_chapter_no") or change.get("expire_chapter"),
                                change.get("effective_volume_no") or change.get("effective_volume"),
                                change.get("expire_volume_no") or change.get("expire_volume"),
                                change.get("duration_type") or ("temporary" if (change.get("expire_chapter_no") or change.get("expire_chapter") or change.get("expires_on_event")) else "persistent"),
                                change.get("expires_on_event"),
                                change.get("confidence"),
                                change.get("source_type", "chapter_commit"),
                                change.get("source_id") or str(commit["commit_id"]),
                                change.get("change_reason") or change.get("reason"),
                                json_dumps(change.get("metadata", {})),
                            )
                            total_entities += 1
                            total_snapshots += 1

            last_chapter_no = batch[-1]["chapter_no"]
            total_commits += len(batch)

        return {
            "commits_processed": total_commits,
            "state_changes_processed": total_entities,
            "snapshots_created": total_snapshots,
            "batches": (total_commits + batch_size - 1) // batch_size,
        }

    async def pending_vector_chunks(self, project_id: str, limit: int) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, source_type, source_id::text, chunk_key, content, metadata
            FROM memory_chunks
            WHERE project_id = $1
              AND qdrant_point_id IS NULL
            ORDER BY created_at
            LIMIT $2
            """,
            project_id,
            limit,
        )
        return rows_to_dicts(rows)

    async def mark_vector_indexed(
        self,
        project_id: str,
        chunk_id: str,
        collection: str,
        point_id: str,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            UPDATE memory_chunks
            SET qdrant_collection = $3, qdrant_point_id = $4
            WHERE project_id = $1 AND id = $2
            RETURNING id::text, chunk_key, qdrant_collection, qdrant_point_id
            """,
            project_id,
            chunk_id,
            collection,
            point_id,
        )
        if row is None:
            raise ValueError(f"Memory chunk not found: {chunk_id}")
        return row_to_dict(row)
