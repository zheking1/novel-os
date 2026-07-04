from typing import Any
from json import dumps as json_dumps
from .db import Database
from .utils import row_to_dict, rows_to_dicts
from .utils import ensure_json_value


class KnowledgeService:
    """基础数据知识库服务 - 管理分类和知识条目"""

    def __init__(self, db: Database):
        self._db = db

    # ========================================
    # 分类管理
    # ========================================

    async def list_categories(
        self,
        include_inactive: bool = False,
    ) -> list[dict[str, Any]]:
        """列出所有分类"""
        where_clause = "WHERE is_active = true" if not include_inactive else ""
        rows = await self._db.fetch(
            f"""
            SELECT id::text, slug, name, name_en, description, icon, color,
                   sort_order, parent_id::text, level, is_system, is_active,
                   created_at, updated_at
            FROM categories
            {where_clause}
            ORDER BY sort_order, name
            """
        )
        return rows_to_dicts(rows)

    async def get_category(
        self,
        category_id: str | None = None,
        slug: str | None = None,
    ) -> dict[str, Any]:
        """获取单个分类"""
        if category_id:
            row = await self._db.fetchrow(
                """
                SELECT id::text, slug, name, name_en, description, icon, color,
                       sort_order, parent_id::text, level, is_system, is_active,
                       created_at, updated_at
                FROM categories
                WHERE id = $1
                """,
                category_id,
            )
        elif slug:
            row = await self._db.fetchrow(
                """
                SELECT id::text, slug, name, name_en, description, icon, color,
                       sort_order, parent_id::text, level, is_system, is_active,
                       created_at, updated_at
                FROM categories
                WHERE slug = $1
                """,
                slug,
            )
        else:
            raise ValueError("category_id or slug is required")

        return row_to_dict(row) if row else None

    async def upsert_category(
        self,
        slug: str,
        name: str,
        name_en: str | None = None,
        description: str | None = None,
        icon: str | None = None,
        color: str | None = None,
        sort_order: int | None = None,
        parent_id: str | None = None,
        is_system: bool = False,
    ) -> dict[str, Any]:
        """创建或更新分类"""
        row = await self._db.fetchrow(
            """
            INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (slug) DO UPDATE SET
                name = EXCLUDED.name,
                name_en = EXCLUDED.name_en,
                description = EXCLUDED.description,
                icon = EXCLUDED.icon,
                color = EXCLUDED.color,
                sort_order = EXCLUDED.sort_order,
                parent_id = EXCLUDED.parent_id,
                updated_at = now()
            RETURNING id::text, slug, name, name_en, description, icon, color,
                      sort_order, parent_id::text, level, is_system, is_active
            """,
            slug,
            name,
            name_en,
            description,
            icon,
            color,
            sort_order,
            parent_id,
            is_system,
        )
        return row_to_dict(row)

    async def delete_category(
        self,
        category_id: str | None = None,
        slug: str | None = None,
    ) -> bool:
        """删除分类（软删除）"""
        if category_id:
            result = await self._db.execute(
                "UPDATE categories SET is_active = false WHERE id = $1",
                category_id,
            )
        elif slug:
            result = await self._db.execute(
                "UPDATE categories SET is_active = false WHERE slug = $1",
                slug,
            )
        else:
            raise ValueError("category_id or slug is required")
        return result == "UPDATE 1"

    async def get_category_stats(self) -> list[dict[str, Any]]:
        """获取分类统计（每个分类的知识条目数）"""
        rows = await self._db.fetch(
            """
            SELECT c.id::text, c.slug, c.name, c.icon, c.color,
                   COUNT(k.id) as item_count
            FROM categories c
            LEFT JOIN knowledge_base k ON k.category_id = c.id AND k.status = 'active'
            WHERE c.is_active = true
            GROUP BY c.id, c.slug, c.name, c.icon, c.color
            ORDER BY c.sort_order, c.name
            """
        )
        return rows_to_dicts(rows)

    # ========================================
    # 知识条目管理
    # ========================================

    async def list_items(
        self,
        category_slug: str | None = None,
        source: str | None = None,
        level: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """列出知识条目"""
        conditions = []
        params: list[Any] = []
        param_idx = 0

        if category_slug:
            param_idx += 1
            conditions.append(f"(c.slug = ${param_idx} OR c.parent_id IN (SELECT id FROM ref_categories WHERE slug = ${param_idx}))")
            params.append(category_slug)

        if source:
            param_idx += 1
            conditions.append(f"k.source = ${param_idx}")
            params.append(source)

        if level:
            param_idx += 1
            conditions.append(f"k.level = ${param_idx}")
            params.append(level)

        if status:
            param_idx += 1
            conditions.append(f"k.status = ${param_idx}")
            params.append(status)
        else:
            param_idx += 1
            conditions.append(f"k.status = ${param_idx}")
            params.append('active')

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        param_idx += 1
        params.append(limit)
        param_idx += 1
        params.append(offset)

        rows = await self._db.fetch(
            f"""
            SELECT k.id::text, k.code, k.title, k.summary, k.source, k.level, k.status,
                   k.view_count, k.use_count, k.created_at, k.updated_at,
                   c.slug as category_slug, c.name as category_name
            FROM knowledge_base k
            LEFT JOIN categories c ON c.id = k.category_id
            {where_sql}
            ORDER BY k.created_at DESC
            LIMIT ${param_idx - 1} OFFSET ${param_idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def get_item(
        self,
        item_id: str | None = None,
        code: str | None = None,
    ) -> dict[str, Any]:
        """获取单个知识条目"""
        if item_id:
            row = await self._db.fetchrow(
                """
                SELECT k.id::text, k.code, k.title, k.content, k.summary, k.detail,
                       k.examples, k.counter_examples, k.metadata, k.source,
                       k.source_file, k.applicable_genres, k.applicable_skills,
                       k.level, k.status, k.view_count, k.use_count,
                       k.created_at, k.updated_at,
                       c.id::text as category_id, c.slug as category_slug, c.name as category_name
                FROM knowledge_base k
                LEFT JOIN categories c ON c.id = k.category_id
                WHERE k.id = $1
                """,
                item_id,
            )
        elif code:
            row = await self._db.fetchrow(
                """
                SELECT k.id::text, k.code, k.title, k.content, k.summary, k.detail,
                       k.examples, k.counter_examples, k.metadata, k.source,
                       k.source_file, k.applicable_genres, k.applicable_skills,
                       k.level, k.status, k.view_count, k.use_count,
                       k.created_at, k.updated_at,
                       c.id::text as category_id, c.slug as category_slug, c.name as category_name
                FROM knowledge_base k
                LEFT JOIN categories c ON c.id = k.category_id
                WHERE k.code = $1
                """,
                code,
            )
        else:
            raise ValueError("item_id or code is required")

        result = row_to_dict(row) if row else None
        if result and result.get("metadata"):
            result["metadata"] = ensure_json_value(result["metadata"])
        return result

    async def search_items(
        self,
        query: str,
        category_slug: str | None = None,
        applicable_genre: str | None = None,
        applicable_skill: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """搜索知识条目"""
        conditions = []
        params: list[Any] = []
        param_idx = 1

        # 全文搜索条件
        search_pattern = f"%{query}%"
        param_idx += 1
        params.append(search_pattern)
        param_idx += 1
        params.append(search_pattern)
        param_idx += 1
        params.append(search_pattern)
        conditions.append(
            f"(k.title ILIKE ${param_idx - 3} OR k.content ILIKE ${param_idx - 2} OR k.summary ILIKE ${param_idx - 1})"
        )

        if category_slug:
            param_idx += 1
            params.append(category_slug)
            conditions.append(f"c.slug = ${param_idx}")

        if applicable_genre:
            param_idx += 1
            params.append(applicable_genre)
            conditions.append(f"$${param_idx} = ANY(k.applicable_genres)")

        if applicable_skill:
            param_idx += 1
            params.append(applicable_skill)
            conditions.append(f"$${param_idx} = ANY(k.applicable_skills)")

        param_idx += 1
        params.append(limit)

        rows = await self._db.fetch(
            f"""
            SELECT k.id::text, k.code, k.title, k.summary, k.content,
                   k.applicable_genres, k.applicable_skills, k.level,
                   c.slug as category_slug, c.name as category_name
            FROM knowledge_base k
            LEFT JOIN categories c ON c.id = k.category_id
            WHERE k.status = 'active' AND {' AND '.join(conditions)}
            ORDER BY k.use_count DESC, k.view_count DESC
            LIMIT ${param_idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def upsert_item(
        self,
        code: str,
        title: str,
        content: str,
        summary: str | None = None,
        detail: str | None = None,
        examples: str | None = None,
        counter_examples: str | None = None,
        metadata: dict[str, Any] | None = None,
        category_slug: str | None = None,
        source: str = "manual",
        source_file: str | None = None,
        applicable_genres: list[str] | None = None,
        applicable_skills: list[str] | None = None,
        level: str = "knowledge",
        status: str = "active",
    ) -> dict[str, Any]:
        """创建或更新知识条目"""
        # 获取分类ID
        category_id = None
        if category_slug:
            cat_row = await self._db.fetchrow(
                "SELECT id FROM categories WHERE slug = $1",
                category_slug,
            )
            category_id = cat_row["id"] if cat_row else None

        row = await self._db.fetchrow(
            """
            INSERT INTO knowledge_base (code, title, content, summary, detail, examples, counter_examples,
                                        metadata, category_id, source, source_file,
                                        applicable_genres, applicable_skills, level, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $10, $11, $12, $13, $14, $15)
            ON CONFLICT (code) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                summary = EXCLUDED.summary,
                detail = EXCLUDED.detail,
                examples = EXCLUDED.examples,
                counter_examples = EXCLUDED.counter_examples,
                metadata = EXCLUDED.metadata,
                category_id = EXCLUDED.category_id,
                source = EXCLUDED.source,
                applicable_genres = EXCLUDED.applicable_genres,
                applicable_skills = EXCLUDED.applicable_skills,
                level = EXCLUDED.level,
                status = EXCLUDED.status,
                updated_at = now()
            RETURNING id::text, code, title, content, summary, detail, examples, counter_examples,
                      metadata, category_id::text, source, source_file, applicable_genres,
                      applicable_skills, level, status, created_at, updated_at
            """,
            code,
            title,
            content,
            summary,
            detail,
            examples,
            counter_examples,
            json_dumps(metadata or {}),
            category_id,
            source,
            source_file,
            applicable_genres or [],
            applicable_skills or [],
            level,
            status,
        )
        return row_to_dict(row)

    async def delete_item(
        self,
        item_id: str | None = None,
        code: str | None = None,
    ) -> bool:
        """删除知识条目（软删除）"""
        if item_id:
            result = await self._db.execute(
                "UPDATE knowledge_base SET status = 'deleted' WHERE id = $1",
                item_id,
            )
        elif code:
            result = await self._db.execute(
                "UPDATE knowledge_base SET status = 'deleted' WHERE code = $1",
                code,
            )
        else:
            raise ValueError("item_id or code is required")
        return result == "UPDATE 1"

    async def increment_view_count(self, item_id: str) -> None:
        """增加查看次数"""
        await self._db.execute(
            "UPDATE knowledge_base SET view_count = view_count + 1 WHERE id = $1",
            item_id,
        )

    async def increment_use_count(self, item_id: str) -> None:
        """增加使用次数"""
        await self._db.execute(
            "UPDATE knowledge_base SET use_count = use_count + 1 WHERE id = $1",
            item_id,
        )

    # ========================================
    # 统计与批量操作
    # ========================================

    async def get_stats(self) -> dict[str, Any]:
        """获取知识库统计"""
        row = await self._db.fetchrow(
            """
            SELECT
                COUNT(*) as total_items,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_items,
                COUNT(CASE WHEN source = 'opencode' THEN 1 END) as opencode_items,
                COUNT(CASE WHEN source = 'manual' THEN 1 END) as manual_items,
                SUM(view_count) as total_views,
                SUM(use_count) as total_uses
            FROM knowledge_base
            """
        )
        stats = row_to_dict(row)

        # 获取分类统计
        category_stats = await self.get_category_stats()
        stats["categories"] = category_stats

        return stats

    async def bulk_import(
        self,
        items: list[dict[str, Any]],
        source: str = "bulk_import",
    ) -> dict[str, Any]:
        """批量导入知识条目"""
        imported = 0
        skipped = 0
        errors = []

        for item in items:
            try:
                await self.upsert_item(
                    code=item.get("code"),
                    title=item.get("title"),
                    content=item.get("content"),
                    summary=item.get("summary"),
                    detail=item.get("detail"),
                    examples=item.get("examples"),
                    counter_examples=item.get("counter_examples"),
                    metadata=item.get("metadata"),
                    category_slug=item.get("category_slug"),
                    source=source,
                    source_file=item.get("source_file"),
                    applicable_genres=item.get("applicable_genres"),
                    applicable_skills=item.get("applicable_skills"),
                    level=item.get("level", "knowledge"),
                    status=item.get("status", "active"),
                )
                imported += 1
            except Exception as e:
                skipped += 1
                errors.append(str(e))

        return {
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
        }

    # ========================================
    # 用户私有知识库管理
    # ========================================

    async def get_user_items(
        self,
        user_id: str,
        category_slug: str | None = None,
        status: str | None = None,
        review_status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """获取用户私有知识条目"""
        conditions = []
        params: list[Any] = []
        param_idx = 0

        param_idx += 1
        conditions.append(f"uk.user_id = ${param_idx}")
        params.append(user_id)

        if category_slug:
            param_idx += 1
            conditions.append(f"c.slug = ${param_idx}")
            params.append(category_slug)

        if status:
            param_idx += 1
            conditions.append(f"uk.status = ${param_idx}")
            params.append(status)

        if review_status:
            param_idx += 1
            conditions.append(f"uk.review_status = ${param_idx}")
            params.append(review_status)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        param_idx += 1
        params.append(limit)
        param_idx += 1
        params.append(offset)

        rows = await self._db.fetch(
            f"""
            SELECT uk.id::text, uk.code, uk.title, uk.summary, uk.status,
                   uk.review_status, uk.review_comment, uk.created_at, uk.updated_at,
                   uk.base_knowledge_id::text, c.slug as category_slug, c.name as category_name,
                   bk.title as base_title
            FROM user_knowledge uk
            LEFT JOIN categories c ON c.id = uk.category_id
            LEFT JOIN knowledge_base bk ON bk.id = uk.base_knowledge_id
            {where_sql}
            ORDER BY uk.updated_at DESC
            LIMIT ${param_idx - 1} OFFSET ${param_idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def get_user_item(
        self,
        user_id: str,
        item_id: str,
    ) -> dict[str, Any]:
        """获取单个用户私有知识条目"""
        row = await self._db.fetchrow(
            """
            SELECT uk.id::text, uk.code, uk.title, uk.content, uk.summary, uk.detail,
                   uk.examples, uk.counter_examples, uk.metadata, uk.status,
                   uk.review_status, uk.review_comment, uk.applicable_genres,
                   uk.applicable_skills, uk.level, uk.created_at, uk.updated_at,
                   uk.base_knowledge_id::text, c.id::text as category_id,
                   c.slug as category_slug, c.name as category_name,
                   bk.title as base_title, bk.content as base_content
            FROM user_knowledge uk
            LEFT JOIN categories c ON c.id = uk.category_id
            LEFT JOIN knowledge_base bk ON bk.id = uk.base_knowledge_id
            WHERE uk.id = $1 AND uk.user_id = $2
            """,
            item_id,
            user_id,
        )

        result = row_to_dict(row) if row else None
        if result and result.get("metadata"):
            result["metadata"] = ensure_json_value(result["metadata"])
        return result

    async def upsert_user_item(
        self,
        user_id: str,
        title: str,
        content: str,
        item_id: str | None = None,
        code: str | None = None,
        summary: str | None = None,
        detail: str | None = None,
        examples: str | None = None,
        counter_examples: str | None = None,
        metadata: dict[str, Any] | None = None,
        category_slug: str | None = None,
        base_knowledge_id: str | None = None,
        applicable_genres: list[str] | None = None,
        applicable_skills: list[str] | None = None,
        level: str = "knowledge",
        status: str = "active",
    ) -> dict[str, Any]:
        """创建或更新用户私有知识条目"""
        category_id = None
        if category_slug:
            cat_row = await self._db.fetchrow(
                "SELECT id FROM categories WHERE slug = $1",
                category_slug,
            )
            category_id = cat_row["id"] if cat_row else None

        if item_id:
            row = await self._db.fetchrow(
                """
                UPDATE user_knowledge
                SET title = $1, content = $2, summary = $3, detail = $4,
                    examples = $5, counter_examples = $6, metadata = $7::jsonb,
                    category_id = $8, code = $9,
                    applicable_genres = $10, applicable_skills = $11,
                    level = $12, status = $13, updated_at = now()
                WHERE id = $14 AND user_id = $15
                RETURNING id::text, code, title, status, review_status, updated_at
                """,
                title,
                content,
                summary,
                detail,
                examples,
                counter_examples,
                json_dumps(metadata or {}),
                category_id,
                code,
                applicable_genres or [],
                applicable_skills or [],
                level,
                status,
                item_id,
                user_id,
            )
        else:
            row = await self._db.fetchrow(
                """
                INSERT INTO user_knowledge (user_id, base_knowledge_id, code, title, content,
                    summary, detail, examples, counter_examples, metadata, category_id,
                    applicable_genres, applicable_skills, level, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11, $12, $13, $14, $15)
                RETURNING id::text, code, title, status, review_status, created_at
                """,
                user_id,
                base_knowledge_id,
                code,
                title,
                content,
                summary,
                detail,
                examples,
                counter_examples,
                json_dumps(metadata or {}),
                category_id,
                applicable_genres or [],
                applicable_skills or [],
                level,
                status,
            )

        return row_to_dict(row)

    async def delete_user_item(
        self,
        user_id: str,
        item_id: str,
    ) -> bool:
        """删除用户私有知识条目"""
        result = await self._db.execute(
            "DELETE FROM user_knowledge WHERE id = $1 AND user_id = $2",
            item_id,
            user_id,
        )
        return result == "DELETE 1"

    async def create_from_base(
        self,
        user_id: str,
        base_knowledge_id: str,
    ) -> dict[str, Any]:
        """从公共知识条目创建用户私有副本"""
        base_row = await self._db.fetchrow(
            """
            SELECT k.id, k.code, k.title, k.content, k.summary, k.detail,
                   k.examples, k.counter_examples, k.metadata, k.category_id,
                   k.applicable_genres, k.applicable_skills, k.level
            FROM knowledge_base k
            WHERE k.id = $1 AND k.status = 'active'
            """,
            base_knowledge_id,
        )

        if not base_row:
            raise ValueError("Base knowledge item not found")

        row = await self._db.fetchrow(
            """
            INSERT INTO user_knowledge (
                user_id, base_knowledge_id, code, title, content, summary, detail,
                examples, counter_examples, metadata, category_id,
                applicable_genres, applicable_skills, level, status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, 'active')
            RETURNING id::text, code, title, status, created_at
            """,
            user_id,
            base_row["id"],
            base_row["code"],
            base_row["title"],
            base_row["content"],
            base_row["summary"],
            base_row["detail"],
            base_row["examples"],
            base_row["counter_examples"],
            base_row["metadata"],
            base_row["category_id"],
            base_row["applicable_genres"],
            base_row["applicable_skills"],
            base_row["level"],
        )

        return row_to_dict(row)

    # ========================================
    # 审核流程管理
    # ========================================

    async def submit_for_review(
        self,
        user_id: str,
        item_id: str,
        reason: str,
    ) -> dict[str, Any]:
        """提交用户知识条目进行审核"""
        async with self._db.transaction():
            row = await self._db.fetchrow(
                """
                UPDATE user_knowledge
                SET status = 'submitted', review_status = 'pending'
                WHERE id = $1 AND user_id = $2 AND status IN ('active', 'draft')
                RETURNING id::text, title, base_knowledge_id::text
                """,
                item_id,
                user_id,
            )

            if not row:
                raise ValueError("Cannot submit item for review")

            review_row = await self._db.fetchrow(
                """
                INSERT INTO knowledge_review (user_knowledge_id, submitter_id, submit_reason)
                VALUES ($1, $2, $3)
                RETURNING id::text, submit_time
                """,
                item_id,
                user_id,
                reason,
            )

            return {
                **row_to_dict(row),
                **row_to_dict(review_row),
            }

    async def list_review_items(
        self,
        review_status: str | None = None,
        submitter_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """列出待审核的知识条目"""
        conditions = []
        params: list[Any] = []
        param_idx = 0

        if review_status:
            param_idx += 1
            conditions.append(f"kr.review_status = ${param_idx}")
            params.append(review_status)

        if submitter_id:
            param_idx += 1
            conditions.append(f"kr.submitter_id = ${param_idx}")
            params.append(submitter_id)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        param_idx += 1
        params.append(limit)
        param_idx += 1
        params.append(offset)

        rows = await self._db.fetch(
            f"""
            SELECT kr.id::text as review_id, kr.review_status, kr.submit_time,
                   kr.submit_reason, kr.reviewer_id::text, kr.review_time,
                   kr.review_comment, kr.version,
                   uk.id::text as user_knowledge_id, uk.title, uk.code, uk.status,
                   uk.review_comment as item_comment, uk.updated_at,
                   uk.base_knowledge_id::text,
                   u.username as submitter_name,
                   c.slug as category_slug, c.name as category_name,
                   bk.title as base_title
            FROM knowledge_review kr
            JOIN user_knowledge uk ON uk.id = kr.user_knowledge_id
            JOIN users u ON u.id = kr.submitter_id
            LEFT JOIN categories c ON c.id = uk.category_id
            LEFT JOIN knowledge_base bk ON bk.id = uk.base_knowledge_id
            {where_sql}
            ORDER BY kr.submit_time DESC
            LIMIT ${param_idx - 1} OFFSET ${param_idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def get_review_detail(
        self,
        review_id: str,
    ) -> dict[str, Any]:
        """获取审核详情"""
        row = await self._db.fetchrow(
            """
            SELECT kr.id::text as review_id, kr.review_status, kr.submit_time,
                   kr.submit_reason, kr.reviewer_id::text, kr.review_time,
                   kr.review_comment, kr.version, kr.merged_base_id::text,
                   uk.id::text as user_knowledge_id, uk.title, uk.code, uk.content,
                   uk.summary, uk.detail, uk.examples, uk.counter_examples,
                   uk.metadata, uk.applicable_genres, uk.applicable_skills,
                   uk.level, uk.status, uk.created_at, uk.updated_at,
                   uk.base_knowledge_id::text,
                   u.username as submitter_name,
                   c.slug as category_slug, c.name as category_name,
                   bk.title as base_title, bk.content as base_content,
                   r.username as reviewer_name
            FROM knowledge_review kr
            JOIN user_knowledge uk ON uk.id = kr.user_knowledge_id
            JOIN users u ON u.id = kr.submitter_id
            LEFT JOIN categories c ON c.id = uk.category_id
            LEFT JOIN knowledge_base bk ON bk.id = uk.base_knowledge_id
            LEFT JOIN users r ON r.id = kr.reviewer_id
            WHERE kr.id = $1
            """,
            review_id,
        )

        result = row_to_dict(row) if row else None
        if result and result.get("metadata"):
            result["metadata"] = ensure_json_value(result["metadata"])
        return result

    async def approve_review(
        self,
        reviewer_id: str,
        review_id: str,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """审核通过：将用户条目合并到公共知识库"""
        async with self._db.transaction():
            review_row = await self._db.fetchrow(
                """
                SELECT kr.user_knowledge_id, uk.base_knowledge_id, uk.code,
                       uk.title, uk.content, uk.summary, uk.detail,
                       uk.examples, uk.counter_examples, uk.metadata,
                       uk.category_id, uk.applicable_genres, uk.applicable_skills, uk.level
                FROM knowledge_review kr
                JOIN user_knowledge uk ON uk.id = kr.user_knowledge_id
                WHERE kr.id = $1 AND kr.review_status = 'pending'
                """,
                review_id,
            )

            if not review_row:
                raise ValueError("Review item not found or already processed")

            base_id = review_row["base_knowledge_id"]

            if base_id:
                await self._db.execute(
                    """
                    UPDATE knowledge_base
                    SET title = $1, content = $2, summary = $3, detail = $4,
                        examples = $5, counter_examples = $6, metadata = $7,
                        applicable_genres = $8, applicable_skills = $9,
                        level = $10, last_reviewed_at = now(),
                        reviewed_by = $11, review_version = review_version + 1
                    WHERE id = $12
                    """,
                    review_row["title"],
                    review_row["content"],
                    review_row["summary"],
                    review_row["detail"],
                    review_row["examples"],
                    review_row["counter_examples"],
                    review_row["metadata"],
                    review_row["applicable_genres"],
                    review_row["applicable_skills"],
                    review_row["level"],
                    reviewer_id,
                    base_id,
                )
                merged_id = base_id
            else:
                new_row = await self._db.fetchrow(
                    """
                    INSERT INTO knowledge_base (code, title, content, summary, detail,
                        examples, counter_examples, metadata, category_id,
                        applicable_genres, applicable_skills, level, status,
                        last_reviewed_at, reviewed_by, review_version, source)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                            'active', now(), $13, 1, 'user_reviewed')
                    RETURNING id
                    """,
                    review_row["code"] or None,
                    review_row["title"],
                    review_row["content"],
                    review_row["summary"],
                    review_row["detail"],
                    review_row["examples"],
                    review_row["counter_examples"],
                    review_row["metadata"],
                    review_row["category_id"],
                    review_row["applicable_genres"],
                    review_row["applicable_skills"],
                    review_row["level"],
                    reviewer_id,
                )
                merged_id = new_row["id"]

            await self._db.execute(
                """
                UPDATE user_knowledge
                SET status = 'active', review_status = 'approved', review_comment = $1
                WHERE id = $2
                """,
                comment,
                review_row["user_knowledge_id"],
            )

            result = await self._db.fetchrow(
                """
                UPDATE knowledge_review
                SET review_status = 'approved', reviewer_id = $1,
                    review_time = now(), review_comment = $2, merged_base_id = $3
                WHERE id = $4
                RETURNING id::text, review_status, merged_base_id::text
                """,
                reviewer_id,
                comment,
                merged_id,
                review_id,
            )

            return row_to_dict(result)

    async def reject_review(
        self,
        reviewer_id: str,
        review_id: str,
        comment: str,
    ) -> dict[str, Any]:
        """审核拒绝"""
        async with self._db.transaction():
            await self._db.execute(
                """
                UPDATE user_knowledge
                SET status = 'active', review_status = 'rejected', review_comment = $1
                WHERE id = (SELECT user_knowledge_id FROM knowledge_review WHERE id = $2)
                """,
                comment,
                review_id,
            )

            result = await self._db.fetchrow(
                """
                UPDATE knowledge_review
                SET review_status = 'rejected', reviewer_id = $1,
                    review_time = now(), review_comment = $2
                WHERE id = $3
                RETURNING id::text, review_status
                """,
                reviewer_id,
                comment,
                review_id,
            )

            return row_to_dict(result)

    async def get_review_stats(self) -> dict[str, Any]:
        """获取审核统计"""
        row = await self._db.fetchrow(
            """
            SELECT
                COUNT(*) as total_reviews,
                COUNT(CASE WHEN review_status = 'pending' THEN 1 END) as pending_count,
                COUNT(CASE WHEN review_status = 'approved' THEN 1 END) as approved_count,
                COUNT(CASE WHEN review_status = 'rejected' THEN 1 END) as rejected_count
            FROM knowledge_review
            """
        )
        return row_to_dict(row)

    async def get_user_stats(self, user_id: str) -> dict[str, Any]:
        """获取用户知识统计"""
        row = await self._db.fetchrow(
            """
            SELECT
                COUNT(*) as total_items,
                COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
                COUNT(CASE WHEN status = 'submitted' THEN 1 END) as submitted_count,
                COUNT(CASE WHEN review_status = 'approved' THEN 1 END) as approved_count,
                COUNT(CASE WHEN review_status = 'rejected' THEN 1 END) as rejected_count
            FROM user_knowledge
            WHERE user_id = $1
            """,
            user_id,
        )
        return row_to_dict(row)