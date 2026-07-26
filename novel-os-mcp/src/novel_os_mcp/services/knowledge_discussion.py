"""Knowledge Discussion Service — 多模型讨论共识引擎
用于 AI 模型之间多轮讨论、审阅、达成共识后产出最终结果。
不暴露为 MCP 工具，仅通过直接脚本调用。
"""
import asyncio
import json
import logging
from typing import Any

from ..db import Database

logger = logging.getLogger("novel_os_mcp.services.knowledge_discussion")

# 可用讨论模型池（5 个）
MODEL_POOL = [
    "baidubce-deepseek-v4-flash",
    "baidubce-deepseek-v3.2",
    "baidubce-glm-5",
    "baidubce-deepseek-v4-pro",
    "baidubce-glm-5.1",
]

# 轮换方案（每轮尽量换 2/3 模型）
ROTATION = [
    ["baidubce-deepseek-v4-flash", "baidubce-deepseek-v3.2", "baidubce-glm-5"],
    ["baidubce-deepseek-v4-pro", "baidubce-glm-5.1", "baidubce-deepseek-v4-flash"],
    ["baidubce-deepseek-v3.2", "baidubce-glm-5", "baidubce-deepseek-v4-pro"],
    ["baidubce-glm-5.1", "baidubce-deepseek-v4-flash", "baidubce-deepseek-v3.2"],
]


class KnowledgeDiscussionService:
    """知识讨论服务 — 多模型多轮讨论共识"""

    def __init__(self, db: Database, llm_client=None):
        self._db = db
        self._llm = llm_client

    async def discuss(
        self,
        project_id: str,
        title: str,
        round1_prompt: str,
        review_prompt: str,
        summary_prompt: str,
        max_rounds: int = 5,
    ) -> dict[str, Any]:
        """执行完整的多轮讨论流程。

        Args:
            project_id: 项目 UUID
            title: 讨论标题（用于标识）
            round1_prompt: 第一轮提议 prompt
            review_prompt: 审阅 prompt（含 {proposals} 占位符）
            summary_prompt: 总结 prompt（含 {proposals} 占位符）
            max_rounds: 最大轮数

        Returns:
            {proposals, summary, rounds, consensus_reached}
        """
        # Round 1: 3 模型独立提议
        round_idx = 0
        models_r1 = ROTATION[round_idx % len(ROTATION)]
        proposals_list = []  # List of model proposals (list of strings)

        for i, mk in enumerate(models_r1):
            try:
                r = await self._call_model(project_id, mk, round1_prompt)
                proposals_list.append({"model": mk, "text": r.get("text", "")})
            except Exception as e:
                logger.warning("Round 1 model %s failed: %s", mk, e)
            await asyncio.sleep(0.8)

        if not proposals_list:
            return {"proposals": [], "summary": "", "rounds": 0, "consensus_reached": False}

        # Merge proposals
        merged = self._merge_proposals([p["text"] for p in proposals_list])
        all_rounds = [{"round": 1, "type": "propose", "models": models_r1, "results": proposals_list}]
        consensus_reached = False

        # Rounds 2+: review
        for round_idx in range(1, max_rounds):
            review_models = ROTATION[round_idx % len(ROTATION)]
            review_input = merged
            objections = []

            for i, mk in enumerate(review_models):
                prompt = review_prompt.replace("{proposals}", review_input)
                try:
                    r = await self._call_model(project_id, mk, prompt)
                    text = r.get("text", "")
                    if self._has_objections(text):
                        objections.append({"model": mk, "text": text})
                except Exception as e:
                    logger.warning("Review round %d model %s failed: %s", round_idx + 1, mk, e)
                await asyncio.sleep(0.8)  # Rate limit

            all_rounds.append({
                "round": round_idx + 1,
                "type": "review",
                "models": review_models,
                "objections": objections,
            })

            if not objections:
                consensus_reached = True
                break

            # Merge objections into proposals for next round
            merged = self._merge_proposals(
                [merged] + [o["text"] for o in objections]
            )

        # Final: summary
        summary_model = ROTATION[0][0]
        summary_input = merged
        prompt = summary_prompt.replace("{proposals}", summary_input)
        try:
            r = await self._call_model(project_id, summary_model, prompt)
            summary = r.get("text", "")
        except Exception as e:
            logger.warning("Summary model failed: %s", e)
            summary = merged

        return {
            "title": title,
            "summary": summary,
            "rounds": len(all_rounds),
            "consensus_reached": consensus_reached,
            "history": all_rounds,
        }

    def _merge_proposals(self, texts: list[str]) -> str:
        """合并多个模型的输出为一份文档。"""
        # Simply join with separators
        parts = []
        for i, t in enumerate(texts):
            parts.append(f"--- 来源 {i + 1} ---\n{t.strip()}")
        return "\n\n".join(parts)

    def _has_objections(self, text: str) -> bool:
        """判断模型输出是否包含异议。"""
        lower = text.lower()
        # 如果模型说"无异议""同意""没有补充"等，视为无异议
        no_objection = any(kw in lower for kw in [
            "无异议", "没有异议", "同意", "没有补充", "无补充",
            "no objection", "i agree", "no issues",
            "没有意见", "全部同意", "认可", "完全同意",
        ])
        return not no_objection

    async def _call_model(self, project_id: str, profile_key: str, prompt: str) -> dict:
        """调用单个模型。"""
        msg = [
            {"role": "system", "content": "你是小说创作知识库专家。输出要结构化、清晰、有实际价值。"},
            {"role": "user", "content": prompt},
        ]
        return await self._llm.chat_with_profile(project_id, profile_key, msg, temperature=0.3, max_tokens=4096)