# Phase 7: P1 创作效率增强 - Prompt 模板托管服务

from typing import Any
from .db import Database
from .utils import ensure_json_value, row_to_dict, json_dumps


class PromptTemplateService:
    """Prompt 模板服务 - 管理 Prompt 模板"""

    def __init__(self, db: Database):
        self._db = db

    async def upsert_template(
        self,
        project_id: str,
        template_key: str,
        name: str,
        template_content: str,
        description: str | None = None,
        template_type: str = "system",
        variables: list[dict[str, Any]] | None = None,
        genre: str | None = None,
        scene: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """创建或更新 Prompt 模板"""
        row = await self._db.fetchrow(
            """
            INSERT INTO prompt_templates
              (project_id, template_key, name, description, template_content, template_type,
               variables, genre, scene, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9, $10)
            ON CONFLICT (project_id, template_key)
            DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                template_content = EXCLUDED.template_content,
                template_type = EXCLUDED.template_type,
                variables = EXCLUDED.variables,
                genre = EXCLUDED.genre,
                scene = EXCLUDED.scene,
                updated_at = NOW(),
                version = prompt_templates.version + 1
            RETURNING id::text, project_id::text, template_key, name, description, template_type,
                      variables, genre, scene, version, is_active, usage_count, created_at, updated_at
            """,
            project_id,
            template_key,
            name,
            description,
            template_content,
            template_type,
            json_dumps(variables or []),
            genre,
            scene,
            created_by,
        )
        result = row_to_dict(row)
        result["variables"] = ensure_json_value(result.get("variables"))
        return result

    async def get_template(
        self,
        project_id: str,
        template_key: str,
    ) -> dict[str, Any] | None:
        """获取模板"""
        row = await self._db.fetchrow(
            """
            SELECT id::text, project_id::text, template_key, name, description, template_content,
                   template_type, variables, genre, scene, version, is_active, usage_count,
                   last_used_at, created_by, created_at, updated_at
            FROM prompt_templates
            WHERE project_id = $1 AND template_key = $2
            """,
            project_id,
            template_key,
        )
        if row is None:
            return None
        result = row_to_dict(row)
        result["variables"] = ensure_json_value(result.get("variables"))
        return result

    async def list_templates(
        self,
        project_id: str,
        genre: str | None = None,
        scene: str | None = None,
        template_type: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """列出模板"""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        param_idx = 1

        if genre:
            param_idx += 1
            conditions.append(f"genre = ${param_idx}")
            params.append(genre)

        if scene:
            param_idx += 1
            conditions.append(f"scene = ${param_idx}")
            params.append(scene)

        if template_type:
            param_idx += 1
            conditions.append(f"template_type = ${param_idx}")
            params.append(template_type)

        if is_active is not None:
            param_idx += 1
            conditions.append(f"is_active = ${param_idx}")
            params.append(is_active)

        param_idx += 1
        params.append(limit)
        param_idx += 1
        params.append(offset)

        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, template_key, name, description, template_type,
                   genre, scene, version, is_active, usage_count, last_used_at, created_at
            FROM prompt_templates
            WHERE {' AND '.join(conditions)}
            ORDER BY name
            LIMIT ${param_idx - 1} OFFSET ${param_idx}
            """,
            *params,
        )
        return [row_to_dict(row) for row in rows]

    async def list_templates_by_workspace(
        self,
        workspace: str,
        principal: Any,
        genre: str | None = None,
        scene: str | None = None,
        template_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """跨项目列出模板（用于未选择项目时）"""
        conditions = ["p.workspace_id::text = $1"]
        params: list[Any] = [workspace]
        param_idx = 1

        if genre:
            param_idx += 1
            conditions.append(f"pt.genre = ${param_idx}")
            params.append(genre)

        if scene:
            param_idx += 1
            conditions.append(f"pt.scene = ${param_idx}")
            params.append(scene)

        if template_type:
            param_idx += 1
            conditions.append(f"pt.template_type = ${param_idx}")
            params.append(template_type)

        param_idx += 1
        params.append(limit)

        rows = await self._db.fetch(
            f"""
            SELECT pt.id::text, pt.project_id::text, pt.template_key, pt.name, pt.description,
                   pt.template_type, pt.genre, pt.scene, pt.version, pt.is_active,
                   pt.usage_count, pt.last_used_at, pt.created_at,
                   p.slug as project_slug, p.title as project_title
            FROM prompt_templates pt
            JOIN projects p ON pt.project_id = p.id
            WHERE {' AND '.join(conditions)}
            ORDER BY pt.name
            LIMIT ${param_idx}
            """,
            *params,
        )
        return [row_to_dict(row) for row in rows]

    async def delete_template(self, project_id: str, template_key: str) -> bool:
        """删除模板（系统模板不可删除）"""
        result = await self._db.execute(
            """
            DELETE FROM prompt_templates
            WHERE project_id = $1 AND template_key = $2 AND is_system = FALSE
            """,
            project_id,
            template_key,
        )
        return "DELETE 1" in result

    async def render_template(
        self,
        project_id: str,
        template_key: str,
        variables: dict[str, Any],
    ) -> dict[str, Any]:
        """渲染模板"""
        template = await self.get_template(project_id, template_key)
        if template is None:
            raise ValueError(f"Template not found: {template_key}")

        content = template["template_content"]
        # 简单的变量替换
        for var_name, var_value in variables.items():
            content = content.replace(f"{{{{{var_name}}}}}", str(var_value))

        # 记录使用
        await self._db.execute(
            """
            UPDATE prompt_templates
            SET usage_count = usage_count + 1, last_used_at = NOW()
            WHERE id = $1
            """,
            template["id"],
        )

        return {
            "template_key": template_key,
            "rendered_content": content,
            "variables_used": variables,
        }

    async def get_version_history(
        self,
        project_id: str,
        template_key: str,
    ) -> list[dict[str, Any]]:
        """获取版本历史"""
        rows = await self._db.fetch(
            """
            SELECT ptv.id::text, ptv.template_id::text, ptv.version, ptv.template_content,
                   ptv.variables, ptv.change_summary, ptv.created_by, ptv.created_at
            FROM prompt_template_versions ptv
            JOIN prompt_templates pt ON pt.id = ptv.template_id
            WHERE pt.project_id = $1 AND pt.template_key = $2
            ORDER BY ptv.version DESC
            """,
            project_id,
            template_key,
        )
        results = []
        for row in rows:
            r = row_to_dict(row)
            r["variables"] = ensure_json_value(r.get("variables"))
            results.append(r)
        return results


class ContextWeightService:
    """上下文权重服务"""

    def __init__(self, db: Database):
        self._db = db

    async def upsert_config(
        self,
        project_id: str,
        config_name: str,
        weights: dict[str, float],
        profile: str = "default",
        max_total_tokens: int = 8000,
        priority_order: list[str] | None = None,
    ) -> dict[str, Any]:
        """创建或更新权重配置"""
        row = await self._db.fetchrow(
            """
            INSERT INTO context_weight_configs
              (project_id, config_name, profile, weights, max_total_tokens, priority_order)
            VALUES ($1, $2, $3, $4::jsonb, $5, $6::jsonb)
            ON CONFLICT (project_id, config_name, profile)
            DO UPDATE SET
                weights = EXCLUDED.weights,
                max_total_tokens = EXCLUDED.max_total_tokens,
                priority_order = EXCLUDED.priority_order,
                updated_at = NOW()
            RETURNING id::text, project_id::text, config_name, profile, weights,
                      max_total_tokens, priority_order, is_active, created_at, updated_at
            """,
            project_id,
            config_name,
            profile,
            json_dumps(weights),
            max_total_tokens,
            json_dumps(priority_order or []),
        )
        result = row_to_dict(row)
        result["weights"] = ensure_json_value(result.get("weights"))
        result["priority_order"] = list(result.get("priority_order") or [])
        return result

    async def get_config(
        self,
        project_id: str,
        config_name: str,
        profile: str = "default",
    ) -> dict[str, Any] | None:
        """获取权重配置"""
        row = await self._db.fetchrow(
            """
            SELECT id::text, project_id::text, config_name, profile, weights,
                   max_total_tokens, priority_order, is_active
            FROM context_weight_configs
            WHERE project_id = $1 AND config_name = $2 AND profile = $3
            """,
            project_id,
            config_name,
            profile,
        )
        if row is None:
            return None
        result = row_to_dict(row)
        result["weights"] = ensure_json_value(result.get("weights"))
        result["priority_order"] = list(result.get("priority_order") or [])
        return result

    async def list_configs(
        self,
        project_id: str,
        profile: str | None = None,
    ) -> list[dict[str, Any]]:
        """列出配置"""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]

        if profile:
            conditions.append("profile = $2")
            params.append(profile)

        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, config_name, profile, weights,
                   max_total_tokens, priority_order, is_active
            FROM context_weight_configs
            WHERE {' AND '.join(conditions)}
            ORDER BY config_name
            """,
            *params,
        )
        results = []
        for row in rows:
            r = row_to_dict(row)
            r["weights"] = ensure_json_value(r.get("weights"))
            r["priority_order"] = list(r.get("priority_order") or [])
            results.append(r)
        return results


class ReferenceMaterialService:
    """素材库服务"""

    def __init__(self, db: Database):
        self._db = db

    async def upsert_material(
        self,
        project_id: str,
        material_key: str,
        title: str,
        material_type: str,
        content: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        source_url: str | None = None,
        source_credit: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """创建或更新素材"""
        row = await self._db.fetchrow(
            """
            INSERT INTO reference_materials
              (project_id, material_key, title, content, material_type, category,
               tags, source_url, source_credit, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (project_id, material_key)
            DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                material_type = EXCLUDED.material_type,
                category = EXCLUDED.category,
                tags = EXCLUDED.tags,
                source_url = EXCLUDED.source_url,
                source_credit = EXCLUDED.source_credit,
                updated_at = NOW()
            RETURNING id::text, project_id::text, material_key, title, material_type,
                      category, tags, source_url, source_credit, usage_count, favorite,
                      created_by, created_at, updated_at
            """,
            project_id,
            material_key,
            title,
            content,
            material_type,
            category,
            tags or [],
            source_url,
            source_credit,
            created_by,
        )
        result = row_to_dict(row)
        result["tags"] = list(result.get("tags") or [])
        return result

    async def get_material(
        self,
        project_id: str,
        material_key: str,
    ) -> dict[str, Any] | None:
        """获取素材"""
        row = await self._db.fetchrow(
            """
            SELECT id::text, project_id::text, material_key, title, content, material_type,
                   category, tags, source_url, source_credit, usage_count, favorite,
                   created_by, created_at, updated_at
            FROM reference_materials
            WHERE project_id = $1 AND material_key = $2
            """,
            project_id,
            material_key,
        )
        if row is None:
            return None
        result = row_to_dict(row)
        result["tags"] = list(result.get("tags") or [])
        return result

    async def list_materials(
        self,
        project_id: str,
        material_type: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        favorite: bool | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """列出素材"""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        param_idx = 1

        if material_type:
            param_idx += 1
            conditions.append(f"material_type = ${param_idx}")
            params.append(material_type)

        if category:
            param_idx += 1
            conditions.append(f"category = ${param_idx}")
            params.append(category)

        if favorite is not None:
            param_idx += 1
            conditions.append(f"favorite = ${param_idx}")
            params.append(favorite)

        if tags:
            param_idx += 1
            conditions.append(f"tags && ${param_idx}")
            params.append(tags)

        if search:
            param_idx += 1
            conditions.append(f"(title ILIKE ${param_idx} OR content ILIKE ${param_idx})")
            params.append(f"%{search}%")

        param_idx += 1
        params.append(limit)
        param_idx += 1
        params.append(offset)

        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, material_key, title, material_type,
                   category, tags, usage_count, favorite, created_at
            FROM reference_materials
            WHERE {' AND '.join(conditions)}
            ORDER BY favorite DESC, usage_count DESC, created_at DESC
            LIMIT ${param_idx - 1} OFFSET ${param_idx}
            """,
            *params,
        )
        results = []
        for row in rows:
            r = row_to_dict(row)
            r["tags"] = list(r.get("tags") or [])
            results.append(r)
        return results

    async def toggle_favorite(
        self,
        project_id: str,
        material_key: str,
    ) -> dict[str, Any]:
        """切换收藏状态"""
        row = await self._db.fetchrow(
            """
            UPDATE reference_materials
            SET favorite = NOT favorite, updated_at = NOW()
            WHERE project_id = $1 AND material_key = $2
            RETURNING id::text, material_key, favorite
            """,
            project_id,
            material_key,
        )
        return row_to_dict(row) if row else {}

    async def delete_material(self, project_id: str, material_key: str) -> bool:
        """删除素材"""
        result = await self._db.execute(
            """
            DELETE FROM reference_materials
            WHERE project_id = $1 AND material_key = $2
            """,
            project_id,
            material_key,
        )
        return "DELETE 1" in result


class ReaderExpectationService:
    """读者期待服务"""

    def __init__(self, db: Database):
        self._db = db

    async def upsert_expectation(
        self,
        project_id: str,
        expectation_key: str,
        title: str,
        expectation_type: str,
        description: str | None = None,
        chapter_no: int | None = None,
        importance: str = "medium",
        tags: list[str] | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """创建或更新期待"""
        row = await self._db.fetchrow(
            """
            INSERT INTO reader_expectations
              (project_id, expectation_key, title, description, expectation_type,
               chapter_no, importance, tags, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (project_id, expectation_key)
            DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                expectation_type = EXCLUDED.expectation_type,
                chapter_no = EXCLUDED.chapter_no,
                importance = EXCLUDED.importance,
                tags = EXCLUDED.tags,
                updated_at = NOW()
            RETURNING id::text, project_id::text, expectation_key, title, description,
                      expectation_type, status, chapter_no, payoff_chapter_no, importance,
                      tags, created_by, created_at, updated_at
            """,
            project_id,
            expectation_key,
            title,
            description,
            expectation_type,
            chapter_no,
            importance,
            tags or [],
            created_by,
        )
        result = row_to_dict(row)
        result["tags"] = list(result.get("tags") or [])
        return result

    async def list_expectations(
        self,
        project_id: str,
        status: str | None = None,
        expectation_type: str | None = None,
        importance: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """列出期待"""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        param_idx = 1

        if status:
            param_idx += 1
            conditions.append(f"status = ${param_idx}")
            params.append(status)

        if expectation_type:
            param_idx += 1
            conditions.append(f"expectation_type = ${param_idx}")
            params.append(expectation_type)

        if importance:
            param_idx += 1
            conditions.append(f"importance = ${param_idx}")
            params.append(importance)

        param_idx += 1
        params.append(limit)

        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, expectation_key, title, expectation_type,
                   status, chapter_no, payoff_chapter_no, importance, tags
            FROM reader_expectations
            WHERE {' AND '.join(conditions)}
            ORDER BY importance DESC, chapter_no
            LIMIT ${param_idx - 1}
            """,
            *params,
        )
        results = []
        for row in rows:
            r = row_to_dict(row)
            r["tags"] = list(r.get("tags") or [])
            results.append(r)
        return results

    async def mark_fulfilled(
        self,
        project_id: str,
        expectation_key: str,
        payoff_chapter_no: int,
    ) -> dict[str, Any]:
        """标记为已回收"""
        row = await self._db.fetchrow(
            """
            UPDATE reader_expectations
            SET status = 'fulfilled', payoff_chapter_no = $3, updated_at = NOW()
            WHERE project_id = $1 AND expectation_key = $2
            RETURNING id::text, status, payoff_chapter_no
            """,
            project_id,
            expectation_key,
            payoff_chapter_no,
        )
        return row_to_dict(row) if row else {}


class ChapterAnnotationService:
    """章节批注服务"""

    def __init__(self, db: Database):
        self._db = db

    async def create_annotation(
        self,
        project_id: str,
        chapter_id: str,
        chapter_no: int,
        annotation_type: str,
        content: str,
        anchor_start: int | None = None,
        anchor_end: int | None = None,
        parent_id: str | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """创建批注"""
        row = await self._db.fetchrow(
            """
            INSERT INTO chapter_annotations
              (project_id, chapter_id, chapter_no, annotation_type, content,
               anchor_start, anchor_end, parent_id, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id::text, project_id::text, chapter_id::text, chapter_no, annotation_type,
                      content, anchor_start, anchor_end, parent_id::text, resolve_status,
                      resolved_by, resolved_at, created_by, created_at
            """,
            project_id,
            chapter_id,
            chapter_no,
            annotation_type,
            content,
            anchor_start,
            anchor_end,
            parent_id,
            created_by,
        )
        return row_to_dict(row)

    async def list_annotations(
        self,
        project_id: str,
        chapter_id: str | None = None,
        annotation_type: str | None = None,
        resolve_status: str | None = None,
    ) -> list[dict[str, Any]]:
        """列出批注"""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        param_idx = 1

        if chapter_id:
            param_idx += 1
            conditions.append(f"chapter_id = ${param_idx}")
            params.append(chapter_id)

        if annotation_type:
            param_idx += 1
            conditions.append(f"annotation_type = ${param_idx}")
            params.append(annotation_type)

        if resolve_status:
            param_idx += 1
            conditions.append(f"resolve_status = ${param_idx}")
            params.append(resolve_status)

        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, chapter_id::text, chapter_no, annotation_type,
                   content, anchor_start, anchor_end, parent_id::text, resolve_status,
                   resolved_by, resolved_at, created_by, created_at
            FROM chapter_annotations
            WHERE {' AND '.join(conditions)}
            ORDER BY chapter_no, anchor_start, created_at
            """,
            *params,
        )
        return [row_to_dict(row) for row in rows]

    async def resolve_annotation(
        self,
        project_id: str,
        annotation_id: str,
        resolved_by: str,
    ) -> dict[str, Any]:
        """解决批注"""
        row = await self._db.fetchrow(
            """
            UPDATE chapter_annotations
            SET resolve_status = 'resolved', resolved_by = $3, resolved_at = NOW()
            WHERE project_id = $1 AND id = $2
            RETURNING id::text, resolve_status, resolved_by, resolved_at
            """,
            project_id,
            annotation_id,
            resolved_by,
        )
        return row_to_dict(row) if row else {}


class ProperNounService:
    """专有名词服务"""

    def __init__(self, db: Database):
        self._db = db

    async def upsert_noun(
        self,
        project_id: str,
        noun_key: str,
        noun_value: str,
        noun_type: str,
        aliases: list[str] | None = None,
        description: str | None = None,
        locked: bool = False,
        first_chapter_no: int | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """创建或更新名词"""
        row = await self._db.fetchrow(
            """
            INSERT INTO proper_nouns
              (project_id, noun_key, noun_value, noun_type, aliases, description,
               locked, first_chapter_no, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (project_id, noun_key)
            DO UPDATE SET
                noun_value = EXCLUDED.noun_value,
                noun_type = EXCLUDED.noun_type,
                aliases = EXCLUDED.aliases,
                description = EXCLUDED.description,
                locked = EXCLUDED.locked,
                updated_at = NOW()
            RETURNING id::text, project_id::text, noun_key, noun_value, noun_type,
                      aliases, description, locked, usage_count, first_chapter_no,
                      created_by, created_at, updated_at
            """,
            project_id,
            noun_key,
            noun_value,
            noun_type,
            aliases or [],
            description,
            locked,
            first_chapter_no,
            created_by,
        )
        result = row_to_dict(row)
        result["aliases"] = list(result.get("aliases") or [])
        return result

    async def list_nouns(
        self,
        project_id: str,
        noun_type: str | None = None,
        locked: bool | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        """列出名词"""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        param_idx = 1

        if noun_type:
            param_idx += 1
            conditions.append(f"noun_type = ${param_idx}")
            params.append(noun_type)

        if locked is not None:
            param_idx += 1
            conditions.append(f"locked = ${param_idx}")
            params.append(locked)

        if search:
            param_idx += 1
            conditions.append(f"(noun_value ILIKE ${param_idx} OR noun_key ILIKE ${param_idx})")
            params.append(f"%{search}%")

        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, noun_key, noun_value, noun_type,
                   aliases, locked, usage_count, created_at
            FROM proper_nouns
            WHERE {' AND '.join(conditions)}
            ORDER BY noun_type, noun_value
            """,
            *params,
        )
        results = []
        for row in rows:
            r = row_to_dict(row)
            r["aliases"] = list(r.get("aliases") or [])
            results.append(r)
        return results

    async def check_consistency(
        self,
        project_id: str,
        text: str,
    ) -> dict[str, Any]:
        """检查文本中名词一致性"""
        nouns = await self.list_nouns(project_id)

        found = []
        missing = []

        for noun in nouns:
            if noun["noun_value"] in text or noun["noun_key"] in text:
                found.append({
                    "noun_key": noun["noun_key"],
                    "noun_value": noun["noun_value"],
                    "locked": noun["locked"],
                })
            else:
                for alias in noun.get("aliases", []):
                    if alias in text:
                        found.append({
                            "noun_key": noun["noun_key"],
                            "noun_value": noun["noun_value"],
                            "alias_used": alias,
                            "locked": noun["locked"],
                        })
                        break

        return {
            "checked": len(text),
            "found": found,
            "missing": missing,
            "inconsistent": [n for n in found if n.get("locked") and n.get("alias_used")],
        }


class FulltextSearchService:
    """全文检索服务"""

    def __init__(self, db: Database):
        self._db = db

    async def index_record(
        self,
        project_id: str,
        source_type: str,
        source_id: str,
        title: str,
        content: str,
        source_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """索引记录"""
        row = await self._db.fetchrow(
            """
            INSERT INTO fulltext_search_records
              (project_id, source_type, source_id, source_key, title, content, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
            ON CONFLICT (source_type, source_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                source_key = EXCLUDED.source_key,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING id::text, source_type, source_id, title, updated_at
            """,
            project_id,
            source_type,
            source_id,
            source_key,
            title,
            content,
            json_dumps(metadata or {}),
        )
        return row_to_dict(row) if row else {}

    async def search(
        self,
        project_id: str,
        query: str,
        source_types: list[str] | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """全文搜索"""
        conditions = ["project_id = $1", "search_vector @@ plainto_tsquery('chinese', $2)"]
        params: list[Any] = [project_id, query]
        param_idx = 2

        if source_types:
            param_idx += 1
            conditions.append(f"source_type = ANY(${param_idx})")
            params.append(source_types)

        param_idx += 1
        params.append(limit)

        rows = await self._db.fetch(
            f"""
            SELECT id::text, source_type, source_id, source_key, title,
                   ts_rank(search_vector, plainto_tsquery('chinese', $2)) as rank,
                   ts_headline('chinese', content, plainto_tsquery('chinese', $2),
                               'MaxWords=50, MinWords=20') as snippet
            FROM fulltext_search_records
            WHERE {' AND '.join(conditions)}
            ORDER BY rank DESC
            LIMIT ${param_idx - 1}
            """,
            *params,
        )
        return [row_to_dict(row) for row in rows]
