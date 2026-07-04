from typing import Any
from json import dumps as json_dumps
from .db import Database
from .utils import row_to_dict, rows_to_dicts


class KBService:
    """新知识库系统 - 通用知识/项目知识/实体/关联/世界状态"""

    def __init__(self, db: Database):
        self._db = db

    # ============================================================
    # ref_categories
    # ============================================================

    async def list_categories(self, parent_slug: str | None = None, include_all: bool = False) -> list[dict]:
        if include_all:
            rows = await self._db.fetch(
                """
                SELECT rc.id::text, rc.slug, rc.name, rc.description, rc.parent_id::text,
                       rc.genre_tags, rc.sort_order, rc.is_system,
                       (SELECT COUNT(*) FROM ref_categories child WHERE child.parent_id = rc.id) as child_count
                FROM ref_categories rc
                ORDER BY rc.sort_order
                """
            )
        elif parent_slug:
            rows = await self._db.fetch(
                """
                SELECT rc.id::text, rc.slug, rc.name, rc.description, rc.parent_id::text,
                       rc.genre_tags, rc.sort_order, rc.is_system,
                       (SELECT COUNT(*) FROM ref_categories child WHERE child.parent_id = rc.id) as child_count
                FROM ref_categories rc
                JOIN ref_categories parent ON parent.slug = $1
                WHERE rc.parent_id = parent.id
                ORDER BY rc.sort_order
                """,
                parent_slug,
            )
        else:
            rows = await self._db.fetch(
                """
                SELECT rc.id::text, rc.slug, rc.name, rc.description, rc.parent_id::text,
                       rc.genre_tags, rc.sort_order, rc.is_system,
                       (SELECT COUNT(*) FROM ref_categories child WHERE child.parent_id = rc.id) as child_count
                FROM ref_categories rc
                WHERE rc.parent_id IS NULL
                ORDER BY rc.sort_order
                """
            )
        return rows_to_dicts(rows)

    async def category_create(
        self, slug: str, name: str, parent_id: str | None = None,
        description: str | None = None, sort_order: int = 0,
    ) -> dict:
        row = await self._db.fetchrow(
            """
            INSERT INTO ref_categories (slug, name, parent_id, description, sort_order)
            VALUES ($1, $2, $3::uuid, $4, $5)
            RETURNING id::text, slug, name, parent_id::text, description, sort_order, is_system
            """,
            slug, name, parent_id, description, sort_order,
        )
        return dict(row) if row else {}

    async def category_update(
        self, category_id: str, name: str | None = None, slug: str | None = None,
        description: str | None = None, sort_order: int | None = None,
        parent_id: str | None = None,
    ) -> dict:
        sets, params, idx = [], [], 1
        if name is not None:
            sets.append(f"name = ${idx}"); params.append(name); idx += 1
        if slug is not None:
            sets.append(f"slug = ${idx}"); params.append(slug); idx += 1
        if description is not None:
            sets.append(f"description = ${idx}"); params.append(description); idx += 1
        if sort_order is not None:
            sets.append(f"sort_order = ${idx}"); params.append(sort_order); idx += 1
        if parent_id is not None:
            sets.append(f"parent_id = ${idx}::uuid"); params.append(parent_id if parent_id else None); idx += 1
        if not sets:
            return {}
        params.append(category_id)
        row = await self._db.fetchrow(
            f"UPDATE ref_categories SET {', '.join(sets)} WHERE id = ${idx} "
            "RETURNING id::text, slug, name, parent_id::text, description, sort_order, is_system",
            *params,
        )
        return dict(row) if row else {}

    async def category_delete(self, category_id: str) -> bool:
        result = await self._db.execute(
            "DELETE FROM ref_categories WHERE id = $1 AND is_system = false", category_id,
        )
        return result and "DELETE" in result

    # ============================================================
    # knowledge_entities
    # ============================================================

    async def entity_create(
        self,
        entity_type: str,
        name: str,
        content: str,
        summary: str | None = None,
        aliases: list[str] | None = None,
        structured_data: dict | None = None,
        source: str = "manual",
        source_url: str | None = None,
        reliability: float = 0.5,
        genre_tags: list[str] | None = None,
        era: str | None = None,
    ) -> dict:
        row = await self._db.fetchrow(
            """
            INSERT INTO knowledge_entities
                (entity_type, name, content, summary, aliases, structured_data,
                 source, source_url, reliability, genre_tags, era)
            VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7,$8,$9,$10,$11)
            RETURNING id::text, entity_type, name, summary, source, reliability,
                      genre_tags, era, status, created_at
            """,
            entity_type, name, content, summary,
            aliases or [], json_dumps(structured_data or {}),
            source, source_url, reliability,
            genre_tags or [], era,
        )
        return row_to_dict(row)

    async def entity_get(self, entity_id: str) -> dict | None:
        row = await self._db.fetchrow(
            "SELECT * FROM knowledge_entities WHERE id = $1", entity_id
        )
        return row_to_dict(row) if row else None

    async def entity_search(
        self,
        query: str,
        entity_type: str | None = None,
        genre: str | None = None,
        era: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        conditions = ["status = 'active'"]
        params: list[Any] = []
        idx = 0

        if query:
            idx += 1
            params.append(query)
            conditions.append(f"search_vector @@ plainto_tsquery('simple', ${idx})")

        if entity_type:
            idx += 1
            params.append(entity_type)
            conditions.append(f"entity_type = ${idx}")

        if genre:
            idx += 1
            params.append(genre)
            conditions.append(f"${idx} = ANY(genre_tags)")

        if era:
            idx += 1
            params.append(era)
            conditions.append(f"era ILIKE '%' || ${idx} || '%'")

        idx += 1
        params.append(limit)

        where = " AND ".join(conditions)
        rows = await self._db.fetch(
            f"""
            SELECT id::text, entity_type, name, aliases, summary, source,
                   reliability, genre_tags, era, status, use_count, created_at
            FROM knowledge_entities
            WHERE {where}
            ORDER BY reliability DESC, use_count DESC
            LIMIT ${idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def entity_update(self, entity_id: str, **fields) -> dict:
        set_clauses = []
        params: list[Any] = []
        idx = 0
        for k, v in fields.items():
            if k in ("name", "summary", "content", "source", "source_url", "era", "status"):
                idx += 1
                set_clauses.append(f"{k} = ${idx}")
                params.append(v)
            elif k == "aliases":
                idx += 1
                set_clauses.append(f"aliases = ${idx}")
                params.append(v or [])
            elif k == "genre_tags":
                idx += 1
                set_clauses.append(f"genre_tags = ${idx}")
                params.append(v or [])
            elif k == "structured_data":
                idx += 1
                set_clauses.append(f"structured_data = ${idx}::jsonb")
                params.append(json_dumps(v or {}))
            elif k == "reliability":
                idx += 1
                set_clauses.append(f"reliability = ${idx}")
                params.append(v)

        if not set_clauses:
            return await self.entity_get(entity_id)

        idx += 1
        params.append(entity_id)
        set_clauses.append("updated_at = now()")

        row = await self._db.fetchrow(
            f"UPDATE knowledge_entities SET {', '.join(set_clauses)} WHERE id = ${idx} RETURNING *",
            *params,
        )
        return row_to_dict(row) if row else None

    # ============================================================
    # knowledge_relations
    # ============================================================

    async def relation_create(
        self,
        from_entity_id: str,
        to_entity_id: str,
        relation_type: str,
        detail: str | None = None,
        strength: float = 1.0,
        metadata: dict | None = None,
    ) -> dict:
        row = await self._db.fetchrow(
            """
            INSERT INTO knowledge_relations (from_entity_id, to_entity_id, relation_type, relation_detail, strength, metadata)
            VALUES ($1,$2,$3,$4,$5,$6::jsonb)
            ON CONFLICT (from_entity_id, to_entity_id, relation_type) DO UPDATE SET
                relation_detail = EXCLUDED.relation_detail, strength = EXCLUDED.strength
            RETURNING id::text, from_entity_id::text, to_entity_id::text,
                      relation_type, relation_detail, strength, created_at
            """,
            from_entity_id, to_entity_id, relation_type, detail, strength,
            json_dumps(metadata or {}),
        )
        return row_to_dict(row)

    async def entity_list_relations(self, entity_id: str, relation_type: str | None = None) -> list[dict]:
        if relation_type:
            rows = await self._db.fetch(
                """
                SELECT kr.id::text, kr.relation_type, kr.relation_detail, kr.strength,
                       e.id::text as related_id, e.name as related_name, e.entity_type as related_type
                FROM knowledge_relations kr
                JOIN knowledge_entities e ON e.id = kr.to_entity_id
                WHERE kr.from_entity_id = $1 AND kr.relation_type = $2
                UNION
                SELECT kr.id::text, kr.relation_type, kr.relation_detail, kr.strength,
                       e.id::text as related_id, e.name as related_name, e.entity_type as related_type
                FROM knowledge_relations kr
                JOIN knowledge_entities e ON e.id = kr.from_entity_id
                WHERE kr.to_entity_id = $1 AND kr.relation_type = $2
                """,
                entity_id, relation_type,
            )
        else:
            rows = await self._db.fetch(
                """
                SELECT kr.id::text, kr.relation_type, kr.relation_detail, kr.strength,
                       e.id::text as related_id, e.name as related_name, e.entity_type as related_type,
                       CASE WHEN kr.from_entity_id = $1 THEN 'out' ELSE 'in' END as direction
                FROM knowledge_relations kr
                JOIN knowledge_entities e ON (
                    e.id = kr.to_entity_id AND kr.from_entity_id = $1
                ) OR (
                    e.id = kr.from_entity_id AND kr.to_entity_id = $1
                )
                """,
                entity_id,
            )
        return rows_to_dicts(rows)

    # ============================================================
    # universal_knowledge
    # ============================================================

    async def uk_search(
        self,
        query: str,
        category_slug: str | None = None,
        genre: str | None = None,
        era: str | None = None,
        year: int | None = None,
        limit: int = 20,
    ) -> list[dict]:
        conditions = ["uk.status = 'active'"]
        params: list[Any] = []
        idx = 0

        if query:
            idx += 1
            params.append(query)
            conditions.append(f"uk.search_vector @@ plainto_tsquery('simple', ${idx})")

        if category_slug:
            idx += 1
            params.append(category_slug)
            conditions.append(f"(rc.slug = ${idx} OR rc.parent_id IN (SELECT id FROM ref_categories WHERE slug = ${idx}))")

        if genre:
            idx += 1
            params.append(genre)
            conditions.append(f"${idx} = ANY(uk.genre_tags)")

        if era:
            idx += 1
            params.append(era)
            conditions.append(f"uk.era ILIKE '%' || ${idx} || '%'")

        if year is not None:
            idx += 1
            params.append(year)
            conditions.append(f"${idx} = ANY(uk.year_range)")

        idx += 1
        params.append(limit)

        where = " AND ".join(conditions)
        rows = await self._db.fetch(
            f"""
            SELECT uk.id::text, uk.topic, uk.summary, uk.content, uk.era,
                   uk.year_range, uk.genre_tags, uk.source, uk.source_url,
                   uk.reliability, uk.tags, uk.use_count, uk.created_at,
                   rc.slug as category_slug, rc.name as category_name
            FROM universal_knowledge uk
            LEFT JOIN ref_categories rc ON rc.id = uk.category_id
            WHERE {where}
            ORDER BY uk.reliability DESC, uk.use_count DESC
            LIMIT ${idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def uk_entry_create(
        self,
        topic: str,
        content: str,
        category_slug: str | None = None,
        summary: str | None = None,
        structured_data: dict | None = None,
        era: str | None = None,
        year_range: list[int] | None = None,
        genre_tags: list[str] | None = None,
        source: str = "manual",
        source_url: str | None = None,
        reliability: float = 0.5,
        tags: list[str] | None = None,
    ) -> dict:
        category_id = None
        if category_slug:
            cat = await self._db.fetchrow("SELECT id FROM ref_categories WHERE slug = $1", category_slug)
            if cat:
                category_id = cat["id"]

        row = await self._db.fetchrow(
            """
            INSERT INTO universal_knowledge
                (category_id, topic, content, summary, structured_data, era,
                 year_range, genre_tags, source, source_url, reliability, tags)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9,$10,$11,$12)
            RETURNING id::text, topic, summary, era, year_range, genre_tags,
                      source, reliability, status, created_at
            """,
            category_id, topic, content, summary,
            json_dumps(structured_data or {}), era,
            year_range or [], genre_tags or [],
            source, source_url, reliability, tags or [],
        )
        return row_to_dict(row)

    async def uk_entry_update(self, entry_id: str, **fields) -> dict:
        set_clauses = []
        params: list[Any] = []
        idx = 0
        for k, v in fields.items():
            if k in ("topic", "content", "summary", "era", "source", "source_url", "status"):
                idx += 1
                set_clauses.append(f"{k} = ${idx}")
                params.append(v)
            elif k == "genre_tags":
                idx += 1
                set_clauses.append(f"genre_tags = ${idx}")
                params.append(v or [])
            elif k == "year_range":
                idx += 1
                set_clauses.append(f"year_range = ${idx}")
                params.append(v or [])
            elif k == "tags":
                idx += 1
                set_clauses.append(f"tags = ${idx}")
                params.append(v or [])
            elif k == "reliability":
                idx += 1
                set_clauses.append(f"reliability = ${idx}")
                params.append(v)
            elif k == "structured_data":
                idx += 1
                set_clauses.append(f"structured_data = ${idx}::jsonb")
                params.append(json_dumps(v or {}))

        if not set_clauses:
            return {}

        idx += 1
        params.append(entry_id)
        set_clauses.append("updated_at = now()")

        row = await self._db.fetchrow(
            f"UPDATE universal_knowledge SET {', '.join(set_clauses)} WHERE id = ${idx} RETURNING id::text, topic, updated_at",
            *params,
        )
        return row_to_dict(row) if row else {}

    async def uk_entry_delete(self, entry_id: str) -> bool:
        result = await self._db.execute(
            "DELETE FROM universal_knowledge WHERE id = $1", entry_id
        )
        return result == "DELETE 1"

    async def uk_stats(self, genre: str | None = None) -> dict:
        conditions = ["uk.status = 'active'"]
        params: list[Any] = []
        idx = 0
        if genre:
            idx += 1
            params.append(genre)
            conditions.append(f"${idx} = ANY(uk.genre_tags)")

        where = " AND ".join(conditions)
        row = await self._db.fetchrow(
            f"""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT rc.slug) as categories,
                   SUM(CASE WHEN uk.source = 'web_search' THEN 1 ELSE 0 END) as from_web_search,
                   SUM(CASE WHEN uk.source = 'manual' THEN 1 ELSE 0 END) as from_manual,
                   AVG(uk.reliability) as avg_reliability
            FROM universal_knowledge uk
            LEFT JOIN ref_categories rc ON rc.id = uk.category_id
            WHERE {where}
            """,
            *params,
        )
        result = row_to_dict(row)

        cat_rows = await self._db.fetch(
            f"""
            SELECT rc.slug, rc.name, rc.parent_id::text, COUNT(uk.id) as count
            FROM ref_categories rc
            LEFT JOIN universal_knowledge uk ON uk.category_id = rc.id AND uk.status = 'active'
            GROUP BY rc.slug, rc.name, rc.parent_id, rc.sort_order
            ORDER BY rc.sort_order
            """
        )
        result["by_category"] = rows_to_dicts(cat_rows)
        return result

    # ============================================================
    # project_knowledge
    # ============================================================

    async def pk_upsert(
        self,
        project_id: str,
        category: str,
        key: str,
        value: dict,
        description: str | None = None,
        chapter_no: int | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        row = await self._db.fetchrow(
            """
            INSERT INTO project_knowledge (project_id, category, key, value, description, chapter_no, tags)
            VALUES ($1,$2,$3,$4::jsonb,$5,$6,$7)
            ON CONFLICT (project_id, category, key) DO UPDATE SET
                value = EXCLUDED.value, description = EXCLUDED.description,
                chapter_no = EXCLUDED.chapter_no, tags = EXCLUDED.tags,
                updated_at = now()
            RETURNING id::text, project_id::text, category, key, value,
                      description, chapter_no, tags, status, created_at, updated_at
            """,
            project_id, category, key, json_dumps(value),
            description, chapter_no, tags or [],
        )
        return row_to_dict(row)

    async def pk_get(self, project_id: str, category: str, key: str) -> dict | None:
        row = await self._db.fetchrow(
            "SELECT * FROM project_knowledge WHERE project_id = $1 AND category = $2 AND key = $3",
            project_id, category, key,
        )
        return row_to_dict(row) if row else None

    async def pk_list(self, project_id: str, category: str | None = None) -> list[dict]:
        if category:
            rows = await self._db.fetch(
                "SELECT * FROM project_knowledge WHERE project_id = $1 AND category = $2 AND status = 'active' ORDER BY key",
                project_id, category,
            )
        else:
            rows = await self._db.fetch(
                "SELECT * FROM project_knowledge WHERE project_id = $1 AND status = 'active' ORDER BY category, key",
                project_id,
            )
        return rows_to_dicts(rows)

    async def pk_delete(self, project_id: str, category: str, key: str) -> bool:
        result = await self._db.execute(
            "UPDATE project_knowledge SET status = 'deleted' WHERE project_id = $1 AND category = $2 AND key = $3",
            project_id, category, key,
        )
        return result == "UPDATE 1"

    # ============================================================
    # world_snapshots
    # ============================================================

    async def world_get_state(self, project_id: str, chapter_no: int | None = None) -> dict | None:
        if chapter_no is not None:
            row = await self._db.fetchrow(
                "SELECT * FROM world_snapshots WHERE project_id = $1 AND chapter_no = $2",
                project_id, chapter_no,
            )
        else:
            row = await self._db.fetchrow(
                "SELECT * FROM world_snapshots WHERE project_id = $1 ORDER BY chapter_no DESC LIMIT 1",
                project_id,
            )
        return row_to_dict(row) if row else None

    async def world_update_state(
        self,
        project_id: str,
        chapter_no: int,
        world_state: dict,
        story_time: str | None = None,
        story_year: int | None = None,
        story_era: str | None = None,
        story_progress: float | None = None,
        character_count: int | None = None,
        active_threads: list[str] | None = None,
    ) -> dict:
        row = await self._db.fetchrow(
            """
            INSERT INTO world_snapshots
                (project_id, chapter_no, world_state, story_time, story_year,
                 story_era, story_progress, character_count, active_threads)
            VALUES ($1,$2,$3::jsonb,$4,$5,$6,$7,$8,$9)
            ON CONFLICT (project_id, chapter_no) DO UPDATE SET
                world_state = EXCLUDED.world_state, story_time = EXCLUDED.story_time,
                story_year = EXCLUDED.story_year, story_era = EXCLUDED.story_era,
                story_progress = EXCLUDED.story_progress, character_count = EXCLUDED.character_count,
                active_threads = EXCLUDED.active_threads
            RETURNING id::text, project_id::text, chapter_no, story_time, story_year,
                      story_era, story_progress, world_state, character_count, active_threads, created_at
            """,
            project_id, chapter_no, json_dumps(world_state),
            story_time, story_year, story_era, story_progress,
            character_count, active_threads or [],
        )
        return row_to_dict(row)

    async def world_list_snapshots(self, project_id: str, limit: int = 10) -> list[dict]:
        rows = await self._db.fetch(
            "SELECT id::text, chapter_no, story_time, story_year, story_era, story_progress, character_count, active_threads, created_at FROM world_snapshots WHERE project_id = $1 ORDER BY chapter_no DESC LIMIT $2",
            project_id, limit,
        )
        return rows_to_dicts(rows)

    # ============================================================
    # search & gap
    # ============================================================

    async def search_create_job(
        self,
        query_text: str,
        project_id: str | None = None,
        category_slug: str | None = None,
        chapter_no: int | None = None,
        triggered_by: str = "manual",
    ) -> dict:
        category_id = None
        if category_slug:
            cat = await self._db.fetchrow("SELECT id FROM ref_categories WHERE slug = $1", category_slug)
            if cat:
                category_id = cat["id"]

        row = await self._db.fetchrow(
            """
            INSERT INTO ref_search_jobs (project_id, query_text, category_id, chapter_no, triggered_by)
            VALUES ($1,$2,$3,$4,$5)
            RETURNING id::text, query_text, status, created_at
            """,
            project_id, query_text, category_id, chapter_no, triggered_by,
        )
        return row_to_dict(row)

    async def search_complete_job(
        self, job_id: str, results_count: int, entries_created: int
    ) -> None:
        await self._db.execute(
            "UPDATE ref_search_jobs SET status = 'completed', results_count = $1, entries_created = $2, completed_at = now() WHERE id = $3",
            results_count, entries_created, job_id,
        )

    async def gap_create(
        self,
        description: str,
        project_id: str | None = None,
        gap_type: str = "missing_knowledge",
        entity_name: str | None = None,
        entity_type: str | None = None,
        context: str | None = None,
    ) -> dict:
        row = await self._db.fetchrow(
            """
            INSERT INTO ref_gap_logs (project_id, gap_type, description, context, entity_name, entity_type)
            VALUES ($1,$2,$3,$4,$5,$6)
            RETURNING id::text, gap_type, description, entity_name, resolved, created_at
            """,
            project_id, gap_type, description, context, entity_name, entity_type,
        )
        return row_to_dict(row)

    async def gap_list(self, project_id: str | None = None, resolved: bool = False) -> list[dict]:
        conditions = ["resolved = $1"]
        params: list[Any] = [resolved]
        idx = 1
        if project_id:
            idx += 1
            params.append(project_id)
            conditions.append(f"project_id = ${idx}")

        where = " AND ".join(conditions)
        rows = await self._db.fetch(
            f"SELECT * FROM ref_gap_logs WHERE {where} ORDER BY created_at DESC LIMIT 50",
            *params,
        )
        return rows_to_dicts(rows)

    async def gap_resolve(self, gap_id: str, entry_id: str | None = None) -> bool:
        result = await self._db.execute(
            "UPDATE ref_gap_logs SET resolved = true, resolved_by_entry_id = $1, resolved_at = now() WHERE id = $2",
            entry_id, gap_id,
        )
        return result == "UPDATE 1"

    # ============================================================
    # Genre Strategies
    # ============================================================

    GENRE_STRATEGIES = {
        "historical_republic": {
            "display_name": "民国历史",
            "strategy": "real_historical",
            "timeline_type": "real_year",
            "year_range": [1912, 1949],
            "data_sources": {"history": "web_search_by_year", "culture": "universal_knowledge"},
            "search_keywords": ["{year}年 中国", "{year}年 {city}", "{event} 历史"],
        },
        "historical_ancient": {
            "display_name": "古代历史",
            "strategy": "real_historical",
            "timeline_type": "dynasty",
            "dynasties": ["先秦", "秦汉", "三国", "晋", "南北朝", "隋唐", "宋元", "明清"],
            "data_sources": {"history": "web_search_by_dynasty", "culture": "universal_knowledge"},
            "search_keywords": ["{dynasty} 历史", "{dynasty} {topic}", "{event} {dynasty}"],
        },
        "xianxia": {
            "display_name": "仙侠",
            "strategy": "progression",
            "timeline_type": "cultivation_progress",
            "data_sources": {"cultivation": "genre_template"},
            "search_keywords": ["修仙体系", "修真境界", "丹药法宝"],
        },
        "xuanhuan": {
            "display_name": "玄幻",
            "strategy": "progression",
            "timeline_type": "power_progress",
            "data_sources": {"power_system": "genre_template"},
            "search_keywords": ["力量体系", "种族设定", "魔法体系"],
        },
        "sci-fi": {
            "display_name": "科幻",
            "strategy": "hybrid",
            "timeline_type": "future_year",
            "data_sources": {"science": "web_search", "tech": "genre_template"},
            "search_keywords": ["科幻设定", "未来科技", "太空殖民"],
        },
        "urban": {
            "display_name": "都市",
            "strategy": "real_modern",
            "timeline_type": "modern_year",
            "year_range": [2000, 2030],
            "data_sources": {"society": "web_search", "tech": "universal_knowledge"},
            "search_keywords": ["当代社会", "现代职业", "都市生活"],
        },
        "post_apocalyptic": {
            "display_name": "末日",
            "strategy": "pure_fiction",
            "timeline_type": "post_disaster",
            "data_sources": {"setting": "genre_template"},
            "search_keywords": ["末日设定", "变异类型", "生存体系"],
        },
        "horror": {
            "display_name": "灵异",
            "strategy": "pure_fiction",
            "timeline_type": "floating",
            "data_sources": {"supernatural": "genre_template"},
            "search_keywords": ["鬼怪分类", "灵异规则", "禁忌"],
        },
        "game": {
            "display_name": "游戏",
            "strategy": "pure_fiction",
            "timeline_type": "game_time",
            "data_sources": {"game_system": "genre_template"},
            "search_keywords": ["游戏系统", "技能树", "副本设计"],
        },
        "time_travel": {
            "display_name": "穿越",
            "strategy": "hybrid",
            "timeline_type": "cross_timeline",
            "data_sources": {"history": "web_search", "cheat": "genre_template"},
            "search_keywords": ["穿越设定", "金手指", "系统流"],
        },
        "isekai": {
            "display_name": "异世界",
            "strategy": "pure_fiction",
            "timeline_type": "floating",
            "data_sources": {"world": "genre_template"},
            "search_keywords": ["异世界设定", "召唤", "转生"],
        },
    }

    async def genre_list(self) -> list[dict]:
        return [
            {"id": k, **v}
            for k, v in self.GENRE_STRATEGIES.items()
        ]

    async def genre_get_strategy(self, genre_id: str) -> dict | None:
        return self.GENRE_STRATEGIES.get(genre_id)

    async def genre_get_search_keywords(self, genre_id: str, **kwargs) -> list[str]:
        """Generate search keywords for a genre with template variables filled."""
        strategy = self.GENRE_STRATEGIES.get(genre_id)
        if not strategy:
            return []
        keywords = []
        for template in strategy.get("search_keywords", []):
            kw = template
            for k, v in kwargs.items():
                kw = kw.replace(f"{{{k}}}", str(v))
            keywords.append(kw)
        return keywords

    async def genre_preheat(self, project_id: str, genre: str) -> dict:
        """Pre-load genre-related UK items into project_knowledge for faster retrieval."""
        strategy = self.GENRE_STRATEGIES.get(genre)
        if not strategy:
            return {"ok": False, "error": f"Unknown genre: {genre}"}

        # Find UK items matching this genre's categories
        category_map = {
            "xianxia": "kb_plot_templates",
            "xuanhuan": "kb_plot_templates",
            "urban": "kb_writing_technique",
            "sci-fi": "kb_setting_background",
            "horror": "kb_setting_background",
            "post_apocalyptic": "kb_setting_background",
            "game": "kb_plot_templates",
            "time_travel": "kb_plot_templates",
            "isekai": "kb_plot_templates",
            "historical_republic": "kb_setting_background",
            "historical_ancient": "kb_setting_background",
        }
        target_cat = category_map.get(genre, "kb_genre")

        # Query UK items by category
        rows = await self._db.fetch(
            """
            SELECT id::text, kb_code, topic, summary, content, genre_tags
            FROM universal_knowledge
            WHERE category_slug = $1
            ORDER BY reliability DESC NULLS LAST, use_count DESC NULLS LAST, RANDOM()
            LIMIT 20
            """,
            target_cat,
        )

        if not rows:
            return {"ok": True, "genre": genre, "preloaded": 0, "total_available": 0}

        created = 0
        for row in rows:
            key = f"preheat_{genre}_{row['kb_code'] or row['topic'][:50]}"
            value = {
                "topic": row["topic"],
                "summary": row["summary"] or "",
                "content": row["content"] or "",
                "source_uk_id": row["id"],
            }
            tags = [genre] + (row["genre_tags"] or [])
            # Use pk_upsert which has ON CONFLICT handling
            await self.pk_upsert(
                project_id=project_id,
                category="genre_template",
                key=key,
                value=value,
                description=f"[预热] {row['topic']}",
                tags=tags,
            )
            created += 1

        return {"ok": True, "genre": genre, "preloaded": created, "total_available": len(rows)}

    # ============================================================
    # Auto Search + AI Organize
    # ============================================================

    async def auto_search_and_organize(
        self,
        query: str,
        category_slug: str | None = None,
        genre_tags: list[str] | None = None,
        project_id: str | None = None,
        chapter_no: int | None = None,
    ) -> dict:
        """
        1. Create search job
        2. Return query for caller to execute web_search
        3. Caller passes results back to organize_and_store()
        """
        job = await self.search_create_job(
            query_text=query, project_id=project_id,
            category_slug=category_slug, chapter_no=chapter_no,
            triggered_by="auto_search",
        )
        return {
            "job_id": job["id"],
            "query": query,
            "status": "pending_search",
            "message": "Execute web_search with this query, then call kb.organize_and_store with results.",
        }

    async def organize_and_store(
        self,
        job_id: str,
        search_results: list[dict],
        category_slug: str | None = None,
        genre_tags: list[str] | None = None,
    ) -> dict:
        """
        Take web_search results, extract structured entries, store to universal_knowledge.
        search_results: list of {title, url, snippet} from web_search.
        """
        entries_created = 0
        entities_created = 0
        created_ids = []

        for result in search_results:
            title = result.get("title", "")
            url = result.get("url", "")
            snippet = result.get("snippet", result.get("content", ""))

            if not title or not snippet:
                continue

            # Store as universal knowledge entry
            entry = await self.uk_entry_create(
                topic=title,
                content=snippet,
                category_slug=category_slug,
                source="web_search",
                source_url=url,
                reliability=0.5,
                genre_tags=genre_tags or [],
            )
            entries_created += 1
            created_ids.append(entry["id"])

        await self.search_complete_job(
            job_id=job_id,
            results_count=len(search_results),
            entries_created=entries_created,
        )

        return {
            "job_id": job_id,
            "results_count": len(search_results),
            "entries_created": entries_created,
            "entry_ids": created_ids,
        }

    # ============================================================
    # Gap Detection
    # ============================================================

    async def detect_gaps(
        self,
        project_id: str,
        chapter_plan: str | None = None,
        chapter_no: int | None = None,
    ) -> dict:
        """
        Detect knowledge gaps from chapter plan text.
        Extracts entities/topics and checks if they exist in universal_knowledge or project_knowledge.
        """
        if not chapter_plan:
            return {"gaps": [], "message": "No chapter plan provided"}

        # Simple keyword extraction (common entity patterns)
        import re
        # Extract potential entity names (Chinese names, places, events)
        name_patterns = re.findall(r'[\u4e00-\u9fff]{2,6}', chapter_plan)
        # Deduplicate while preserving order
        seen = set()
        potential_entities = []
        for name in name_patterns:
            if name not in seen and len(name) >= 2:
                seen.add(name)
                potential_entities.append(name)

        gaps = []
        for entity_name in potential_entities[:20]:  # Limit to 20
            # Check universal_knowledge
            uk_rows = await self._db.fetch(
                "SELECT id FROM universal_knowledge WHERE topic ILIKE '%' || $1 || '%' AND status = 'active' LIMIT 1",
                entity_name,
            )
            # Check project_knowledge
            pk_rows = await self._db.fetch(
                "SELECT id FROM project_knowledge WHERE project_id = $1 AND (key ILIKE '%' || $2 || '%' OR value::text ILIKE '%' || $2 || '%') AND status = 'active' LIMIT 1",
                project_id, entity_name,
            )
            # Check knowledge_entities
            ke_rows = await self._db.fetch(
                "SELECT id FROM knowledge_entities WHERE name ILIKE '%' || $1 || '%' AND status = 'active' LIMIT 1",
                entity_name,
            )

            if not uk_rows and not pk_rows and not ke_rows:
                gap = await self.gap_create(
                    description=f"Missing knowledge for: {entity_name}",
                    project_id=project_id,
                    gap_type="missing_entity",
                    entity_name=entity_name,
                    context=chapter_plan[:200] if chapter_plan else None,
                )
                gaps.append(gap)

        return {
            "gaps_found": len(gaps),
            "gaps": gaps,
            "entities_checked": len(potential_entities[:20]),
        }

    # ============================================================
    # Knowledge Pack System
    # ============================================================

    async def get_genre_config(self, genre: str) -> dict | None:
        """获取小说类型的知识配置"""
        await self._db.connect()
        row = await self._db.fetchrow(
            "SELECT * FROM genre_knowledge_config WHERE genre = $1", genre
        )
        return row_to_dict(row) if row else None

    async def list_genre_configs(self) -> list[dict]:
        """列出所有小说类型配置"""
        await self._db.connect()
        rows = await self._db.fetch("SELECT * FROM genre_knowledge_config ORDER BY genre")
        return rows_to_dicts(rows)

    async def get_project_pack(self, project_id: str) -> dict | None:
        """获取项目知识包"""
        await self._db.connect()
        row = await self._db.fetchrow(
            "SELECT * FROM project_knowledge_pack WHERE project_id = $1", project_id
        )
        return row_to_dict(row) if row else None

    async def create_project_pack(self, project_id: str, genre: str) -> dict:
        """创建项目知识包（基于类型配置）"""
        await self._db.connect()
        config = await self.get_genre_config(genre)
        active_categories = config["included_categories"] if config else []

        row = await self._db.fetchrow(
            """INSERT INTO project_knowledge_pack (project_id, genre, active_categories)
               VALUES ($1, $2, $3)
               ON CONFLICT (project_id) DO UPDATE SET
                 genre = $2, active_categories = $3, updated_at = NOW()
               RETURNING *""",
            project_id, genre, active_categories,
        )
        return row_to_dict(row)

    async def update_project_pack(self, project_id: str, active_categories: list[str] | None = None, custom_categories: dict | None = None) -> dict:
        """更新项目知识包"""
        await self._db.connect()
        updates = []
        params = [project_id]
        param_idx = 2

        if active_categories is not None:
            updates.append(f"active_categories = ${param_idx}")
            params.append(active_categories)
            param_idx += 1

        if custom_categories is not None:
            from .utils import ensure_json_value
            updates.append(f"custom_categories = ${param_idx}")
            params.append(ensure_json_value(custom_categories))
            param_idx += 1

        updates.append("updated_at = NOW()")
        params.append(project_id)

        row = await self._db.fetchrow(
            f"UPDATE project_knowledge_pack SET {', '.join(updates)} WHERE project_id = ${param_idx} RETURNING *",
            *params,
        )
        return row_to_dict(row) if row else {}

    async def add_custom_category(self, project_id: str, name: str, parent: str | None = None, description: str = "") -> dict:
        """添加自定义分类"""
        await self._db.connect()
        pack = await self.get_project_pack(project_id)
        custom = pack.get("custom_categories", {}) if pack else {}
        custom[name] = {"parent": parent, "description": description}

        row = await self._db.fetchrow(
            """UPDATE project_knowledge_pack
               SET custom_categories = $2, updated_at = NOW()
               WHERE project_id = $1
               RETURNING *""",
            project_id, ensure_json_value(custom),
        )
        return row_to_dict(row) if row else {}

    async def remove_custom_category(self, project_id: str, name: str) -> dict:
        """移除自定义分类"""
        await self._db.connect()
        pack = await self.get_project_pack(project_id)
        custom = pack.get("custom_categories", {}) if pack else {}
        if name in custom:
            del custom[name]

        row = await self._db.fetchrow(
            """UPDATE project_knowledge_pack
               SET custom_categories = $2, updated_at = NOW()
               WHERE project_id = $1
               RETURNING *""",
            project_id, ensure_json_value(custom),
        )
        return row_to_dict(row) if row else {}

    async def get_active_categories(self, project_id: str) -> list[str]:
        """获取项目启用的分类（系统 + 自定义）"""
        await self._db.connect()
        pack = await self.get_project_pack(project_id)
        if not pack:
            return []
        active = pack.get("active_categories", [])
        custom = pack.get("custom_categories", {})
        return active + list(custom.keys())
