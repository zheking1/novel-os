"""Knowledge Council Service — 多模型知识辩论委员会
Takes pending_review proposals, dispatches to multiple review models,
collects votes, applies changes if consensus reached.
"""
import json
import logging
from typing import Any

from ..db import Database

logger = logging.getLogger("novel_os_mcp.services.knowledge_council")


class KnowledgeCouncilService:
    """知识辩论委员会"""

    def __init__(self, db: Database, llm_client=None):
        self._db = db
        self._llm = llm_client

    async def debate_all(self, project_id: str) -> dict[str, Any]:
        """对所有 pending_review 提案发起辩论。"""
        proposals = await self._db.fetch(
            "SELECT id FROM system_evolution_proposals WHERE source_project_id=$1 AND status='pending_review' ORDER BY created_at",
            project_id,
        )
        results = {"total": len(proposals), "approved": 0, "rejected": 0, "errors": 0}
        for row in proposals:
            try:
                r = await self._debate_single(project_id, row["id"])
                if r.get("approved"):
                    results["approved"] += 1
                else:
                    results["rejected"] += 1
            except Exception as e:
                logger.warning("Debate failed for proposal %s: %s", row["id"], e)
                results["errors"] += 1
        return results

    async def _debate_single(self, project_id: str, proposal_id: str) -> dict[str, Any]:
        """对单条提案发起辩论。"""
        prop = await self._db.fetchrow(
            """SELECT title, description, proposed_content, evolution_reason
               FROM system_evolution_proposals WHERE id=$1""",
            proposal_id,
        )
        if not prop:
            return {"approved": False, "error": "not found"}

        content = prop["proposed_content"]
        if isinstance(content, str):
            content = json.loads(content)

        debate_prompt = f"""请评估以下知识库进化提案是否应该采纳。

【提案标题】
{prop['title']}

【提案内容】
{json.dumps(content, ensure_ascii=False, indent=2)}

【提案理由】
{prop['evolution_reason']}

【评估标准】
1. 是否具有实际价值？
2. 是否与已有知识冲突？
3. 表述是否准确完整？

输出 JSON:
{{"vote": "approve", "confidence": 0.8, "reason": "..."}}
或
{{"vote": "reject", "confidence": 0.6, "reason": "..."}}"""

        # Use review models for debate
        model_keys = ["baidubce-deepseek-v4-flash", "baidubce-deepseek-v3.2", "baidubce-glm-5"]
        available = []
        for mk in model_keys:
            row = await self._db.fetchrow(
                "SELECT 1 FROM model_profiles WHERE profile_key=$1 AND status='active'",
                mk,
            )
            if row:
                available.append(mk)

        if not available:
            return {"approved": False, "error": "no models available"}

        import asyncio
        results = []
        for mk in available:
            try:
                r = await self._call_model(project_id, mk, debate_prompt)
                results.append(r)
            except Exception as e:
                logger.warning("Model %s debate failed: %s", mk, e)
                results.append(e)
            await asyncio.sleep(1.5)  # Rate limit: 1.5s between calls to same API

        votes = []
        for idx, r in enumerate(results):
            if isinstance(r, Exception):
                logger.warning("Model %s debate failed: %s", available[idx], r)
                continue
            vote_data = self._parse_json(r.get("text", ""))
            if vote_data:
                vote_data["model"] = available[idx]
                votes.append(vote_data)

        total_votes = len(votes)
        approved_votes = sum(1 for v in votes if v.get("vote") == "approve")
        rejected_votes = sum(1 for v in votes if v.get("vote") == "reject")

        # Consensus: ≥2/3 approve (at least 2 if 3 voters)
        if total_votes >= 3:
            consensus = approved_votes >= 2
        elif total_votes == 2:
            consensus = approved_votes == 2
        else:
            consensus = approved_votes >= 1

        # Save vote results
        council_result = {
            "council_votes": votes,
            "consensus": consensus,
            "approved_count": approved_votes,
            "rejected_count": rejected_votes,
            "total_votes": total_votes,
        }

        if consensus:
            new_status = "applied"
            await self._apply_proposal(proposal_id)
        else:
            new_status = "rejected"

        await self._db.execute(
            """UPDATE system_evolution_proposals
               SET status=$1, admin_review_result=$2::jsonb, updated_at=now()
               WHERE id=$3""",
            new_status, json.dumps(council_result), proposal_id,
        )

        return {"approved": consensus, "votes": votes}

    async def _call_model(self, project_id: str, profile_key: str, prompt: str) -> dict:
        msg = [{"role": "system", "content": "你是知识库进化审核专家，评估提案是否应该采纳。输出 JSON 格式投票结果。"},
               {"role": "user", "content": prompt}]
        return await self._llm.chat_with_profile(project_id, profile_key, msg, temperature=0.3, max_tokens=2048)

    def _parse_json(self, text: str) -> dict | None:
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

    async def _apply_proposal(self, proposal_id: str) -> None:
        """应用已通过的提案到对应系统表。"""
        prop = await self._db.fetchrow(
            """SELECT target_entity_type, proposed_content, target_entity_key
               FROM system_evolution_proposals WHERE id=$1""",
            proposal_id,
        )
        if not prop:
            return
        etype = prop["target_entity_type"]
        content = prop["proposed_content"]
        if isinstance(content, str):
            content = json.loads(content)

        try:
            if etype == "setting_item":
                cat_slug = content.get("category", "general")
                cat = await self._db.fetchrow(
                    "SELECT id FROM setting_categories WHERE slug=$1 AND workspace_id=(SELECT id FROM workspaces LIMIT 1) LIMIT 1",
                    cat_slug,
                )
                if cat:
                    await self._db.execute(
                        """INSERT INTO setting_items (workspace_id, category_id, item_code, core_summary, level, ai_instruction, is_global)
                           VALUES ((SELECT id FROM workspaces LIMIT 1), $1, $2, $3, 'knowledge', $4, true)
                           ON CONFLICT DO NOTHING""",
                        cat["id"], f"council_{proposal_id[:8]}",
                        content.get("core_summary", content.get("title", "")),
                        content.get("core_summary", ""),
                    )
            elif etype == "knowledge_item":
                ename = content.get("name", "")
                etype_k = content.get("entity_type", "character")
                sug = content.get("suggested_update", content.get("core_summary", ""))
                if ename and sug:
                    await self._db.execute(
                        """INSERT INTO knowledge_entities (entity_type, name, content, summary, source)
                           VALUES ($1, $2, $3, $4, 'council_evolution')
                           ON CONFLICT (name, entity_type) DO UPDATE
                           SET content = CASE WHEN knowledge_entities.source = 'council_evolution' THEN EXCLUDED.content ELSE knowledge_entities.content END""",
                        etype_k, ename, sug, sug[:200],
                    )
        except Exception as e:
            logger.warning("Apply proposal %s failed: %s", proposal_id, e)