"""Knowledge Audit Service — 多模型知识库审计
Scans all knowledge categories, sends to multiple analysis models,
generates evolution proposals for gaps and improvements.
"""
import json
import logging
from typing import Any

from ..db import Database

logger = logging.getLogger("novel_os_mcp.services.knowledge_audit")


class KnowledgeAuditService:
    """知识审计服务"""

    def __init__(self, db: Database, llm_client=None):
        self._db = db
        self._llm = llm_client

    async def audit_all(self, project_id: str, mode: str | None = None) -> dict[str, Any]:
        """审计所有知识分类，返回生成的提案统计。

        Args:
            project_id: 项目 UUID
            mode: None=新增+优化, "add"=只新增, "optimize"=只优化

        Returns:
            {total_proposals, categories}
        """
        categories = await self._list_categories(project_id)
        all_proposals = []
        summary = {}

        for cat in categories:
            try:
                result = await self._audit_category(project_id, cat, mode)
                all_proposals.extend(result.get("proposals", []))
                summary[cat["name"]] = {
                    "proposals": len(result.get("proposals", [])),
                    "models_used": result.get("models_used", []),
                }
            except Exception as e:
                logger.warning("Audit failed for category %s: %s", cat["name"], e)
                summary[cat["name"]] = {"error": str(e)}

        return {"total_proposals": len(all_proposals), "categories": summary, "_proposals": all_proposals}

    async def _list_categories(self, project_id: str) -> list[dict]:
        """列出所有需要审计的知识分类（限制总数不超过 15 个）。"""
        cats = []

        # 1. universal_knowledge topic groups (top 10 by count)
        uk_topics = await self._db.fetch(
            "SELECT topic, count(*) as cnt FROM universal_knowledge WHERE status='active' GROUP BY topic ORDER BY cnt DESC LIMIT 10"
        )
        for r in uk_topics:
            cats.append({"type": "universal_knowledge", "name": f"通用知识-{r['topic']}", "query_field": "topic", "query_value": r["topic"]})

        # 2. knowledge_entities by entity_type
        ke_types = await self._db.fetch(
            "SELECT DISTINCT entity_type FROM knowledge_entities WHERE status='active' ORDER BY entity_type"
        )
        for r in ke_types:
            cats.append({"type": "knowledge_entities", "name": f"知识实体-{r['entity_type']}", "query_field": "entity_type", "query_value": r["entity_type"]})

        # 3. setting_items by category
        si_cats = await self._db.fetch(
            """SELECT sc.slug, sc.name FROM setting_categories sc
               JOIN setting_items si ON si.category_id = sc.id
               WHERE sc.workspace_id = (SELECT workspace_id FROM projects WHERE id=$1 LIMIT 1)
               GROUP BY sc.id, sc.slug, sc.name ORDER BY sc.name""",
            project_id,
        )
        for r in si_cats:
            cats.append({"type": "setting_items", "name": f"写作知识-{r['name']}", "query_field": "category_slug", "query_value": r["slug"]})

        # 4. project-level canon_rules by rule_type
        cr_types = await self._db.fetch(
            "SELECT DISTINCT rule_type FROM canon_rules WHERE project_id=$1 AND status='active' ORDER BY rule_type",
            project_id,
        )
        for r in cr_types:
            cats.append({"type": "canon_rules", "name": f"创作规则-{r['rule_type']}", "query_field": "rule_type", "query_value": r["rule_type"]})

        return cats

    async def _audit_category(self, project_id: str, cat: dict, mode: str | None = None) -> dict[str, Any]:
        """审计单个分类：获取已有知识 → 并行调用多模型 → 收集建议。

        mode: None=新增+优化, "add"=只新增, "optimize"=只优化
        """
        existing = await self._get_existing_knowledge(project_id, cat)
        if not existing:
            return {"proposals": [], "models_used": []}

        if mode == "add":
            mode_instruction = "只做新增分析"
            additions_required = "最多 8 条"
            updates_required = "0 条（本次不做优化）"
        elif mode == "optimize":
            mode_instruction = "只做优化分析"
            additions_required = "0 条（本次不做新增）"
            updates_required = "最多 5 条"
        else:
            mode_instruction = "同时做新增和优化分析"
            additions_required = "最多 5 条"
            updates_required = "最多 3 条"

        audit_prompt = f"""你正在审计知识库中的「{cat['name']}」分类。{mode_instruction}

【已有知识】
{existing}

【你的任务】
分析当前知识库，找出缺口和改进点。输出 JSON（只输出 JSON，不要其他文字）：

{{
  "additions": [
    {{"title": "建议新增标题", "content": "详细内容", "reason": "补充理由"}}
  ],
  "updates": [
    {{"existing": "现有条目", "suggested_content": "更新后内容", "reason": "更新理由"}}
  ]
}}

要求：
- additions {additions_required}
- updates {updates_required}
- 每条必须给出具体理由"""

        # Pick models for audit — use available analysis/review profiles
        model_keys = ["baidubce-deepseek-v4-flash", "baidubce-deepseek-v3.2", "baidubce-glm-5"]
        available = []
        for mk in model_keys:
            row = await self._db.fetchrow(
                "SELECT 1 FROM model_profiles WHERE project_id=$1 AND profile_key=$2 AND status='active'",
                project_id, mk,
            )
            if row:
                available.append(mk)

        if not available:
            return {"proposals": [], "models_used": [], "error": "no models available"}

        # Parallel calls
        import asyncio
        results = await asyncio.gather(
            *[self._call_model(project_id, mk, audit_prompt) for mk in available],
            return_exceptions=True,
        )

        # Parse and merge proposals
        all_additions: list[dict] = []
        for idx, r in enumerate(results):
            if isinstance(r, Exception):
                logger.warning("Model %s audit failed: %s", available[idx], r)
                continue
            try:
                data = self._parse_json(r.get("text", ""))
                if data:
                    for a in data.get("additions", []):
                        a["_source_model"] = available[idx]
                        all_additions.append(a)
                    for u in data.get("updates", []):
                        u["_source_model"] = available[idx]
                        u["_is_update"] = True
                        all_additions.append(u)
            except Exception as e:
                logger.warning("Parse failed for %s: %s", available[idx], e)

        # Deduplicate by title similarity across models → consensus detection
        proposals = self._merge_to_proposals(all_additions, cat, project_id)

        return {"proposals": proposals, "models_used": available}

    async def _get_existing_knowledge(self, project_id: str, cat: dict) -> str:
        """获取分类的现有知识，格式化为文本。"""
        lines = []
        t = cat["type"]

        if t == "universal_knowledge":
            rows = await self._db.fetch(
                "SELECT topic, content, summary FROM universal_knowledge WHERE topic=$1 AND status='active' LIMIT 50",
                cat["query_value"],
            )
            for r in rows:
                lines.append(f"- {r['topic']}: {r['summary'] or r['content'][:100]}")

        elif t == "knowledge_entities":
            rows = await self._db.fetch(
                "SELECT name, summary, content FROM knowledge_entities WHERE entity_type=$1 AND status='active' LIMIT 50",
                cat["query_value"],
            )
            for r in rows:
                lines.append(f"- {r['name']}: {r['summary'] or r['content'][:100]}")

        elif t == "setting_items":
            rows = await self._db.fetch(
                """SELECT si.core_summary, si.level FROM setting_items si
                   JOIN setting_categories sc ON si.category_id = sc.id
                   WHERE sc.slug=$1 AND si.workspace_id=(SELECT workspace_id FROM projects WHERE id=$2 LIMIT 1)
                   LIMIT 50""",
                cat["query_value"], project_id,
            )
            for r in rows:
                lines.append(f"- [{r['level']}] {r['core_summary'][:100]}")

        elif t == "canon_rules":
            rows = await self._db.fetch(
                "SELECT title, content FROM canon_rules WHERE project_id=$1 AND rule_type=$2 AND status='active' LIMIT 50",
                project_id, cat["query_value"],
            )
            for r in rows:
                lines.append(f"- {r['title']}: {r['content'][:100]}")

        return "\n".join(lines) if lines else "(空)"

    async def _call_model(self, project_id: str, profile_key: str, prompt: str) -> dict:
        """调用单个模型进行审计。"""
        msg = [{"role": "system", "content": "你是知识库审计专家，分析知识缺口并输出 JSON 格式的补充建议。"},
               {"role": "user", "content": prompt}]
        return await self._llm.chat_with_profile(project_id, profile_key, msg, temperature=0.3, max_tokens=4096)

    def _parse_json(self, text: str) -> dict | None:
        """从模型输出中提取 JSON。"""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            text = text.rsplit("\n", 1)[0] if text.endswith("```") else text
            if text.endswith("```"):
                text = text[:-3]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _merge_to_proposals(self, items: list[dict], cat: dict, project_id: str) -> list[dict]:
        """将多模型建议去重合并为进化提案。"""
        # Simple key: use title as dedup key
        seen = {}
        for item in items:
            key = item.get("title", item.get("existing", ""))
            if key in seen:
                seen[key]["_models"].append(item.get("_source_model", ""))
                seen[key]["_model_count"] = len(seen[key]["_models"])
            else:
                item["_models"] = [item.get("_source_model", "")]
                item["_model_count"] = 1
                seen[key] = item

        proposals = []
        for key, item in seen.items():
            is_update = item.get("_is_update", False)
            proposals.append({
                "title": f"{'更新' if is_update else '新增'} {cat['name']}: {key}",
                "description": item.get("reason", item.get("content", "")),
                "proposal_type": "update" if is_update else "create",
                "target_entity_type": "setting_item",
                "proposed_content": {
                    "category": cat.get("query_value", "general"),
                    "title": key,
                    "core_summary": item.get("content", item.get("suggested_content", "")),
                },
                "evolution_reason": f"知识审计: {cat['name']} — {item.get('reason', '')}",
                "evidence": json.dumps({"model_count": item["_model_count"], "models": item["_models"]}),
                "_model_count": item["_model_count"],
            })
        return proposals

    async def save_proposals(self, project_id: str, proposals: list[dict]) -> dict[str, int]:
        """将审计提案写入 system_evolution_proposals。"""
        saved = 0
        for p in proposals:
            model_count = p.pop("_model_count", 1)
            status = "pending_review"  # 等待辩论委员会裁决
            try:
                await self._db.execute(
                    """INSERT INTO system_evolution_proposals
                       (title, description, proposal_type, target_entity_type, proposed_content,
                        evolution_reason, source_project_id, ai_submitter, evidence, status)
                       VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9::jsonb,$10)""",
                    p["title"], p["description"], p["proposal_type"],
                    p["target_entity_type"], json.dumps(p["proposed_content"]),
                    p["evolution_reason"], project_id, f"audit_{p['target_entity_type']}",
                    json.dumps(p.get("evidence", {})), status,
                )
                saved += 1
            except Exception as e:
                logger.warning("Failed to save proposal: %s", e)
        return {"saved": saved, "total": len(proposals)}