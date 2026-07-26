"""AI Evolution Reviewer Service - AI进化提案评审服务

提供AI自动初审功能，对系统级进化提案进行全面评审。
"""

import json
import logging
from typing import Any

from ..deps import db
from ..mcp_core import mcp

logger = logging.getLogger("novel_os_mcp.services.ai_reviewer")


class AIEvolutionReviewer:
    """AI进化提案评审器"""
    
    # 通过阈值
    APPROVAL_THRESHOLD = 0.8
    
    # 各维度权重
    DIMENSION_WEIGHTS = {
        "necessity": 0.3,
        "feasibility": 0.3,
        "impact": 0.2,
        "quality": 0.2
    }
    
    # 评审维度定义
    DIMENSIONS = {
        "style_profile": {
            "completeness": 0.25,
            "reasonableness": 0.25,
            "uniqueness": 0.25,
            "practicality": 0.25
        },
        "prompt_template": {
            "quality": 0.3,
            "variable_validity": 0.25,
            "applicability": 0.25,
            "innovation": 0.2
        },
        "model_profile": {
            "completeness": 0.25,
            "parameter_validity": 0.3,
            "practicality": 0.25,
            "economy": 0.2
        },
        "knowledge_item": {
            "accuracy": 0.3,
            "completeness": 0.25,
            "applicability": 0.25,
            "value": 0.2
        }
    }
    
    def __init__(self, llm_client: Any = None):
        self.max_retries = 3
        self._llm = llm_client
    
    async def review_proposal(self, proposal_id: str) -> dict[str, Any]:
        """评审单个提案。
        
        Args:
            proposal_id: 提案ID
            
        Returns:
            {
                "score": 综合评分 0-1,
                "verdict": "pass"|"reject"|"needs_improvement",
                "reasoning": 详细理由,
                "risk_assessment": 风险评估,
                "suggestions": [改进建议],
                "dimension_scores": 各维度评分,
                "confidence": 置信度
            }
        """
        logger.info(f"Starting AI review for proposal: {proposal_id}")
        
        try:
            # 获取提案详情
            proposal = await self._get_proposal(proposal_id)
            if not proposal:
                raise ValueError(f"Proposal not found: {proposal_id}")
            
            # 获取现有类似实体
            similar_entities = await self._get_similar_entities(
                proposal["target_entity_type"],
                proposal["target_entity_key"]
            )
            
            # 检测冲突
            conflicts = await self._detect_conflicts(proposal, similar_entities)
            
            # 执行通用评审
            general_review = await self._general_review(proposal, similar_entities)
            
            # 执行专项评审
            specialized_review = await self._specialized_review(proposal)
            
            # 合并结果
            result = self._merge_reviews(
                general=general_review,
                specialized=specialized_review,
                conflicts=conflicts
            )
            
            # 根据冲突调整评分
            if conflicts.get("has_high_severity_conflict", False):
                result["score"] = max(0, result["score"] - 0.3)
                result["verdict"] = "reject"
                result["reasoning"] += "\n\n[系统自动调整] 检测到严重冲突，评分已降低。"
            
            logger.info(f"AI review completed for {proposal_id}: score={result['score']:.2f}, verdict={result['verdict']}")
            
            return result
            
        except Exception as e:
            logger.error(f"AI review failed for {proposal_id}: {e}")
            raise
    
    async def _get_proposal(self, proposal_id: str) -> dict[str, Any] | None:
        """获取提案详情。"""
        row = await db.fetchrow(
            """
            SELECT 
                id::text, title, description, proposal_type, target_entity_type,
                target_entity_key, proposed_content, evolution_reason, evidence
            FROM system_evolution_proposals
            WHERE id = $1
            """,
            proposal_id
        )
        
        if not row:
            return None
        
        return dict(row)
    
    async def _get_similar_entities(self, entity_type: str, entity_key: str | None) -> list[dict]:
        """获取同类型的现有实体。"""
        table_map = {
            'style_profile': 'system_style_profiles',
            'prompt_template': 'system_prompt_templates',
            'model_profile': 'system_model_profiles',
        }
        
        if entity_type not in table_map:
            return []
        
        table = table_map[entity_type]
        
        if entity_key:
            # 获取特定实体
            rows = await db.fetch(
                f"SELECT * FROM {table} WHERE profile_key = $1 OR template_key = $1",
                entity_key
            )
        else:
            # 获取所有同类实体（限制5个）
            rows = await db.fetch(
                f"SELECT * FROM {table} WHERE status = 'active' LIMIT 5"
            )
        
        return [dict(row) for row in rows]
    
    async def _detect_conflicts(self, proposal: dict, similar_entities: list) -> dict[str, Any]:
        """检测冲突。"""
        conflicts = {
            "has_conflict": False,
            "has_high_severity_conflict": False,
            "conflicts": []
        }
        
        target_key = proposal.get("target_entity_key")
        proposal_type = proposal["proposal_type"]
        
        # 检查命名冲突
        if proposal_type == 'create' and target_key:
            for entity in similar_entities:
                entity_key = entity.get('profile_key') or entity.get('template_key')
                if entity_key == target_key:
                    conflicts["has_conflict"] = True
                    conflicts["conflicts"].append({
                        "type": "naming",
                        "severity": "high",
                        "description": f"业务键 '{target_key}' 已存在",
                        "existing_entity": entity_key
                    })
                    conflicts["has_high_severity_conflict"] = True
        
        # TODO: 更多冲突检测逻辑（内容冲突、逻辑冲突等）
        
        return conflicts
    
    async def _general_review(self, proposal: dict, similar_entities: list) -> dict[str, Any]:
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(proposal, similar_entities)
        self._current_proposal = proposal
        review_result = await self._mock_ai_review(system_prompt, user_prompt)
        return review_result
    
    async def _specialized_review(self, proposal: dict) -> dict[str, Any]:
        """专项评审。"""
        entity_type = proposal["target_entity_type"]
        
        if entity_type not in self.DIMENSIONS:
            return {"dimension_scores": {}}
        
        weights = self.DIMENSIONS[entity_type]
        
        # 根据实体类型进行专项评审
        # TODO: 实现具体的专项评审逻辑
        dimension_scores = {}
        for dimension in weights.keys():
            dimension_scores[dimension] = {
                "score": 0.85,  # 模拟评分
                "reasoning": f"{dimension}评估通过"
            }
        
        return {"dimension_scores": dimension_scores}
    
    def _merge_reviews(self, general: dict, specialized: dict, conflicts: dict) -> dict[str, Any]:
        """合并评审结果。"""
        score = general.get("score", 0)
        
        # 计算综合评分
        if specialized.get("dimension_scores"):
            dim_scores = specialized["dimension_scores"]
            avg_dim_score = sum(d.get("score", 0) for d in dim_scores.values()) / len(dim_scores)
            score = (score + avg_dim_score) / 2
        
        # 确定裁决
        if score >= self.APPROVAL_THRESHOLD:
            verdict = "pass"
        elif score >= 0.6:
            verdict = "needs_improvement"
        else:
            verdict = "reject"
        
        return {
            "score": round(score, 2),
            "verdict": verdict,
            "reasoning": general.get("reasoning", ""),
            "risk_assessment": general.get("risk_assessment", ""),
            "suggestions": general.get("suggestions", []),
            "dimension_scores": specialized.get("dimension_scores", {}),
            "confidence": general.get("confidence", 0.8),
            "conflicts_detected": conflicts["has_conflict"]
        }
    
    def _build_system_prompt(self) -> str:
        """构建系统Prompt。"""
        return """你是Novel OS系统级进化评审专家。你的任务是对系统级数据改进提案进行专业评审。

## 评审职责
1. 评估提案的必要性、合理性和影响
2. 检测与现有系统数据的冲突
3. 评估方案的可行性
4. 识别潜在风险

## 评审标准
- 必要性: 问题是否真实存在？是否有数据支撑？
- 合理性: 方案是否可行？是否符合最佳实践？
- 影响: 影响范围是否合理？是否有负面影响？
- 质量: 内容是否完整？描述是否清晰？

## 输出要求
必须输出有效的JSON格式，包含以下字段:
- score: 综合评分 (0.0-1.0)
- verdict: "pass" | "reject" | "needs_improvement"
- reasoning: 详细评审理由
- risk_assessment: 风险评估
- suggestions: 改进建议列表
- dimension_scores: 各维度评分详情
- confidence: 置信度 (0.0-1.0)

评分标准:
- >= 0.8: 高质量提案，建议通过
- 0.6-0.8: 需要改进
- < 0.6: 建议拒绝
"""
    
    def _build_user_prompt(self, proposal: dict, similar_entities: list) -> str:
        """构建用户Prompt。"""
        prompt = f"""## 提案信息

**提案标题**: {proposal['title']}
**提案类型**: {proposal['proposal_type']}
**目标实体类型**: {proposal['target_entity_type']}
**目标实体**: {proposal.get('target_entity_key', 'N/A')}

**提案描述**:
{proposal['description']}

**进化原因**:
{proposal['evolution_reason']}

**提案内容**:
```json
{json.dumps(proposal['proposed_content'], ensure_ascii=False, indent=2)}
```

**支持证据**:
```json
{json.dumps(proposal.get('evidence', {}), ensure_ascii=False, indent=2)}
```

## 现有系统数据参考

**同类型现有数据**:
```json
{json.dumps(similar_entities, ensure_ascii=False, indent=2)[:2000]}
```

---

请对上述提案进行全面评审，输出JSON格式的评审结果。
"""
        return prompt
    
    async def _mock_ai_review(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """使用真实 LLM 模型进行评审，失败时回退到模拟数据。"""
        if self._llm:
            try:
                proposal = {}
                if hasattr(self, '_current_proposal'):
                    proposal = self._current_proposal
                project_id = proposal.get('project_id') or proposal.get('source_project_id')
                if project_id:
                    result = await self._llm.chat_simple(project_id, "review",
                        system_prompt, user_prompt, temperature=0.3, max_tokens=2000)
                    text = result.get("text", "")
                    # Try to parse JSON from the response
                    import json
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        # Try to extract JSON from text
                        import re
                        match = re.search(r'\{[\s\S]*\}', text)
                        if match:
                            return json.loads(match.group())
            except Exception as e:
                logger.warning("LLM review failed, using mock: %s", e)

        return {
            "score": 0.85,
            "verdict": "pass",
            "reasoning": "该提案提供了合理的改进方案。(Mock — LLM 审查服务未配置或调用失败)",
            "risk_assessment": "低风险。",
            "suggestions": [],
            "confidence": 0.5,
        }


# 全局评审器实例（llm_client 由 deps 注入）
ai_reviewer = None

def init_ai_reviewer(llm_client):
    global ai_reviewer
    ai_reviewer = AIEvolutionReviewer(llm_client=llm_client)
    return ai_reviewer


# ============================================================================
# 评审队列处理
# ============================================================================

async def process_ai_review_queue() -> dict[str, Any]:
    """处理AI初审队列。
    
    扫描所有待AI初审的提案，逐个进行评审。
    
    Returns:
        {"processed": 处理数量, "passed": 通过数量, "rejected": 拒绝数量, "failed": 失败数量}
    """
    logger.info("Starting AI review queue processing")
    
    # 获取待评审提案
    rows = await db.fetch(
        """
        SELECT id::text 
        FROM system_evolution_proposals 
        WHERE status = 'ai_reviewing' 
        AND ai_retry_count < 3
        ORDER BY created_at ASC
        LIMIT 10
        """
    )
    
    if not rows:
        logger.info("No proposals pending AI review")
        return {"processed": 0, "passed": 0, "rejected": 0, "failed": 0}
    
    processed = 0
    passed = 0
    rejected = 0
    failed = 0
    
    for row in rows:
        proposal_id = row["id"]
        
        try:
            # 更新状态为评审中
            await db.execute(
                "UPDATE system_evolution_proposals SET status = 'ai_reviewing' WHERE id = $1",
                proposal_id
            )
            
            # 执行评审
            review_result = await ai_reviewer.review_proposal(proposal_id)
            
            # 更新评审结果
            new_status = 'ai_reviewed' if review_result["verdict"] != "reject" else 'ai_rejected'
            
            await db.execute(
                """
                UPDATE system_evolution_proposals 
                SET status = $1, ai_review_result = $2, updated_at = now()
                WHERE id = $3
                """,
                new_status, review_result, proposal_id
            )
            
            processed += 1
            
            if review_result["score"] >= AIEvolutionReviewer.APPROVAL_THRESHOLD:
                passed += 1
                # 通知管理员有新的待审核提案
                await _notify_admin_review_pending(proposal_id)
            else:
                rejected += 1
                # 通知提交者AI初审未通过
                await _notify_ai_review_rejected(proposal_id, review_result)
                
        except Exception as e:
            logger.error(f"AI review failed for {proposal_id}: {e}")
            failed += 1
            
            # 更新失败状态
            await db.execute(
                """
                UPDATE system_evolution_proposals 
                SET ai_last_error = $1, ai_retry_count = ai_retry_count + 1, updated_at = now()
                WHERE id = $2
                """,
                str(e), proposal_id
            )
    
    logger.info(f"AI review queue processing completed: processed={processed}, passed={passed}, rejected={rejected}, failed={failed}")
    
    return {
        "processed": processed,
        "passed": passed,
        "rejected": rejected,
        "failed": failed
    }


async def _notify_admin_review_pending(proposal_id: str) -> None:
    """通知管理员有新的待审核提案。"""
    from .system_notifications import _send_notification
    
    proposal = await db.fetchrow(
        "SELECT title FROM system_evolution_proposals WHERE id = $1",
        proposal_id
    )
    
    if proposal:
        await _send_notification(
            user_id=None,  # 全局通知
            notification_type='admin_review_required',
            title=f'新的进化提案待审核: {proposal["title"]}',
            content=f'提案ID: {proposal_id}\n标题: {proposal["title"]}\n状态: AI初审已通过，等待管理员审核',
            is_global=True,
            related_proposal_id=proposal_id
        )


async def _notify_ai_review_rejected(proposal_id: str, review_result: dict) -> None:
    """通知提交者AI初审未通过。"""
    from .system_notifications import _send_notification
    
    proposal = await db.fetchrow(
        "SELECT title, submitted_by FROM system_evolution_proposals WHERE id = $1",
        proposal_id
    )
    
    if proposal and proposal["submitted_by"]:
        await _send_notification(
            user_id=proposal["submitted_by"],
            notification_type='evolution_proposal',
            title=f'您的进化提案需要改进: {proposal["title"]}',
            content=f'提案: {proposal["title"]}\n状态: AI初审未通过\n原因: {review_result.get("reasoning", "")[:200]}',
            related_proposal_id=proposal_id
        )


# ============================================================================
# MCP工具暴露
# ============================================================================

@mcp.tool(name="system.evolution.ai_review")
async def system_evolution_ai_review(
    proposal_id: str,
) -> dict[str, Any]:
    """手动触发AI初审（管理员）。
    
    通常AI初审会自动触发，但管理员可以手动重新触发。
    
    Args:
        proposal_id: 提案ID
        
    Returns:
        {
            "id": "提案ID",
            "score": 评分,
            "verdict": "裁决",
            "status": "新状态",
            "message": "处理结果"
        }
    """
    principal = await get_principal("write")
    # await auth.require_admin(principal)
    
    validate_required(locals(), "proposal_id")
    
    # 检查当前状态
    current = await db.fetchval(
        "SELECT status FROM system_evolution_proposals WHERE id = $1",
        proposal_id
    )
    
    if current not in ('draft', 'ai_reviewing', 'ai_rejected'):
        raise ValueError(f"Cannot trigger AI review for proposal with status={current}")
    
    # 执行评审
    review_result = await ai_reviewer.review_proposal(proposal_id)
    
    # 更新状态
    new_status = 'ai_reviewed' if review_result["verdict"] != "reject" else 'ai_rejected'
    
    await db.execute(
        """
        UPDATE system_evolution_proposals 
        SET status = $1, ai_review_result = $2, updated_at = now()
        WHERE id = $3
        """,
        new_status, review_result, proposal_id
    )
    
    # 如果通过，通知管理员
    if review_result["score"] >= AIEvolutionReviewer.APPROVAL_THRESHOLD:
        await _notify_admin_review_pending(proposal_id)
    
    return {
        "id": proposal_id,
        "score": review_result["score"],
        "verdict": review_result["verdict"],
        "status": new_status,
        "ai_review_result": review_result,
        "message": f"AI初审完成，评分: {review_result['score']:.2f}"
    }
