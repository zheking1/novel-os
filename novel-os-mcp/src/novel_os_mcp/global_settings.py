"""
Global Settings Service - 全局设定服务

包含：
- 分类管理（setting_categories）
- 设定项目管理（setting_items）
- BM25 检索
- 题材规范化
- CSV 导入导出
"""

import csv
import io
import json
from typing import Any

from .db import Database
from .utils import row_to_dict, rows_to_dicts


class GlobalSettingsService:
    """全局设定服务"""

    def __init__(self, db: Database):
        self._db = db

    # ========== 分类管理 ==========

    async def list_categories(
        self,
        workspace_id: str,
        is_active: bool | None = True,
    ) -> list[dict[str, Any]]:
        """列出设定分类"""
        rows = await self._db.fetch(
            """
            SELECT 
                id::text, 
                name, 
                slug, 
                description,
                icon,
                sort_order,
                is_active,
                is_standard,
                created_at,
                updated_at
            FROM setting_categories
            WHERE workspace_id = $1
                AND ($2::boolean IS NULL OR is_active = $2)
            ORDER BY sort_order, name
            """,
            workspace_id,
            is_active,
        )
        return rows_to_dicts(rows)

    async def get_category(
        self,
        workspace_id: str,
        category_id: str | None = None,
        slug: str | None = None,
    ) -> dict[str, Any] | None:
        """获取分类详情（含字段定义）"""
        if not category_id and not slug:
            raise ValueError("category_id or slug is required")

        if category_id:
            row = await self._db.fetchrow(
                """
                SELECT id::text, name, slug, description, icon, sort_order, 
                       is_active, is_standard, metadata, created_at, updated_at
                FROM setting_categories
                WHERE id = $1 AND workspace_id = $2
                """,
                category_id,
                workspace_id,
            )
        else:
            row = await self._db.fetchrow(
                """
                SELECT id::text, name, slug, description, icon, sort_order, 
                       is_active, is_standard, metadata, created_at, updated_at
                FROM setting_categories
                WHERE slug = $1 AND workspace_id = $2
                """,
                slug,
                workspace_id,
            )

        if not row:
            return None

        result = row_to_dict(row)

        # 加载字段定义
        fields = await self._db.fetch(
            """
            SELECT 
                id::text,
                field_name,
                field_key,
                field_type,
                options,
                is_required,
                is_searchable,
                default_value,
                placeholder,
                help_text,
                sort_order
            FROM setting_field_definitions
            WHERE category_id = $1
            ORDER BY sort_order
            """,
            row["id"],
        )
        result["field_definitions"] = rows_to_dicts(fields)

        return result

    async def upsert_category(
        self,
        workspace_id: str,
        slug: str,
        name: str,
        username: str,
        description: str | None = None,
        icon: str = "📁",
        sort_order: int = 0,
        is_standard: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """创建或更新分类"""
        row = await self._db.fetchrow(
            """
            INSERT INTO setting_categories (
                workspace_id, slug, name, description, icon, sort_order, is_standard, metadata,
                created_by, updated_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb, $9, $9)
            ON CONFLICT (workspace_id, slug) 
            DO UPDATE SET 
                name = EXCLUDED.name,
                description = COALESCE(EXCLUDED.description, setting_categories.description),
                icon = EXCLUDED.icon,
                sort_order = EXCLUDED.sort_order,
                metadata = EXCLUDED.metadata,
                updated_by = EXCLUDED.updated_by,
                updated_at = now()
            RETURNING id::text, name, slug, description, icon, sort_order, is_active, is_standard, created_at, updated_at
            """,
            workspace_id,
            slug,
            name,
            description,
            icon,
            sort_order,
            is_standard,
            json.dumps(metadata or {}),
            username,
        )
        return row_to_dict(row)

    async def delete_category(
        self,
        workspace_id: str,
        category_id: str,
    ) -> dict[str, Any]:
        """删除分类（标准分类不可删除）"""
        # 检查是否是标准分类
        row = await self._db.fetchrow(
            "SELECT is_standard FROM setting_categories WHERE id = $1 AND workspace_id = $2",
            category_id,
            workspace_id,
        )

        if not row:
            raise ValueError(f"Category not found: {category_id}")

        if row["is_standard"]:
            # 标准分类改为隐藏，不删除
            await self._db.execute(
                """
                UPDATE setting_categories SET is_active = FALSE, updated_at = now()
                WHERE id = $1
                """,
                category_id,
            )
            return {"id": category_id, "deleted": False, "reason": "standard_category_hidden"}

        # 删除分类（字段定义会级联删除）
        await self._db.execute(
            "DELETE FROM setting_categories WHERE id = $1 AND workspace_id = $2",
            category_id,
            workspace_id,
        )

        return {"id": category_id, "deleted": True}

    # ========== 设定项目管理 ==========

    async def list_items(
        self,
        workspace_id: str,
        category_id: str | None = None,
        is_global: bool | None = None,
        level: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """列出设定项目"""
        conditions = ["(workspace_id = $1 OR is_global = TRUE)"]
        params: list[Any] = [workspace_id]
        param_idx = 2

        if category_id:
            conditions.append(f"category_id = ${param_idx}")
            params.append(category_id)
            param_idx += 1

        if is_global is not None:
            conditions.append(f"is_global = ${param_idx}")
            params.append(is_global)
            param_idx += 1

        if level:
            conditions.append(f"level = ${param_idx}")
            params.append(level)
            param_idx += 1

        where_clause = " AND ".join(conditions)

        rows = await self._db.fetch(
            f"""
            SELECT 
                id::text,
                category_id::text,
                item_code,
                core_summary,
                detailed_expansion,
                ai_instruction,
                level,
                is_global,
                keywords,
                intent_synonyms,
                poison_points,
                applicable_skills,
                applicable_genres,
                tags,
                sort_order,
                created_at,
                updated_at
            FROM setting_items
            WHERE {where_clause}
            ORDER BY sort_order, created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """,
            *params,
            limit,
            offset,
        )
        return rows_to_dicts(rows)

    async def get_item(
        self,
        workspace_id: str,
        item_id: str | None = None,
        item_code: str | None = None,
    ) -> dict[str, Any] | None:
        """获取设定项目详情"""
        if not item_id and not item_code:
            raise ValueError("item_id or item_code is required")

        if item_id:
            row = await self._db.fetchrow(
                """
                SELECT 
                    id::text,
                    category_id::text,
                    workspace_id::text,
                    item_code,
                    keywords,
                    intent_synonyms,
                    core_summary,
                    detailed_expansion,
                    ai_instruction,
                    poison_points,
                    level,
                    applicable_skills,
                    applicable_genres,
                    data,
                    tags,
                    is_global,
                    sort_order,
                    metadata,
                    created_at,
                    updated_at
                FROM setting_items
                WHERE id = $1 AND (workspace_id = $2 OR is_global = TRUE)
                """,
                item_id,
                workspace_id,
            )
        else:
            row = await self._db.fetchrow(
                """
                SELECT 
                    id::text,
                    category_id::text,
                    workspace_id::text,
                    item_code,
                    keywords,
                    intent_synonyms,
                    core_summary,
                    detailed_expansion,
                    ai_instruction,
                    poison_points,
                    level,
                    applicable_skills,
                    applicable_genres,
                    data,
                    tags,
                    is_global,
                    sort_order,
                    metadata,
                    created_at,
                    updated_at
                FROM setting_items
                WHERE workspace_id = $1 AND item_code = $2
                """,
                workspace_id,
                item_code,
            )

        result = row_to_dict(row)
        if result and result.get("data"):
            result["data"] = json.loads(result["data"]) if isinstance(result["data"], str) else result["data"]
        if result and result.get("metadata"):
            result["metadata"] = json.loads(result["metadata"]) if isinstance(result["metadata"], str) else result["metadata"]
        return result

    async def upsert_item(
        self,
        workspace_id: str,
        category_id: str,
        username: str,
        core_summary: str,
        item_code: str | None = None,
        keywords: list[str] | None = None,
        intent_synonyms: list[str] | None = None,
        detailed_expansion: str | None = None,
        ai_instruction: str | None = None,
        poison_points: list[str] | None = None,
        level: str = "knowledge",
        applicable_skills: list[str] | None = None,
        applicable_genres: list[str] | None = None,
        data: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        is_global: bool = True,
        sort_order: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """创建或更新设定项目"""
        # 生成 item_code 如果未提供
        if not item_code:
            count = await self._db.fetchval(
                "SELECT COUNT(*) FROM setting_items WHERE category_id = $1",
                category_id,
            )
            item_code = f"GS-{int(count) + 1:04d}"

        row = await self._db.fetchrow(
            """
            INSERT INTO setting_items (
                category_id, workspace_id, item_code,
                keywords, intent_synonyms, core_summary, detailed_expansion,
                ai_instruction, poison_points,
                level, applicable_skills, applicable_genres,
                data, tags, is_global, sort_order, metadata,
                created_by, updated_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::jsonb, $14, $15, $16, $17::jsonb, $18, $18)
            ON CONFLICT (workspace_id, item_code) 
            DO UPDATE SET 
                category_id = EXCLUDED.category_id,
                keywords = EXCLUDED.keywords,
                intent_synonyms = EXCLUDED.intent_synonyms,
                core_summary = EXCLUDED.core_summary,
                detailed_expansion = EXCLUDED.detailed_expansion,
                ai_instruction = EXCLUDED.ai_instruction,
                poison_points = EXCLUDED.poison_points,
                level = EXCLUDED.level,
                applicable_skills = EXCLUDED.applicable_skills,
                applicable_genres = EXCLUDED.applicable_genres,
                data = EXCLUDED.data,
                tags = EXCLUDED.tags,
                is_global = EXCLUDED.is_global,
                sort_order = EXCLUDED.sort_order,
                metadata = EXCLUDED.metadata,
                updated_by = EXCLUDED.updated_by,
                updated_at = now()
            RETURNING id::text, item_code, category_id::text, core_summary, level, is_global, created_at, updated_at
            """,
            category_id,
            workspace_id,
            item_code,
            keywords or [],
            intent_synonyms or [],
            core_summary,
            detailed_expansion,
            ai_instruction,
            poison_points or [],
            level,
            applicable_skills or [],
            applicable_genres or [],
            json.dumps(data or {}),
            tags or [],
            is_global,
            sort_order,
            json.dumps(metadata or {}),
            username,
        )
        return row_to_dict(row)

    async def delete_item(
        self,
        workspace_id: str,
        item_id: str,
    ) -> dict[str, Any]:
        """删除设定项目"""
        row = await self._db.fetchrow(
            """
            DELETE FROM setting_items
            WHERE id = $1 AND workspace_id = $2 AND is_global = FALSE
            RETURNING id::text
            """,
            item_id,
            workspace_id,
        )

        if not row:
            raise ValueError(f"Setting item not found or cannot be deleted: {item_id}")

        return {"id": row["id"], "deleted": True}

    # ========== BM25 检索 ==========

    async def bm25_search(
        self,
        workspace_id: str,
        query: str,
        category_id: str | None = None,
        level: str | None = None,
        skill: str | None = None,
        genre: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """BM25 智能检索"""
        # 调用数据库函数
        rows = await self._db.fetch(
            """
            SELECT * FROM fn_setting_items_bm25_search(
                $1, $2, $3, $4, $5, $6, $7, $8
            )
            """,
            query,
            workspace_id,
            category_id,
            level,
            skill,
            genre,
            limit,
            offset,
        )
        results = rows_to_dicts(rows)
        # 处理 JSON 字段
        for r in results:
            if r.get("applicable_skills"):
                r["applicable_skills"] = list(r["applicable_skills"]) if hasattr(r["applicable_skills"], "__iter__") else []
            if r.get("applicable_genres"):
                r["applicable_genres"] = list(r["applicable_genres"]) if hasattr(r["applicable_genres"], "__iter__") else []
            if r.get("tags"):
                r["tags"] = list(r["tags"]) if hasattr(r["tags"], "__iter__") else []
        return results

    # ========== 题材规范化 ==========

    async def resolve_genre(self, input_text: str) -> list[dict[str, Any]]:
        """题材规范化解析"""
        rows = await self._db.fetch(
            "SELECT * FROM fn_genre_resolve($1)",
            input_text,
        )
        return rows_to_dicts(rows)

    async def list_genres(self) -> list[dict[str, Any]]:
        """列出所有 canonical genre"""
        rows = await self._db.fetch(
            "SELECT * FROM v_genre_canonical_list ORDER BY canonical_genre"
        )
        results = rows_to_dicts(rows)
        for r in results:
            if r.get("platform_tags"):
                r["platform_tags"] = list(r["platform_tags"]) if hasattr(r["platform_tags"], "__iter__") else []
            if r.get("aliases"):
                r["aliases"] = list(r["aliases"]) if hasattr(r["aliases"], "__iter__") else []
        return results

    # ========== CSV 导入导出 ==========

    async def csv_import(
        self,
        workspace_id: str,
        category_id: str,
        username: str,
        csv_content: str,
    ) -> dict[str, Any]:
        """CSV 导入"""
        reader = csv.DictReader(io.StringIO(csv_content))
        imported = 0
        errors = []

        for row_num, row in enumerate(reader, start=2):
            try:
                await self.upsert_item(
                    workspace_id=workspace_id,
                    category_id=category_id,
                    username=username,
                    item_code=row.get("item_code"),
                    core_summary=row.get("core_summary", ""),
                    keywords=self._parse_array(row.get("keywords")),
                    intent_synonyms=self._parse_array(row.get("intent_synonyms")),
                    detailed_expansion=row.get("detailed_expansion"),
                    ai_instruction=row.get("ai_instruction"),
                    poison_points=self._parse_array(row.get("poison_points")),
                    applicable_skills=self._parse_array(row.get("applicable_skills")),
                    applicable_genres=self._parse_array(row.get("applicable_genres")),
                    level=row.get("level", "knowledge"),
                    tags=self._parse_array(row.get("tags")),
                    is_global=True,
                )
                imported += 1
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})

        return {
            "imported": imported,
            "errors": errors,
            "total": imported + len(errors),
        }

    async def csv_export(
        self,
        workspace_id: str,
        category_id: str | None = None,
    ) -> str:
        """CSV 导出"""
        conditions = ["(workspace_id = $1 OR is_global = TRUE)"]
        params: list[Any] = [workspace_id]

        if category_id:
            conditions.append("category_id = $2")
            params.append(category_id)

        where_clause = " AND ".join(conditions)

        rows = await self._db.fetch(
            f"""
            SELECT 
                item_code,
                keywords,
                intent_synonyms,
                core_summary,
                detailed_expansion,
                ai_instruction,
                poison_points,
                level,
                applicable_skills,
                applicable_genres,
                tags
            FROM setting_items
            WHERE {where_clause}
            ORDER BY item_code
            """,
            *params,
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "item_code", "keywords", "intent_synonyms", "core_summary",
            "detailed_expansion", "ai_instruction", "poison_points",
            "level", "applicable_skills", "applicable_genres", "tags"
        ])

        for row in rows:
            writer.writerow([
                row["item_code"],
                "|".join(row["keywords"] or []),
                "|".join(row["intent_synonyms"] or []),
                row["core_summary"],
                row["detailed_expansion"],
                row["ai_instruction"],
                "|".join(row["poison_points"] or []),
                row["level"],
                "|".join(row["applicable_skills"] or []),
                "|".join(row["applicable_genres"] or []),
                "|".join(row["tags"] or []),
            ])

        return output.getvalue()

    def _parse_array(self, value: str | None, delimiter: str = "|") -> list[str]:
        """解析数组字符串"""
        if not value:
            return []
        return [v.strip() for v in value.split(delimiter) if v.strip()]