# Phase 8: P2 远期扩展 - 人物关系图谱服务

import logging
from typing import Any
from json import dumps as json_dumps
from .db import Database
from .utils import row_to_dict, ensure_json_value

logger = logging.getLogger("novel_os_mcp.p8_services")


class RelationshipGraphService:
    """人物关系图谱服务 - 提供实体关系可视化数据"""

    def __init__(self, db: Database):
        self._db = db

    async def get_graph_data(
        self,
        project_id: str,
        entity_types: list[str] | None = None,
        depth: int = 2,
    ) -> dict[str, Any]:
        """获取关系图谱数据（用于可视化）"""
        # 获取所有实体
        type_condition = ""
        params: list[Any] = [project_id]

        if entity_types:
            placeholders = ",".join(f"${i+2}" for i in range(len(entity_types)))
            type_condition = f"AND entity_type IN ({placeholders})"
            params.extend(entity_types)

        entities = await self._db.fetch(
            f"""
            SELECT id::text, entity_type, name, core_profile
            FROM state_entities
            WHERE project_id = $1 AND isarchived = FALSE {type_condition}
            """,
            *params,
        )

        # 获取所有关系
        entity_ids = [e["id"] for e in entities]
        if not entity_ids:
            return {"nodes": [], "edges": []}

        placeholders = ",".join(f"${i+2}" for i in range(len(entity_ids)))
        relations = await self._db.fetch(
            f"""
            SELECT id::text, source_entity_id::text, target_entity_id::text,
                   relationship_type, attitude, intensity, visibility
            FROM entity_relationships
            WHERE project_id = $1
              AND (source_entity_id IN ({placeholders}) OR target_entity_id IN ({placeholders}))
              AND status IN ('active', 'known')
            """,
            project_id,
            *entity_ids,
        )

        # 构建图数据
        nodes = []
        for e in entities:
            nodes.append({
                "id": e["id"],
                "type": e["entity_type"],
                "name": e["name"],
                "profile": e["core_profile"][:200] if e["core_profile"] else None,
            })

        edges = []
        for r in relations:
            edges.append({
                "id": r["id"],
                "source": r["source_entity_id"],
                "target": r["target_entity_id"],
                "type": r["relationship_type"],
                "attitude": r["attitude"],
                "intensity": r["intensity"],
                "visibility": r["visibility"],
            })

        return {"nodes": nodes, "edges": edges}

    async def get_subgraph(
        self,
        project_id: str,
        center_entity_id: str,
        depth: int = 2,
    ) -> dict[str, Any]:
        """获取以特定实体为中心的子图"""
        # 获取直接关联的实体
        direct_relations = await self._db.fetch(
            """
            SELECT DISTINCT
                CASE
                    WHEN source_entity_id = $2 THEN target_entity_id
                    ELSE source_entity_id
                END as entity_id
            FROM entity_relationships
            WHERE project_id = $1
              AND (source_entity_id = $2 OR target_entity_id = $2)
              AND status IN ('active', 'known')
            """,
            project_id,
            center_entity_id,
        )

        entity_ids = [center_entity_id] + [r["entity_id"] for r in direct_relations]

        if not entity_ids:
            return {"nodes": [], "edges": []}

        placeholders = ",".join(f"${i+2}" for i in range(len(entity_ids)))

        # 获取这些实体的信息
        entities = await self._db.fetch(
            f"""
            SELECT id::text, entity_type, name
            FROM state_entities
            WHERE project_id = $1 AND id IN ({placeholders}) AND isarchived = FALSE
            """,
            project_id,
            *entity_ids,
        )

        # 获取这些实体之间的关系
        relations = await self._db.fetch(
            f"""
            SELECT id::text, source_entity_id::text, target_entity_id::text,
                   relationship_type, attitude, intensity
            FROM entity_relationships
            WHERE project_id = $1
              AND source_entity_id IN ({placeholders})
              AND target_entity_id IN ({placeholders})
              AND status IN ('active', 'known')
            """,
            project_id,
            *entity_ids,
            *entity_ids,
        )

        nodes = [{"id": e["id"], "type": e["entity_type"], "name": e["name"]} for e in entities]
        edges = [
            {
                "id": r["id"],
                "source": r["source_entity_id"],
                "target": r["target_entity_id"],
                "type": r["relationship_type"],
                "attitude": r["attitude"],
                "intensity": r["intensity"],
            }
            for r in relations
        ]

        return {"nodes": nodes, "edges": edges}

    async def get_timeline_data(
        self,
        project_id: str,
        entity_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """获取时间线数据"""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        param_idx = 1

        if entity_id:
            param_idx += 1
            conditions.append("entity_id = $" + str(param_idx))
            params.append(entity_id)

        rows = await self._db.fetch(
            f"""
            SELECT id::text, entity_id::text, chapter_no, volume_no,
                   state_change_type, description, created_at
            FROM state_snapshots
            WHERE {' AND '.join(conditions)}
            ORDER BY chapter_no, volume_no, created_at
            LIMIT 500
            """,
            *params,
        )
        return [row_to_dict(row) for row in rows]


class TemplateMarketService:
    """模板市场服务 - 分享和发现 Prompt 模板"""

    def __init__(self, db: Database):
        self._db = db

    async def publish_template(
        self,
        project_id: str,
        template_key: str,
        marketplace_category: str,
        tags: list[str] | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """发布模板到市场"""
        row = await self._db.fetchrow(
            """
            UPDATE prompt_templates
            SET metadata = jsonb_set(
                COALESCE(metadata, '{}'),
                '{marketplace}',
                jsonb_build_object('category', $3, 'tags', $4::jsonb, 'published', true)
            )
            WHERE project_id = $1 AND template_key = $2
            RETURNING id::text, template_key, metadata
            """,
            project_id,
            template_key,
            marketplace_category,
            tags or [],
        )
        return row_to_dict(row) if row else {}

    async def discover_templates(
        self,
        category: str | None = None,
        tags: list[str] | None = None,
        search: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """发现市场模板"""
        conditions = ["is_active = true"]
        params: list[Any] = []
        param_idx = 0

        if category:
            param_idx += 1
            conditions.append(f"metadata->'marketplace'->>'category' = ${param_idx}")
            params.append(category)

        if tags:
            param_idx += 1
            conditions.append(f"metadata->'marketplace'->'tags' ?| ${param_idx}::text[]")
            params.append(tags)

        if search:
            param_idx += 1
            conditions.append(f"(name ILIKE ${param_idx} OR description ILIKE ${param_idx})")
            params.append(f"%{search}%")

        param_idx += 1
        params.append(limit)

        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, template_key, name, description,
                   genre, metadata->'marketplace'->>'category' as category,
                   metadata->'marketplace'->'tags' as tags,
                   usage_count
            FROM prompt_templates
            WHERE {' AND '.join(conditions)}
            ORDER BY usage_count DESC
            LIMIT ${param_idx}
            """,
            *params,
        )
        return [row_to_dict(row) for row in rows]


class OfflineEnhancementService:
    """离线写作增强服务"""

    def __init__(self, db: Database):
        self._db = db

    async def create_offline_session(
        self,
        project_id: str,
        session_name: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        """创建离线写作会话"""
        row = await self._db.fetchrow(
            """
            INSERT INTO offline_sync_sessions (project_id, session_name, description)
            VALUES ($1, $2, $3)
            RETURNING id::text, project_id::text, session_name, description, status,
                      created_at, updated_at
            """,
            project_id,
            session_name,
            description,
        )
        return row_to_dict(row) if row else {}

    async def queue_offline_changes(
        self,
        session_id: str,
        change_type: str,
        entity_type: str,
        entity_id: str,
        change_data: dict[str, Any],
    ) -> dict[str, Any]:
        """队列离线变更"""
        row = await self._db.fetchrow(
            """
            INSERT INTO offline_change_queue
              (session_id, change_type, entity_type, entity_id, change_data)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            RETURNING id::text, session_id::text, change_type, entity_type, status
            """,
            session_id,
            change_type,
            entity_type,
            entity_id,
            json_dumps(change_data),
        )
        return row_to_dict(row) if row else {}

    async def sync_offline_session(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        """同步离线会话"""
        # 获取所有待同步的变更
        changes = await self._db.fetch(
            """
            SELECT id::text, change_type, entity_type, entity_id, change_data
            FROM offline_change_queue
            WHERE session_id = $1 AND status = 'pending'
            ORDER BY created_at
            """,
            session_id,
        )

        synced = 0
        failed = 0

        for change in changes:
            try:
                # 根据变更类型执行同步
                if change["change_type"] == "upsert":
                    await self._apply_upsert(change)
                elif change["change_type"] == "delete":
                    await self._apply_delete(change)

                # 标记为已同步
                await self._db.execute(
                    "UPDATE offline_change_queue SET status = 'synced' WHERE id = $1",
                    change["id"],
                )
                synced += 1
            except Exception:
                await self._db.execute(
                    "UPDATE offline_change_queue SET status = 'failed' WHERE id = $1",
                    change["id"],
                )
                failed += 1

        # 更新会话状态
        new_status = "completed" if failed == 0 else "partial"
        await self._db.execute(
            "UPDATE offline_sync_sessions SET status = $1, synced_at = NOW() WHERE id = $2",
            new_status,
            session_id,
        )

        return {"synced": synced, "failed": failed, "status": new_status}

    async def _apply_upsert(self, change: dict[str, Any]) -> None:
        """Apply an upsert change from offline sync."""
        entity_type = change.get("entity_type", "")
        entity_id = change.get("entity_id")
        data = change.get("data", {})

        if entity_type == "state_entity":
            name = data.get("name", "")
            etype = data.get("entity_type", "character")
            profile = json_dumps(data.get("core_profile", {}))
            await self._db.execute(
                """
                INSERT INTO state_entities (id, project_id, entity_type, name, core_profile)
                VALUES ($1::uuid, $2::uuid, $3, $4, $5::jsonb)
                ON CONFLICT (project_id, name) DO UPDATE SET
                    core_profile = EXCLUDED.core_profile, updated_at = NOW()
                """,
                entity_id, change.get("project_id"), etype, name, profile,
            )
        elif entity_type == "state_snapshot":
            await self._db.execute(
                """
                INSERT INTO state_snapshots (project_id, entity_id, is_current, state, source_type)
                VALUES ($1::uuid, $2::uuid, true, $3::jsonb, 'offline_sync')
                """,
                change.get("project_id"), entity_id, json_dumps(data.get("state", {})),
            )
        elif entity_type == "foreshadowing":
            await self._db.execute(
                """
                INSERT INTO foreshadowing (project_id, clue_text, payoff_status, planted_chapter_no, priority)
                VALUES ($1::uuid, $2, $3, $4, $5)
                ON CONFLICT DO NOTHING
                """,
                change.get("project_id"), data.get("clue_text", ""),
                data.get("payoff_status", "planted"),
                data.get("planted_chapter_no"), data.get("priority", "medium"),
            )
        else:
            logger.warning("Unknown entity_type in offline upsert: %s", entity_type)

    async def _apply_delete(self, change: dict[str, Any]) -> None:
        """Apply a delete change from offline sync."""
        entity_type = change.get("entity_type", "")
        entity_id = change.get("entity_id")

        if entity_type == "state_entity":
            await self._db.execute(
                "UPDATE state_entities SET isarchived = TRUE WHERE id = $1::uuid",
                entity_id,
            )
        elif entity_type == "foreshadowing":
            await self._db.execute(
                "UPDATE foreshadowing SET payoff_status = 'cancelled' WHERE id = $1::uuid",
                entity_id,
            )
        else:
            logger.warning("Unknown entity_type in offline delete: %s", entity_type)


class VoiceInputService:
    """语音输入服务"""

    def __init__(self, db: Database):
        self._db = db

    async def save_voice_draft(
        self,
        project_id: str,
        audio_data: str,  # base64 编码的音频
        transcription: str,
        chapter_no: int | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        """保存语音草稿"""
        row = await self._db.fetchrow(
            """
            INSERT INTO voice_drafts
              (project_id, audio_data, transcription, chapter_no, created_by)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id::text, project_id::text, chapter_no, transcription, status
            """,
            project_id,
            audio_data,
            transcription,
            chapter_no,
            created_by,
        )
        return row_to_dict(row) if row else {}

    async def list_voice_drafts(
        self,
        project_id: str,
        chapter_no: int | None = None,
    ) -> list[dict[str, Any]]:
        """列出语音草稿"""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]

        if chapter_no is not None:
            conditions.append("chapter_no = $2")
            params.append(chapter_no)

        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, chapter_no, transcription,
                   status, created_at
            FROM voice_drafts
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            """,
            *params,
        )
        return [row_to_dict(row) for row in rows]
