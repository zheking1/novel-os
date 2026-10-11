import json
import logging
import os
from datetime import datetime
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value
from .memory import MemoryService
from .rules import RulesService
from .plot import PlotService

logger = logging.getLogger("novel_os_mcp.services.context")


class ContextService:
    def __init__(
        self,
        db: Database,
        memory: MemoryService,
        rules: RulesService,
        plot: PlotService,
        embedding_service: Any = None,
        rerank_service: Any = None,
        character_arc_service: Any = None,
        causality_service: Any = None,
        pacing_service: Any = None,
        style_fingerprint_service: Any = None,
    ):
        self._db = db
        self._memory = memory
        self._rules = rules
        self._plot = plot
        self._embedding = embedding_service
        self._rerank = rerank_service
        self._character_arc = character_arc_service
        self._causality = causality_service
        self._pacing = pacing_service
        self._style_fingerprint = style_fingerprint_service

    # ===== 动态上下文预算（roadmap 阶段 2 / D-06）=====
    # 见 docs/07-planning/dynamic-context-budget.md
    # 说明：旧逻辑把 total_tokens 按固定百分比切分，且不感知模型上下文窗口大小，
    #       128K 模型会浪费绝大部分空间，4K 模型则每个 section 都被过度压缩。

    # 分配给上下文的总比例（其余留给模型输出）
    CONTEXT_USABLE_RATIO = 0.6

    # section -> (优先级, 保底 token, 上下文窗口占比上限)
    # 优先级：0=必须 / 1=重要 / 2=增强 / 3=可选
    _CONTEXT_SECTION_SPECS: dict[str, tuple[int, int, float]] = {
        # P0 —— 没有就会写崩的
        "active_rules": (0, 400, 0.15),
        "current_state": (0, 600, 0.20),
        "chapter_plan": (0, 200, 0.05),
        # P1 —— 重要
        "open_foreshadowing": (1, 300, 0.08),
        "knowledge_base": (1, 250, 0.06),
        "universal_knowledge": (1, 250, 0.06),
        "project_knowledge": (1, 250, 0.06),
        "canon_documents": (1, 250, 0.06),
        # P2 —— 增强
        "recent_summaries": (2, 300, 0.06),
        "entity_relationships": (2, 200, 0.04),
        "character_arcs": (2, 200, 0.04),
        "pacing_guidance": (2, 150, 0.03),
        "style_guidance": (2, 150, 0.03),
        # P3 —— 可选，空间紧张时最先被跳过
        "relevant_memory": (3, 0, 0.03),
        "causal_chains": (3, 0, 0.03),
        "compressed_context": (3, 0, 0.02),
    }

    # 已知模型的上下文窗口，用于 model_profiles 未配置时兜底
    _KNOWN_CONTEXT_WINDOWS: dict[str, int] = {
        "gpt-4o-mini": 128_000,
        "gpt-4o": 128_000,
        "gpt-4.1": 1_000_000,
        "deepseek-v3": 64_000,
        "deepseek-r1": 128_000,
        "glm-4": 128_000,
        "claude-3.5": 200_000,
    }

    # 节奏调整：各 pacing_type 在基础占比上的增量（新旧两条分配路径共用）
    PACING_ADJUSTMENTS: dict[str, dict[str, float]] = {
        "climax": {
            "current_state": +0.04,
            "open_foreshadowing": +0.03,
            "entity_relationships": +0.02,
            "compressed_context": -0.02,
            "recent_summaries": -0.04,
            "relevant_memory": -0.02,
            "canon_documents": -0.01,
        },
        "climax_buildup": {
            "current_state": +0.02,
            "open_foreshadowing": +0.03,
            "entity_relationships": +0.02,
            "chapter_plan": +0.02,
            "compressed_context": -0.02,
            "recent_summaries": -0.04,
            "relevant_memory": -0.02,
            "canon_documents": -0.01,
        },
        "breather": {
            "current_state": -0.06,
            "relevant_memory": +0.04,
            "knowledge_base": +0.02,
            "canon_documents": +0.03,
        },
        "buildup": {
            "open_foreshadowing": +0.03,
            "chapter_plan": +0.02,
            "canon_documents": +0.02,
            "compressed_context": -0.02,
            "recent_summaries": -0.02,
            "relevant_memory": -0.02,
        },
        "resolution": {
            "compressed_context": +0.04,
            "open_foreshadowing": -0.04,
            "entity_relationships": -0.02,
        },
        "transition": {
            "recent_summaries": +0.03,
            "relevant_memory": +0.03,
            "canon_documents": +0.02,
            "compressed_context": -0.03,
            "current_state": -0.03,
            "entity_relationships": -0.02,
        },
    }

    @staticmethod
    def _section(name: str, content: Any, source_count: int = 0) -> dict[str, Any]:
        text = content if isinstance(content, str) else json_dumps(ContextService._json_safe(content))
        # Accurate token estimation for mixed Chinese/English
        chinese_chars = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
        ascii_words = len(text.split()) - chinese_chars
        tokens = int(chinese_chars * 1.5 + max(0, ascii_words) * 1.3) + 4
        return {
            "name": name,
            "content": text,
            "tokens_estimated": max(1, tokens),
            "source_count": source_count,
        }

    @staticmethod
    def _json_safe(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {key: ContextService._json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [ContextService._json_safe(item) for item in value]
        if isinstance(value, tuple):
            return [ContextService._json_safe(item) for item in value]
        return value

    @staticmethod
    def _normalize_context_pack(pack: dict[str, Any] | None) -> dict[str, Any] | None:
        if pack is None:
            return None
        normalized = dict(pack)
        normalized["budget"] = ensure_json_value(normalized.get("budget") or {})
        normalized["sections"] = ensure_json_value(normalized.get("sections") or [])
        normalized["retrieval_audit"] = ensure_json_value(normalized.get("retrieval_audit") or [])
        normalized["warnings"] = ensure_json_value(normalized.get("warnings") or [])
        return normalized

    @staticmethod
    def _normalize_section_content(section: dict[str, Any]) -> Any:
        return ensure_json_value(section.get("content"))

    async def _resolve_volume_no(self, project_id: str, chapter_no: int, volume_no: int | None) -> int | None:
        if volume_no is not None:
            return volume_no
        row = await self._db.fetchrow(
            "SELECT volume_no FROM chapters WHERE project_id = $1 AND chapter_no = $2",
            project_id,
            chapter_no,
        )
        return row["volume_no"] if row else None

    async def _resolve_pacing_type(self, project_id: str, chapter_no: int) -> str:
        """Look up pacing_type from chapter_emotions table."""
        row = await self._db.fetchrow(
            "SELECT pacing_type FROM chapter_emotions WHERE project_id = $1 AND chapter_no = $2",
            project_id,
            chapter_no,
        )
        return row["pacing_type"] if row else "normal"

    @staticmethod
    def _compute_section_budgets(pacing_type: str, total_tokens: int) -> dict[str, int]:
        """Compute per-section token budgets adjusted for chapter pacing type."""
        DEFAULT = {
            "active_rules": 0.12,
            "current_state": 0.14,
            "knowledge_base": 0.06,
            "universal_knowledge": 0.08,
            "project_knowledge": 0.08,
            "canon_documents": 0.08,
            "entity_relationships": 0.05,
            "open_foreshadowing": 0.07,
            "recent_summaries": 0.08,
            "chapter_plan": 0.04,
            "relevant_memory": 0.04,
            "compressed_context": 0.02,
            "character_arcs": 0.05,
            "causal_chains": 0.04,
            "style_guidance": 0.03,
            "pacing_guidance": 0.04,
        }

        # Pacing-specific adjustments (additive to base percentages)
        # 节奏增量表已提取为类常量 PACING_ADJUSTMENTS，动态预算路径（_allocate_dynamic_budgets）复用同一份
        ADJUSTMENTS = ContextService.PACING_ADJUSTMENTS

        budget = dict(DEFAULT)
        adjustments = ADJUSTMENTS.get(pacing_type, {})
        for k, delta in adjustments.items():
            budget[k] = max(0.01, budget.get(k, 0) + delta)

        # Normalize to sum = 1.0
        total = sum(budget.values())
        if abs(total - 1.0) > 0.001:
            scale = 1.0 / total
            budget = {k: v * scale for k, v in budget.items()}

        return {k: int(total_tokens * v) for k, v in budget.items()}

    async def _detect_context_window(self) -> int:
        """推断当前所用模型的上下文窗口大小（token）。

        取值顺序：model_profiles 的 metadata / default_params 中的显式配置
        → 已知模型容量表 → 都取不到则返回 0（调用方据此回落到旧的固定百分比分配）。

        注意：model_profiles.project_id 是 NOT NULL，模型配置是全局的，
        这里沿用 llm_client._get_config 的查询模式（按 task_types 匹配，不按项目过滤）。
        """
        try:
            row = await self._db.fetchrow(
                """
                SELECT model_name, metadata, default_params
                FROM model_profiles
                WHERE status = 'active'
                  AND 'context' = ANY(task_types)
                ORDER BY is_default DESC, tier
                LIMIT 1
                """
            )
            if not row:
                # 没有专门承担 context 角色的模型时，退回任意默认模型
                row = await self._db.fetchrow(
                    """
                    SELECT model_name, metadata, default_params
                    FROM model_profiles
                    WHERE status = 'active'
                    ORDER BY is_default DESC, tier
                    LIMIT 1
                    """
                )
        except Exception:
            logger.debug("context window detection skipped: model_profiles query failed", exc_info=True)
            return 0

        if not row:
            return 0

        # JSONB 列在 asyncpg 下返回字符串，统一先尝试解析
        sources = [ensure_json_value(row["metadata"]), ensure_json_value(row["default_params"])]
        for src in sources:
            if not isinstance(src, dict):
                continue
            for key in ("max_tokens", "context_window", "context_length"):
                val = src.get(key)
                if isinstance(val, bool):
                    continue
                if isinstance(val, (int, float)) and val > 1000:
                    return int(val)

        name = (row["model_name"] or "").lower()
        for key, window in self._KNOWN_CONTEXT_WINDOWS.items():
            if key in name:
                return window
        return 0

    def _allocate_by_priority(self, detected: int) -> dict[str, int]:
        """两级分配：Round 1 按优先级顺序发保底，Round 2 把剩余空间按优先级权重分到上限。

        空间不足时低优先级 section 直接为 0（例如 4K 模型下 P3 全部跳过），
        避免像固定百分比那样"每个 section 都给一点、结果全都不够用"。
        """
        specs = self._CONTEXT_SECTION_SPECS
        total = int(detected * self.CONTEXT_USABLE_RATIO)
        budgets: dict[str, int] = {name: 0 for name in specs}
        remaining = total

        # Round 1: 保底，高优先级先拿
        for prio in (0, 1, 2, 3):
            for name, (p, min_tok, _) in specs.items():
                if p != prio:
                    continue
                give = min(min_tok, max(0, remaining))
                budgets[name] = give
                remaining -= give
            if remaining <= 0:
                break

        # Round 2: 剩余空间按权重（权重 = 4 - 优先级）分，受各 section 上限约束
        caps = {name: int(detected * max_ratio) for name, (_, _, max_ratio) in specs.items()}
        for _ in range(4):
            if remaining <= 0:
                break
            candidates = [(n, p) for n, (p, _, _) in specs.items() if budgets[n] < caps[n]]
            if not candidates:
                break
            total_weight = sum(4 - p for _, p in candidates)
            if total_weight <= 0:
                break
            allocated = 0
            for name, prio in candidates:
                headroom = caps[name] - budgets[name]
                share = int(remaining * ((4 - prio) / total_weight))
                give = min(share, headroom, remaining - allocated)
                if give > 0:
                    budgets[name] += give
                    allocated += give
            if allocated <= 0:
                break
            remaining -= allocated

        return budgets

    # 调用方未指定预算时的兜底（仅当探测不到模型窗口时使用）
    DEFAULT_TOTAL_TOKENS = 8000
    # 动态上下文预算默认开启；部署侧可设 NOVEL_CONTEXT_DYNAMIC_BUDGET=0 回落固定百分比
    CONTEXT_DYNAMIC_BUDGET_DEFAULT = "1"

    def _allocate_dynamic_budgets(self, detected: int, pacing_type: str,
                                  total_tokens: int = 0) -> dict[str, int]:
        """按模型上下文窗口动态分配各 section 预算，并叠加节奏调整。

        detected 只作为"上界"（窗口内可用空间），绝不放大调用方传入的预算：
        各 section 之和 = min(detected * CONTEXT_USABLE_RATIO, total_tokens)。
        """
        budgets = self._allocate_by_priority(detected)
        total = sum(budgets.values())
        if total <= 0:
            return self._compute_section_budgets(pacing_type, total_tokens)

        # 归一化成比例后套用 PACING_ADJUSTMENTS（与旧路径语义一致：增量相加后重新归一化）
        ratios = {k: v / total for k, v in budgets.items()}
        for k, delta in self.PACING_ADJUSTMENTS.get(pacing_type, {}).items():
            ratios[k] = max(0.0, ratios.get(k, 0.0) + delta)
        ratio_total = sum(ratios.values()) or 1.0

        # 窗口决定"最多能用多少"，调用方预算决定"实际给多少"
        window_cap = int(detected * self.CONTEXT_USABLE_RATIO)
        target = min(window_cap, total_tokens) if total_tokens > 0 else window_cap
        out = {k: int(target * (v / ratio_total)) for k, v in ratios.items()}

        # 保底不被取整抹掉：P0 section 至少拿到规格中的保底值
        for name, spec in self._CONTEXT_SECTION_SPECS.items():
            prio, min_tok = spec[0], spec[1]
            if prio == 0:
                out[name] = max(out[name], min(min_tok, target))
        return out

    async def _resolve_section_budgets(self, pacing_type: str, total_tokens: int) -> dict[str, int]:
        """决定各 section 的 token 预算。

        开关 `NOVEL_CONTEXT_DYNAMIC_BUDGET=1` 且能探测到模型上下文窗口时走动态分配，
        否则回落到原有的固定百分比分配 —— 开关默认关闭，保证改造前后行为一致。
        """
        if os.getenv("NOVEL_CONTEXT_DYNAMIC_BUDGET", self.CONTEXT_DYNAMIC_BUDGET_DEFAULT) == "0":
            return self._compute_section_budgets(pacing_type, total_tokens)

        detected = await self._detect_context_window()
        if detected <= 0:
            logger.info("dynamic context budget disabled: context window not detected, falling back")
            return self._compute_section_budgets(pacing_type, total_tokens)

        budgets = self._allocate_dynamic_budgets(detected, pacing_type, total_tokens)
        logger.info(
            "dynamic context budget: window=%s requested=%s allocated=%s sections_nonzero=%s",
            detected, total_tokens, sum(budgets.values()),
            sum(1 for v in budgets.values() if v > 0),
        )
        return budgets

    async def _load_delta_state(
        self,
        project_id: str,
        chapter_no: int,
        known_entity_names: set[str],
    ) -> list[dict[str, Any]]:
        """Load state entities that are new or changed since last context."""
        if not known_entity_names:
            return []
        rows = await self._db.fetch(
            """
            SELECT e.entity_type, e.name, e.lifecycle_status, s.state,
                   s.effective_chapter_no, s.expire_chapter_no,
                   s.effective_volume_no, s.expire_volume_no,
                   s.duration_type, s.expires_on_event,
                   s.confidence, s.source_type, s.source_id,
                   s.change_reason, s.metadata
            FROM state_entities e
            JOIN state_snapshots s ON s.entity_id = e.id AND s.is_current = true
            WHERE e.project_id = $1
              AND (s.effective_chapter_no IS NULL OR s.effective_chapter_no <= $2)
              AND (s.expire_chapter_no IS NULL OR s.expire_chapter_no >= $2)
              AND (
                NOT (e.name = ANY($3::text[]))
                OR s.change_reason IS NOT NULL
              )
            """,
            project_id,
            chapter_no,
            list(known_entity_names),
        )
        all_state = rows_to_dicts(rows)
        for s in all_state:
            s["state"] = ensure_json_value(s.get("state") or {})
            s["metadata"] = ensure_json_value(s.get("metadata") or {})
        return all_state

    async def _extract_chapter_characters(
        self, project_id: str, chapter_no: int, focus: list[str] | None = None,
    ) -> list[str]:
        """Extract character names that appear in or near this chapter's context."""
        # 1. Get chapter plan text as primary search source
        plan_row = await self._db.fetchrow(
            "SELECT plan FROM chapter_plans WHERE project_id = $1 AND chapter_no = $2 "
            "AND status <> 'superseded' ORDER BY created_at DESC LIMIT 1",
            project_id, chapter_no,
        )
        plan_text = (plan_row["plan"] if plan_row else "") or ""
        # 2. Build search terms: plan text words + focus terms
        import re as _re
        plan_words = [w for w in _re.split(r'\s+', plan_text) if len(w) >= 2]
        search_terms = list(plan_words) + list(focus or [])
        if not search_terms:
            return []
        # 3. Query state_entities matching any search term (name or alias)
        try:
            rows = await self._db.fetch(
                """
                SELECT DISTINCT e.name
                FROM state_entities e
                WHERE e.project_id = $1
                  AND e.entity_type IN ('character', 'organization', 'faction')
                  AND e.lifecycle_status = 'active'
                  AND (
                    e.name ILIKE ANY(SELECT '%' || UNNEST($2::text[]) || '%')
                    OR EXISTS (
                      SELECT 1 FROM jsonb_array_elements_text(
                        COALESCE(e.aliases, '[]'::jsonb)
                      ) AS a
                      WHERE a ILIKE ANY(SELECT '%' || UNNEST($2::text[]) || '%')
                    )
                  )
                ORDER BY e.name
                LIMIT 20
                """,
                project_id,
                search_terms,
            )
            if rows:
                return [r["name"] for r in rows]
        except Exception:
            logger.warning("Character extraction query failed, falling back to plan scan", exc_info=True)
        # 4. Fallback: find entity names that appear literally in plan text
        entity_rows = await self._db.fetch(
            """
            SELECT DISTINCT e.name FROM state_entities e
            WHERE e.project_id = $1 AND e.lifecycle_status = 'active'
              AND position(lower(e.name) in lower($2)) > 0
            LIMIT 20
            """,
            project_id, plan_text,
        )
        return [r["name"] for r in entity_rows] if entity_rows else []

    # 旧 knowledge_base 表的替代数据源（见 docs/07-planning/category-unification.md §2.3）：
    #   角色 / 阵营卡片  → state_entities
    #   力量体系 / 世界设定 / 情节参考 → project_knowledge
    _ENTITY_CARD_TYPES = ("character", "faction", "organization")
    _PK_CATEGORIES = ("power_system", "world_building", "plot_and_story")

    async def _fetch_entity_cards(
        self, project_id: str, keyword: str, limit: int = 3,
    ) -> list[dict[str, Any]]:
        """按关键词从 state_entities 取角色 / 阵营卡片。查询失败时返回空列表。"""
        try:
            rows = await self._db.fetch(
                """
                SELECT id::text, entity_type, name,
                       COALESCE(summary, '') AS summary,
                       COALESCE(description, '') AS description
                FROM state_entities
                WHERE project_id = $1
                  AND entity_type = ANY($2::text[])
                  AND lifecycle_status = 'active'
                  AND (
                        name ILIKE '%' || $3 || '%'
                     OR summary ILIKE '%' || $3 || '%'
                     OR description ILIKE '%' || $3 || '%'
                  )
                LIMIT $4
                """,
                project_id, list(self._ENTITY_CARD_TYPES), keyword, limit,
            )
            return [dict(r) for r in rows]
        except Exception:
            logger.warning("state_entities card retrieval failed", exc_info=True)
            return []

    async def _fetch_project_knowledge(
        self, project_id: str, keyword: str, limit: int = 4,
    ) -> list[dict[str, Any]]:
        """按关键词从 project_knowledge 取力量体系 / 世界设定 / 情节参考。查询失败时返回空列表。"""
        try:
            rows = await self._db.fetch(
                """
                SELECT id::text, category, key,
                       COALESCE(description, '') AS description,
                       value::text AS value_text
                FROM project_knowledge
                WHERE project_id = $1
                  AND category = ANY($2::text[])
                  AND COALESCE(status, 'active') = 'active'
                  AND (
                        key ILIKE '%' || $3 || '%'
                     OR description ILIKE '%' || $3 || '%'
                     OR value::text ILIKE '%' || $3 || '%'
                  )
                LIMIT $4
                """,
                project_id, list(self._PK_CATEGORIES), keyword, limit,
            )
            return [dict(r) for r in rows]
        except Exception:
            logger.warning("project_knowledge retrieval failed", exc_info=True)
            return []

    async def _retrieve_knowledge_base(
        self,
        project_id: str,
        focus: list[str],
        chapter_characters: list[str],
        token_budget: int,
        genre: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant knowledge items (character cards, faction info, etc.).

        数据源（已不依赖旧的 knowledge_base 表）：
          - 角色 / 阵营卡片 → state_entities
          - 力量体系 / 世界设定 / 情节参考 → project_knowledge
          - 通用知识 → universal_knowledge

        Uses keyword ILIKE for candidate generation, then rerank for precision.

        注意：section 名沿用 `knowledge_base`（预算配置、stage section 集合、
        返回值统计都以此为键），仅 `kb_type` 标注真实来源。
        """
        results: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        # Search by character names — 角色 / 阵营卡片 (扩大候选集)
        for name in chapter_characters[:10]:
            for r in await self._fetch_entity_cards(project_id, name, limit=3):
                rid = r["id"]
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    results.append({
                        "id": rid,
                        "kb_type": f"state_entity:{r['entity_type']}",
                        "title": r["name"],
                        "content": r["summary"] or r["description"],
                        "tags": [],
                        "relevance_score": 0,
                    })

        # Search by focus terms — 项目知识（力量体系 / 世界设定 / 情节参考）
        for term in focus[:5]:
            for r in await self._fetch_project_knowledge(project_id, term, limit=4):
                rid = r["id"]
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    results.append({
                        "id": rid,
                        "kb_type": f"project_knowledge:{r['category']}",
                        "title": r["key"],
                        "content": r["description"] or r["value_text"] or "",
                        "tags": [],
                        "relevance_score": 0,
                    })

        # Also search UK with genre filtering for richer context
        if genre:
            try:
                search_terms = (focus + chapter_characters)[:5]
                if search_terms:
                    conditions = ["uk.status = 'active'", "$1 = ANY(uk.genre_tags)"]
                    params: list[Any] = [genre]
                    for i, term in enumerate(search_terms):
                        idx = len(params) + 1
                        params.append(term)
                        conditions.append(f"uk.search_vector @@ plainto_tsquery('simple', ${idx})")
                    where = " AND ".join(conditions)
                    params.append(10)
                    uk_rows = await self._db.fetch(
                        f"""
                        SELECT uk.id::text, uk.topic, uk.content, uk.genre_tags
                        FROM universal_knowledge uk
                        WHERE {where}
                        ORDER BY uk.reliability DESC, uk.use_count DESC
                        LIMIT ${len(params)}
                        """,
                        *params,
                    )
                    for item in uk_rows:
                        uk_id = item["id"]
                        if uk_id not in seen_ids:
                            seen_ids.add(uk_id)
                            results.append({
                                "id": uk_id,
                                "kb_type": "universal_knowledge",
                                "title": item.get("topic", ""),
                                "content": item.get("content") or "",
                                "tags": ensure_json_value(item.get("genre_tags") or []),
                                "relevance_score": 8.0,
                            })
            except Exception:
                logger.warning("UK search failed for genre-aware KB retrieval", exc_info=True)

        # Rerank: use rerank model to re-score candidates by relevance
        if self._rerank and results and len(results) > 3:
            try:
                query_text = " ".join((focus or []) + (chapter_characters or []))
                docs = [f"{r['title']} {r.get('content', '')[:500]}" for r in results]
                top_n = min(15, len(results))
                reranked = await self._rerank.rerank(project_id, query_text, docs, top_n=top_n)
                results = [results[item["index"]] for item in reranked]
            except Exception:
                logger.debug("Rerank unavailable for KB, falling back to keyword score", exc_info=True)

        # Sort by relevance and trim to budget
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return self._trim_section("knowledge_base", results, token_budget)

    async def _rank_state_entities(
        self,
        all_entities: list[dict[str, Any]],
        chapter_characters: list[str],
        focus: list[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        """Re-rank state entities by relevance to this chapter."""
        focus_lower = [f.lower() for f in focus]
        char_lower = [c.lower() for c in chapter_characters]

        def _relevance_score(entity: dict[str, Any]) -> float:
            score = 0.0
            name_lower = (entity.get("name") or "").lower()
            # Direct character match
            if name_lower in char_lower:
                score += 10.0
            # Partial name match with focus
            for f in focus_lower:
                if f in name_lower or name_lower in f:
                    score += 5.0
            # Lifecycle bonus
            status = entity.get("lifecycle_status") or entity.get("entity_type")
            if status == "active":
                score += 2.0
            elif status == "exited":
                score -= 3.0
            # Expiry urgency
            expire_ch = entity.get("expire_chapter_no")
            if expire_ch is not None:
                score += 1.0  # About to expire = likely relevant
            return score

        all_entities.sort(key=_relevance_score, reverse=True)
        return all_entities[:limit]

    # Pass→section filter: only included sections fetched for each pass
    PASS_SECTIONS: dict[int, set[str]] = {
        1: {"active_rules", "chapter_plan", "open_foreshadowing", "knowledge_base", "project_knowledge", "canon_documents", "compressed_context"},
        2: {"active_rules", "current_state", "knowledge_base", "universal_knowledge", "project_knowledge",
            "canon_documents", "entity_relationships",
            "open_foreshadowing", "recent_summaries", "chapter_plan", "relevant_memory", "compressed_context",
            "character_arcs", "causal_chains"},
        3: {"active_rules", "current_state", "knowledge_base", "universal_knowledge", "project_knowledge",
            "canon_documents", "entity_relationships",
            "recent_summaries", "relevant_memory",
            "character_arcs", "style_guidance"},
        4: {"active_rules", "current_state", "knowledge_base", "universal_knowledge", "project_knowledge",
            "canon_documents", "entity_relationships",
            "open_foreshadowing", "recent_summaries", "chapter_plan", "relevant_memory", "compressed_context",
            "character_arcs", "causal_chains", "style_guidance", "pacing_guidance"},
    }

    # ── Section loaders for prepare_chapter_context ──

    async def _load_rules_section(
        self, project_id: str, chapter_no: int, volume_no: int | None,
        scope_refs: list[str], scope_types: list[str] | None,
        active_event_keys: list[str] | None, chapter_characters: list[str],
        token_budget: int, genre: str | None = None, chapter_plan: dict | None = None,
    ) -> tuple[list[dict], dict[str, Any]]:
        effective_rules = await self._rules.list_effective_rules(
            project_id=project_id,
            rule_types=["canon", "character", "plot", "style", "forbidden", "reveal_lock", "lesson"],
            chapter_no=chapter_no, volume_no=volume_no,
            scope_refs=scope_refs or chapter_characters,
            scope_types=scope_types, active_event_keys=active_event_keys,
        )
        global_rules = await self._rules.list_active_global()
        all_rules = global_rules + effective_rules["rules"]
        if len(all_rules) > 30 and chapter_plan:
            plan_text = json_dumps(chapter_plan) if isinstance(chapter_plan, dict) else str(chapter_plan)
            scene_type = self._infer_scene_type(plan_text)
            filtered = [
                r for r in all_rules
                if r.get("severity") == "critical"
                or self._rule_matches_context(r, genre, scene_type)
            ]
            critical = [r for r in filtered if r.get("severity") == "critical"]
            rest = [r for r in filtered if r.get("severity") != "critical"]
            rest = await self._rank_rules_by_embedding(rest, plan_text, project_id)
            all_rules = critical + rest
        if len(all_rules) > 30:
            all_rules = await self._summarize_rules_if_needed(all_rules, genre)
        rules = self._trim_section("active_rules", all_rules, token_budget)
        return rules, effective_rules

    def _infer_scene_type(self, plan_text: str) -> list[str]:
        SCENE_KW = {
            "battle": ["战斗", "对决", "交锋", "大战", "围剿", "击杀"],
            "cultivation": ["修炼", "突破", "闭关", "悟道", "渡劫", "炼丹"],
            "trade": ["拍卖", "交易", "兑换", "购买", "出售"],
            "social": ["宴会", "宗门", "朝堂", "比武", "会面"],
            "exploration": ["探索", "秘境", "遗迹", "寻宝", "古墓"],
            "dialogue": ["对话", "谈判", "商议", "密谈", "盘问"],
        }
        matches = [s for s, kws in SCENE_KW.items() if any(k in plan_text for k in kws)]
        return matches or ["general"]

    def _rule_matches_context(self, rule: dict, genre: str | None, scene_types: list[str]) -> bool:
        meta = rule.get("metadata") or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                meta = {}
        rule_genres = meta.get("genres") or []
        rule_scenes = meta.get("scene_types") or []
        if rule_genres and genre and genre not in rule_genres:
            return False
        if rule_scenes and not any(s in rule_scenes for s in scene_types):
            return False
        return True

    async def _rank_rules_by_embedding(
        self, rules: list[dict], query_text: str, project_id: str,
    ) -> list[dict]:
        if not self._embedding or not rules:
            return rules
        try:
            query_vec = await self._embedding.embed_single(project_id, query_text)
            if not query_vec:
                return rules
            rule_texts = [f"{r.get('title', '')} {r.get('content', '')[:300]}" for r in rules]
            rule_vecs = await self._embedding.embed(project_id, rule_texts)
            for i, vec in enumerate(rule_vecs):
                if vec:
                    dot = sum(x * y for x, y in zip(query_vec, vec))
                    na = (sum(x * x for x in query_vec) ** 0.5)
                    nb = (sum(y * y for y in vec) ** 0.5)
                    rules[i]["_score"] = dot / (na * nb) if na and nb else 0
            rules.sort(key=lambda x: x.get("_score", 0), reverse=True)
            for r in rules:
                r.pop("_score", None)
        except Exception:
            logger.debug("Rule embedding ranking skipped", exc_info=True)
        return rules

    async def _summarize_rules_if_needed(
        self, rules: list[dict], genre: str | None,
    ) -> list[dict]:
        groups: dict[str, list[dict]] = {}
        for r in rules:
            meta = r.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            g = meta.get("rule_group", "general")
            groups.setdefault(g, []).append(r)
        summarized = []
        for group, items in groups.items():
            if len(items) > 5:
                titles = "; ".join([r.get("title", "") for r in items[:10]])
                summarized.append({
                    "id": f"summary_{group}",
                    "rule_key": f"summary_{group}",
                    "rule_type": "creative",
                    "title": f"[归纳] {group}",
                    "content": f"涵盖以下规则要点: {titles}",
                    "severity": "warning",
                    "metadata": {"summarized": True, "source_rule_count": len(items)},
                })
            else:
                summarized.extend(items)
        return summarized

    async def _load_state_section(
        self, project_id: str, chapter_no: int, volume_no: int | None,
        chapter_characters: list[str], focus: list[str], token_budget: int,
        state_limit: int, previous_context: dict[str, Any] | None,
    ) -> list[dict]:
        if previous_context and "current_state" in previous_context:
            prev_entities = previous_context["current_state"]
            known_names = {e.get("name", "") for e in prev_entities}
            all_state = await self._load_delta_state(project_id, chapter_no, known_names)
            prev_valid = [e for e in prev_entities if e.get("name") not in {s.get("name") for s in all_state}]
            all_state = prev_valid + all_state
        else:
            state_rows = await self._db.fetch(
                """
                SELECT e.entity_type, e.name, e.lifecycle_status, s.state,
                       s.effective_chapter_no, s.expire_chapter_no,
                       s.effective_volume_no, s.expire_volume_no,
                       s.duration_type, s.expires_on_event,
                       s.confidence, s.source_type, s.source_id,
                       s.change_reason, s.metadata
                FROM state_entities e
                JOIN state_snapshots s ON s.entity_id = e.id AND s.is_current = true
                WHERE e.project_id = $1
                  AND (s.effective_chapter_no IS NULL OR s.effective_chapter_no <= $2)
                  AND (s.expire_chapter_no IS NULL OR s.expire_chapter_no >= $2)
                  AND ($3::int IS NULL OR s.effective_volume_no IS NULL OR s.effective_volume_no <= $3)
                  AND ($3::int IS NULL OR s.expire_volume_no IS NULL OR s.expire_volume_no >= $3)
                """,
                project_id, chapter_no, volume_no,
            )
            all_state = rows_to_dicts(state_rows)
            for s in all_state:
                s["state"] = ensure_json_value(s.get("state") or {})
                s["metadata"] = ensure_json_value(s.get("metadata") or {})
        current_state = await self._rank_state_entities(all_state, chapter_characters, focus, state_limit)
        return self._trim_section("current_state", current_state, token_budget)

    async def _load_compressed_section(
        self, project_id: str, chapter_no: int, token_budget: int,
    ) -> list[dict]:
        items: list[dict] = []
        try:
            rows = await self._db.fetch(
                """
                SELECT id::text, context_type, chapter_start, chapter_end,
                       summary, key_entities, emotion_arc
                FROM compressed_contexts
                WHERE project_id = $1 AND (chapter_end IS NULL OR chapter_end >= $2)
                ORDER BY chapter_start DESC LIMIT 5
                """,
                project_id, chapter_no,
            )
            for row in rows:
                rd = row_to_dict(row)
                items.append({
                    "type": rd.get("context_type", "unknown"),
                    "chapters": f"{rd.get('chapter_start')}-{rd.get('chapter_end')}",
                    "summary": rd.get("summary", ""),
                    "key_entities": ensure_json_value(rd.get("key_entities") or []),
                })
        except Exception:
            logger.warning("Failed to load compressed context", exc_info=True)
        return self._trim_section("compressed_context", items, token_budget)

    async def _load_uk_section(
        self, project_id: str, focus: list[str], chapter_characters: list[str],
        token_budget: int,
    ) -> list[dict]:
        items: list[dict] = []
        try:
            from .kb_service import KBService
            kb_svc = KBService(self._db)
            search_terms = (focus or []) + (chapter_characters or [])
            for term in search_terms[:5]:
                results = await kb_svc.uk_search(query=term, limit=3)
                items.extend(results)
            seen_ids: set[str] = set()
            deduped = []
            for item in items:
                item_id = item.get("id")
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    deduped.append(item)
            items = deduped
        except Exception:
            logger.warning("Failed to load universal knowledge", exc_info=True)
        return self._trim_section("universal_knowledge", items, token_budget)

    async def _load_pk_section(
        self, project_id: str, chapter_no: int, token_budget: int,
    ) -> list[dict]:
        items: list[dict] = []
        try:
            from .kb_service import KBService
            kb_svc = KBService(self._db)
            world_state = await kb_svc.world_get_state(project_id, chapter_no)
            if world_state:
                items.append({"type": "world_state", **world_state})
            for cat in ["world_rule", "character", "faction"]:
                cat_items = await kb_svc.pk_list(project_id, category=cat)
                for item in cat_items[:5]:
                    items.append({"category": cat, **item})
        except Exception:
            logger.warning("Failed to load project knowledge", exc_info=True)
        return self._trim_section("project_knowledge", items, token_budget)

    async def _load_canon_section(
        self, project_id: str, chapter_characters: list[str], focus: list[str],
        token_budget: int,
    ) -> list[dict]:
        """Load active canon documents (world rules, character sheets, power systems, etc.)."""
        items: list[dict] = []
        try:
            # 1. Load by doc_type relevance to chapter characters
            if chapter_characters:
                char_patterns = [f"%{name}%" for name in chapter_characters[:8]]
                rows = await self._db.fetch(
                    """
                    SELECT id::text, doc_type, key, title, content, scope, review_status
                    FROM canon_documents
                    WHERE project_id = $1
                      AND status = 'active'
                      AND review_status = 'approved'
                      AND (
                        scope ?| $2::text[]
                        OR title ILIKE ANY($3::text[])
                        OR EXISTS (
                          SELECT 1 FROM unnest($2::text[]) AS pattern
                          WHERE content ILIKE '%' || pattern || '%'
                        )
                      )
                    ORDER BY updated_at DESC
                    LIMIT 15
                    """,
                    project_id,
                    chapter_characters[:8],
                    char_patterns,
                )
                for r in rows:
                    items.append({
                        "id": r["id"],
                        "doc_type": r["doc_type"],
                        "key": r["key"],
                        "title": r["title"],
                        "content": r["content"][:2000],  # cap per-doc
                        "scope": ensure_json_value(r.get("scope") or {}),
                    })
            # 2. Also search by focus terms (global rules, power systems, etc.)
            seen_ids = {i["id"] for i in items}
            for term in focus[:5]:
                rows = await self._db.fetch(
                    """
                    SELECT id::text, doc_type, key, title, content, scope, review_status
                    FROM canon_documents
                    WHERE project_id = $1
                      AND status = 'active'
                      AND review_status = 'approved'
                      AND search_vector @@ plainto_tsquery('simple', $2)
                    ORDER BY updated_at DESC
                    LIMIT 5
                    """,
                    project_id, term,
                )
                for r in rows:
                    rid = r["id"]
                    if rid not in seen_ids:
                        seen_ids.add(rid)
                        items.append({
                            "id": rid,
                            "doc_type": r["doc_type"],
                            "key": r["key"],
                            "title": r["title"],
                            "content": r["content"][:2000],
                            "scope": ensure_json_value(r.get("scope") or {}),
                        })
        except Exception:
            logger.warning("Failed to load canon documents", exc_info=True)
        return self._trim_section("canon_documents", items, token_budget)

    async def _load_relationships_section(
        self, project_id: str, chapter_characters: list[str], chapter_no: int,
        token_budget: int,
    ) -> list[dict]:
        """Load relationships involving characters in this chapter."""
        if not chapter_characters:
            return []
        items: list[dict] = []
        try:
            # Find entity IDs for chapter characters
            name_list = chapter_characters[:12]
            rows = await self._db.fetch(
                """
                SELECT er.id::text,
                       er.relation_type, er.attitude, er.intensity,
                       er.known_by_source, er.known_by_target, er.known_by_reader,
                       er.source_chapter_no, er.metadata,
                       se_src.name AS source_name, se_src.entity_type AS source_type,
                       se_tgt.name AS target_name, se_tgt.entity_type AS target_type
                FROM entity_relationships er
                JOIN state_entities se_src ON er.source_entity_id = se_src.id
                JOIN state_entities se_tgt ON er.target_entity_id = se_tgt.id
                WHERE er.project_id = $1
                  AND er.status = 'active'
                  AND (
                    se_src.name = ANY($2::text[])
                    OR se_tgt.name = ANY($2::text[])
                  )
                ORDER BY er.intensity DESC NULLS LAST, er.source_chapter_no DESC
                LIMIT 30
                """,
                project_id,
                name_list,
            )
            for r in rows:
                items.append({
                    "id": r["id"],
                    "relation_type": r["relation_type"],
                    "source": {"name": r["source_name"], "type": r["source_type"]},
                    "target": {"name": r["target_name"], "type": r["target_type"]},
                    "attitude": r["attitude"],
                    "intensity": float(r["intensity"]) if r["intensity"] is not None else None,
                    "known_by_source": r["known_by_source"],
                    "known_by_target": r["known_by_target"],
                    "known_by_reader": r["known_by_reader"],
                    "established_chapter": r["source_chapter_no"],
                })
        except Exception:
            logger.warning("Failed to load entity relationships", exc_info=True)
        return self._trim_section("entity_relationships", items, token_budget)

    async def _load_arcs_section(
        self, project_id: str, chapter_characters: list[str], chapter_no: int,
        token_budget: int,
    ) -> list[dict]:
        """Load character arc summaries for this chapter's characters."""
        if not self._character_arc or not chapter_characters:
            return []
        items: list[dict] = []
        try:
            for name in chapter_characters[:8]:
                summary = await self._character_arc.get_arc_summary_for_context(
                    project_id, name, chapter_no, max_tokens=150)
                if summary and "no arc data" not in summary:
                    items.append({"character": name, "arc_summary": summary})
        except Exception:
            logger.warning("Failed to load character arcs", exc_info=True)
        return self._trim_section("character_arcs", items, token_budget)

    async def _load_causality_section(
        self, project_id: str, chapter_no: int, token_budget: int,
    ) -> list[dict]:
        """Load causality chain summary for this chapter."""
        if not self._causality:
            return []
        items: list[dict] = []
        try:
            summary = await self._causality.get_causality_summary_for_context(
                project_id, chapter_no, max_tokens=300)
            if summary and "No recent causal chains" not in summary:
                items.append({"summary": summary})
        except Exception:
            logger.warning("Failed to load causality chains", exc_info=True)
        return self._trim_section("causal_chains", items, token_budget)

    async def _load_style_section(
        self, project_id: str, chapter_no: int, token_budget: int,
    ) -> list[dict]:
        """Load style guidance for this chapter."""
        if not self._style_fingerprint:
            return []
        items: list[dict] = []
        try:
            summary = await self._style_fingerprint.get_style_summary_for_context(
                project_id, chapter_no, max_tokens=150)
            if summary:
                items.append({"summary": summary})
        except Exception:
            logger.warning("Failed to load style guidance", exc_info=True)
        return self._trim_section("style_guidance", items, token_budget)

    async def _load_pacing_section(
        self, project_id: str, chapter_no: int, volume_no: int | None,
        token_budget: int,
    ) -> list[dict]:
        """Load pacing guidance for this chapter."""
        if not self._pacing:
            return []
        items: list[dict] = []
        try:
            summary = await self._pacing.get_pacing_summary_for_context(
                project_id, chapter_no, volume_no=volume_no, max_tokens=200)
            if summary:
                items.append({"summary": summary})
        except Exception:
            logger.warning("Failed to load pacing guidance", exc_info=True)
        return self._trim_section("pacing_guidance", items, token_budget)

    def _build_warnings(
        self, overflow_warnings: list[dict], current_state: list[dict],
        effective_rules: dict, foreshadowing: list[dict], chapter_no: int,
        expiry_window: int,
    ) -> list[dict]:
        warnings = list(overflow_warnings)
        for s in current_state:
            expire = s.get("expire_chapter_no")
            if expire is not None and 0 <= int(expire) - chapter_no <= expiry_window:
                warnings.append({"type": "state_expiring", "entity_type": s.get("entity_type"),
                                 "name": s.get("name"), "expire_chapter_no": expire})
        for r in effective_rules.get("excluded", []):
            warnings.append({"type": "rule_excluded", "rule_key": r.get("rule_key"),
                             "excluded_reason": r.get("excluded_reason")})
        for f in foreshadowing:
            f["payload"] = ensure_json_value(f.get("payload") or {})
            if f.get("is_overdue"):
                warnings.append({"type": "foreshadowing_overdue", "key": f.get("key"),
                                 "title": f.get("title"), "overdue_policy": f.get("overdue_policy")})
        return warnings

    async def prepare_chapter_context(
        self,
        project_id: str,
        chapter_no: int,
        purpose: str,
        focus: list[str],
        budget: dict[str, Any],
        volume_no: int | None = None,
        scope_refs: list[str] | None = None,
        scope_types: list[str] | None = None,
        active_event_keys: list[str] | None = None,
        pov_mode: str = "omniscient",
        pass_number: int | None = None,
        previous_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raw_budget = budget.get("total_tokens") or budget.get("max_tokens")
        if not raw_budget:
            # 未给预算时按探测到的模型窗口取可用比例，探测不到才用常量兜底
            detected_window = await self._detect_context_window()
            raw_budget = (int(detected_window * self.CONTEXT_USABLE_RATIO)
                          if detected_window > 0 else self.DEFAULT_TOTAL_TOKENS)
            logger.info("chapter context budget not provided, fallback=%s (detected_window=%s)",
                        raw_budget, detected_window)
        total_budget = int(raw_budget)
        pacing_type = budget.get("pacing_type") or await self._resolve_pacing_type(project_id, chapter_no)
        section_budgets = await self._resolve_section_budgets(pacing_type, total_budget)
        output_overhead = int(total_budget * 0.03)
        effective_budget = total_budget - output_overhead
        wanted = self.PASS_SECTIONS.get(pass_number, set()) if pass_number else set()
        resolved_volume_no = await self._resolve_volume_no(project_id, chapter_no, volume_no)
        chapter_characters = await self._extract_chapter_characters(project_id, chapter_no, focus)

        # Load each section (parallel where possible in future)
        rules, effective_rules = [], {"rules": [], "excluded": []}
        if not wanted or "active_rules" in wanted:
            rules, effective_rules = await self._load_rules_section(
                project_id, chapter_no, resolved_volume_no, scope_refs or [],
                scope_types, active_event_keys, chapter_characters, section_budgets["active_rules"],
                genre=budget.get("genre"), chapter_plan=budget.get("chapter_plan"))

        kb_items = []
        if not wanted or "knowledge_base" in wanted:
            kb_items = await self._retrieve_knowledge_base(
                project_id, focus, chapter_characters, section_budgets["knowledge_base"], genre=budget.get("genre"))

        current_state, all_state = [], []
        if not wanted or "current_state" in wanted:
            current_state = await self._load_state_section(
                project_id, chapter_no, resolved_volume_no, chapter_characters, focus,
                section_budgets["current_state"], int(budget.get("state_limit", 40)), previous_context)
            all_state = current_state  # for audit

        recent = []
        if not wanted or "recent_summaries" in wanted:
            if previous_context and "recent_summaries" in previous_context:
                prev_summaries = previous_context["recent_summaries"]
                latest = await self._memory.get_summary(project_id, chapter_no - 1)
                recent = ([latest] + prev_summaries) if latest else prev_summaries
                recent = recent[:int(budget.get("recent_count", 8))]
            else:
                recent = await self._memory.recent_summaries(project_id, chapter_no, int(budget.get("recent_count", 8)))
            recent = self._trim_section("recent_summaries", recent, section_budgets["recent_summaries"])

        plan = None
        if not wanted or "chapter_plan" in wanted:
            plan = await self._db.fetchrow(
                "SELECT id::text, chapter_no, plan, status, created_at FROM chapter_plans "
                "WHERE project_id = $1 AND chapter_no = $2 AND status <> 'superseded' "
                "ORDER BY created_at DESC LIMIT 1", project_id, chapter_no)

        foreshadowing = []
        if not wanted or "open_foreshadowing" in wanted:
            foreshadowing_layers = budget.get("foreshadowing_layers")
            if foreshadowing_layers is None and pov_mode not in {"omniscient", "review"}:
                foreshadowing_layers = ["visible"]
            foreshadowing = await self._plot.list_foreshadowing(
                project_id, ["planted", "developing", "ready_to_payoff"], ["high", "critical"],
                int(budget.get("foreshadowing_limit", 50)), layers=foreshadowing_layers, overdue_at_chapter=chapter_no)
            foreshadowing = self._trim_section("open_foreshadowing", foreshadowing, section_budgets["open_foreshadowing"])

        long_memory = []
        if not wanted or "relevant_memory" in wanted:
            for term in focus[:3]:
                long_memory.extend(await self._memory.search(project_id, term, None, 5))
            long_memory = self._trim_section("relevant_memory", long_memory[:int(budget.get("memory_limit", 20))], section_budgets["relevant_memory"])

        compressed_items = []
        if not wanted or "compressed_context" in wanted:
            compressed_items = await self._load_compressed_section(project_id, chapter_no, section_budgets["compressed_context"])

        universal_knowledge_items = []
        if not wanted or "universal_knowledge" in wanted:
            universal_knowledge_items = await self._load_uk_section(project_id, focus, chapter_characters, section_budgets["universal_knowledge"])

        project_knowledge_items = []
        if not wanted or "project_knowledge" in wanted:
            project_knowledge_items = await self._load_pk_section(project_id, chapter_no, section_budgets["project_knowledge"])

        canon_items = []
        if not wanted or "canon_documents" in wanted:
            canon_items = await self._load_canon_section(project_id, chapter_characters, focus, section_budgets["canon_documents"])

        relationship_items = []
        if not wanted or "entity_relationships" in wanted:
            relationship_items = await self._load_relationships_section(project_id, chapter_characters, chapter_no, section_budgets["entity_relationships"])

        arc_items = []
        if not wanted or "character_arcs" in wanted:
            arc_items = await self._load_arcs_section(project_id, chapter_characters, chapter_no, section_budgets["character_arcs"])

        causality_items = []
        if not wanted or "causal_chains" in wanted:
            causality_items = await self._load_causality_section(project_id, chapter_no, section_budgets["causal_chains"])

        style_items = []
        if not wanted or "style_guidance" in wanted:
            style_items = await self._load_style_section(project_id, chapter_no, section_budgets["style_guidance"])

        pacing_items = []
        if not wanted or "pacing_guidance" in wanted:
            pacing_items = await self._load_pacing_section(project_id, chapter_no, resolved_volume_no, section_budgets["pacing_guidance"])

        # Assemble + trim
        sections = [
            self._section("active_rules", {"rules": rules, "excluded": effective_rules["excluded"]}, len(rules)),
            self._section("current_state", current_state, len(current_state)),
            self._section("knowledge_base", kb_items, len(kb_items)),
            self._section("universal_knowledge", universal_knowledge_items, len(universal_knowledge_items)),
            self._section("project_knowledge", project_knowledge_items, len(project_knowledge_items)),
            self._section("canon_documents", canon_items, len(canon_items)),
            self._section("entity_relationships", relationship_items, len(relationship_items)),
            self._section("open_foreshadowing", foreshadowing, len(foreshadowing)),
            self._section("recent_summaries", recent, len(recent)),
            self._section("chapter_plan", row_to_dict(plan) or {}, 1 if plan else 0),
            self._section("relevant_memory", long_memory, len(long_memory)),
            self._section("compressed_context", compressed_items, len(compressed_items)),
            self._section("character_arcs", arc_items, len(arc_items)),
            self._section("causal_chains", causality_items, len(causality_items)),
            self._section("style_guidance", style_items, len(style_items)),
            self._section("pacing_guidance", pacing_items, len(pacing_items)),
        ]

        used_tokens = sum(int(s.get("tokens_estimated") or 0) for s in sections if isinstance(s, dict))
        overflow_tokens = max(0, used_tokens - effective_budget)
        overflow_warnings: list[dict[str, Any]] = []
        if overflow_tokens > 0:
            sorted_sections = sorted(
                [(s, self.TRIM_PRIORITY.get(s.get("name", ""), 5)) for s in sections if isinstance(s, dict)],
                key=lambda x: x[1])
            remaining = overflow_tokens
            for section, _p in sorted_sections:
                if remaining <= 0:
                    break
                content = section.get("content")
                sec_tok = int(section.get("tokens_estimated") or 0)
                if isinstance(content, list) and len(content) > 1:
                    trim_amount = min(sec_tok, remaining)
                    removed = 0
                    new_content = []
                    for item in reversed(content):
                        item_tok = self._item_tokens(item)
                        if removed + item_tok > trim_amount:
                            new_content.append(item)
                            break
                        removed += item_tok
                    new_content.reverse()
                    section["content"] = new_content
                    section["tokens_estimated"] = sum(self._item_tokens(i) for i in new_content)
                    remaining -= removed
                    overflow_warnings.append({"type": "section_trimmed", "section": section.get("name"),
                                              "tokens_removed": removed, "items_remaining": len(new_content)})

        used_tokens = sum(int(s.get("tokens_estimated") or 0) for s in sections if isinstance(s, dict))
        if used_tokens > total_budget:
            overflow_warnings.append({"type": "hard_overflow", "estimated_tokens": used_tokens,
                                      "budget_tokens": total_budget, "overflow_tokens": used_tokens - total_budget,
                                      "message": "Context still exceeds budget after trimming."})

        warnings = self._build_warnings(overflow_warnings, current_state, effective_rules,
                                        foreshadowing, chapter_no, int(budget.get("state_expiry_warning_window", 3)))
        retrieval_audit = [
            {"source": "canon_rules", "count": len(rules), "excluded_count": len(effective_rules["excluded"])},
            {"source": "knowledge_base", "count": len(kb_items)},
            {"source": "state_snapshots", "count": len(current_state), "total_available": len(all_state)},
            {"source": "canon_documents", "count": len(canon_items)},
            {"source": "entity_relationships", "count": len(relationship_items)},
            {"source": "recent_summaries", "count": len(recent)},
            {"source": "foreshadowing", "count": len(foreshadowing)},
            {"source": "memory_chunks", "count": len(long_memory)},
            {"source": "compressed_context", "count": len(compressed_items)},
            {"source": "character_arcs", "count": len(arc_items)},
            {"source": "causal_chains", "count": len(causality_items)},
            {"source": "style_guidance", "count": len(style_items)},
            {"source": "pacing_guidance", "count": len(pacing_items)},
            {"source": "chapter_characters", "count": len(chapter_characters), "names": chapter_characters[:10]},
            {"token_usage": {"estimated": used_tokens, "budget": total_budget, "utilization": round(used_tokens / total_budget * 100, 1)}},
        ]

        output_constraint = self._build_output_constraint(chapter_no, focus, chapter_characters, rules)
        row = await self._db.fetchrow(
            """
            INSERT INTO context_packs (project_id, chapter_no, purpose, focus, budget, sections, retrieval_audit, warnings)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7::jsonb, $8::jsonb)
            RETURNING id::text, chapter_no, purpose, focus, budget, sections, retrieval_audit, warnings, created_at
            """,
            project_id, chapter_no, purpose, focus,
            json_dumps({**budget, "volume_no": resolved_volume_no, "pov_mode": pov_mode,
                        "total_tokens": total_budget, "effective_tokens": effective_budget, "output_overhead": output_overhead}),
            json_dumps(sections), json_dumps(retrieval_audit), json_dumps(warnings),
        )
        result = self._normalize_context_pack(row_to_dict(row))
        result["output_constraint"] = output_constraint
        return result

    @staticmethod
    def _build_output_constraint(
        chapter_no: int,
        focus: list[str],
        chapter_characters: list[str],
        rules: list[dict[str, Any]],
    ) -> str:
        """Build structured output constraint to prevent hallucination."""
        forbidden_rules = [r for r in rules if r.get("rule_type") == "forbidden"]
        canon_rules = [r for r in rules if r.get("rule_type") == "canon"]

        lines = [
            f"=== GENERATION CONSTRAINTS FOR CHAPTER {chapter_no} ===",
            "",
            "MANDATORY RULES (violation = reject):",
        ]
        for r in (canon_rules + forbidden_rules)[:15]:
            lines.append(f"- [{r.get('rule_type', 'unknown')}] {r.get('rule_key', '')}: {r.get('content', '')[:200]}")

        if chapter_characters:
            lines.append("")
            lines.append(f"CHARACTERS IN THIS CHAPTER: {', '.join(chapter_characters[:10])}")
            lines.append("Use ONLY the character states provided in context. Do not invent new abilities, relationships, or locations.")

        if focus:
            lines.append("")
            lines.append(f"FOCUS TOPICS: {', '.join(focus[:5])}")

        lines.append("")
        lines.append("OUTPUT FORMAT:")
        lines.append("- Write the chapter content directly")
        lines.append("- Do NOT add meta-commentary or explanations")
        lines.append("- Reference context facts naturally, do not copy-paste")
        lines.append("- If context is insufficient for a detail, leave it vague rather than fabricate")
        lines.append(f"=== END CONSTRAINTS (chapter {chapter_no}) ===")
        return "\n".join(lines)

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count for mixed Chinese/English text.

        Chinese characters ≈ 1.5 tokens each, ASCII words ≈ 1.3 tokens/word.
        Conservative estimate to prevent overflow.
        """
        if not text:
            return 0
        chinese_chars = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
        non_chinese = len(text) - chinese_chars
        ascii_words = len(text.split()) if non_chinese > 0 else 0
        return int(chinese_chars * 1.5 + ascii_words * 1.3) + 4

    def _item_tokens(self, item: Any) -> int:
        """Estimate token count for a single context item."""
        if isinstance(item, dict):
            return self._estimate_tokens(json_dumps(item))
        return self._estimate_tokens(str(item))

    # ── Section trim priority (lower = trim first) ──
    TRIM_PRIORITY: dict[str, int] = {
        "compressed_context": 1,
        "relevant_memory": 2,
        "recent_summaries": 3,
        "open_foreshadowing": 4,
        "style_guidance": 4,
        "pacing_guidance": 4,
        "chapter_plan": 5,
        "universal_knowledge": 6,
        "project_knowledge": 6,
        "causal_chains": 6,
        "entity_relationships": 7,
        "character_arcs": 7,
        "canon_documents": 8,
        "current_state": 8,
        "knowledge_base": 9,
        "active_rules": 10,
    }

    def _trim_section(
        self,
        section_name: str,
        items: list[Any] | dict[str, Any],
        token_budget: int,
    ) -> Any:
        """Trim a section to fit within its token budget using accurate token estimation."""
        if isinstance(items, dict):
            serialized = json_dumps(items)
            if self._estimate_tokens(serialized) <= token_budget:
                return items
            return items
        if not isinstance(items, list):
            return items
        total = 0
        result = []
        for item in items:
            item_tok = self._item_tokens(item)
            if total + item_tok > token_budget:
                break
            result.append(item)
            total += item_tok
        return result

    async def list_context_packs(
        self,
        project_id: str,
        chapter_no: int | None = None,
        purpose: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        param_idx = 1
        
        if chapter_no is not None:
            param_idx += 1
            conditions.append(f"chapter_no = ${param_idx}")
            params.append(chapter_no)
        
        if purpose is not None:
            param_idx += 1
            conditions.append(f"purpose = ${param_idx}")
            params.append(purpose)
        
        param_idx += 1
        params.append(limit)
        
        where_sql = " AND ".join(conditions)
        rows = await self._db.fetch(
            f"""
            SELECT id::text, chapter_no, purpose, focus, budget, sections, retrieval_audit, warnings, created_at
            FROM context_packs
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx}
            """,
            *params,
        )
        return [self._normalize_context_pack(row_to_dict(row)) for row in rows]

    async def get_context_pack(
        self,
        project_id: str,
        context_pack_id: str | None = None,
        chapter_no: int | None = None,
    ) -> dict[str, Any]:
        if context_pack_id is None and chapter_no is None:
            raise ValueError("context_pack_id or chapter_no is required")
        row = await self._db.fetchrow(
            """
            SELECT id::text, chapter_no, purpose, focus, budget, sections, retrieval_audit, warnings, created_at
            FROM context_packs
            WHERE project_id = $1
              AND ($2::uuid IS NULL OR id = $2)
              AND ($3::int IS NULL OR chapter_no = $3)
            ORDER BY created_at DESC
            LIMIT 1
            """,
            project_id,
            context_pack_id,
            chapter_no,
        )
        if row is None:
            raise ValueError("Context pack not found")
        return self._normalize_context_pack(row_to_dict(row))

    async def validate_context_pack(
        self,
        project_id: str,
        context_pack_id: str | None = None,
        chapter_no: int | None = None,
        context_pack: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        pack = self._normalize_context_pack(context_pack) if context_pack else await self.get_context_pack(project_id, context_pack_id, chapter_no)
        sections = pack.get("sections") or []
        section_by_name = {section.get("name"): section for section in sections if isinstance(section, dict)}
        issues: list[dict[str, Any]] = []
        for required in ["active_rules", "current_state", "recent_summaries", "open_foreshadowing", "relevant_memory"]:
            if required not in section_by_name:
                issues.append({"severity": "error", "type": "missing_section", "section": required})

        total_tokens = sum(int(section.get("tokens_estimated") or 0) for section in sections if isinstance(section, dict))
        budget = pack.get("budget") or {}
        token_limit = int(budget.get("total_tokens") or budget.get("max_tokens") or 0)
        if token_limit and total_tokens > token_limit:
            issues.append(
                {
                    "severity": "error",
                    "type": "token_budget_exceeded",
                    "tokens_estimated": total_tokens,
                    "token_limit": token_limit,
                }
            )

        active_rules_section = section_by_name.get("active_rules")
        if active_rules_section:
            active_rules_payload = self._normalize_section_content(active_rules_section) or {}
            rules_payload = active_rules_payload.get("rules", active_rules_payload) if isinstance(active_rules_payload, dict) else active_rules_payload
            active_rules = rules_payload if isinstance(rules_payload, list) else []
            if not any(rule.get("rule_type") == "canon" for rule in active_rules if isinstance(rule, dict)):
                issues.append({"severity": "warning", "type": "missing_canon_rules", "message": "No active canon rules are present."})
            if not any(rule.get("severity") == "critical" for rule in active_rules if isinstance(rule, dict)):
                issues.append({"severity": "info", "type": "no_critical_rules", "message": "No critical guardrail rules are present."})

        for warning in pack.get("warnings") or []:
            warning_type = warning.get("type") if isinstance(warning, dict) else None
            if warning_type == "foreshadowing_overdue" and warning.get("overdue_policy") == "block":
                issues.append({"severity": "error", **warning})
            elif warning_type:
                issues.append({"severity": "warning", **warning})

        blocking_count = len([issue for issue in issues if issue.get("severity") in {"error", "blocking"}])
        return {
            "ok": blocking_count == 0,
            "context_pack_id": pack.get("id"),
            "chapter_no": pack.get("chapter_no"),
            "tokens_estimated": total_tokens,
            "token_limit": token_limit or None,
            "blocking_count": blocking_count,
            "issue_count": len(issues),
            "issues": issues,
        }

    async def preflight_generation(
        self,
        project_id: str,
        chapter_no: int,
        purpose: str,
        focus: list[str],
        budget: dict[str, Any],
        volume_no: int | None = None,
        scope_refs: list[str] | None = None,
        scope_types: list[str] | None = None,
        active_event_keys: list[str] | None = None,
        pov_mode: str = "omniscient",
    ) -> dict[str, Any]:
        pack = await self.prepare_chapter_context(
            project_id=project_id,
            chapter_no=chapter_no,
            purpose=purpose,
            focus=focus,
            budget=budget,
            volume_no=volume_no,
            scope_refs=scope_refs,
            scope_types=scope_types,
            active_event_keys=active_event_keys,
            pov_mode=pov_mode,
        )
        validation = await self.validate_context_pack(project_id, context_pack=pack)
        resolved_volume_no = (pack.get("budget") or {}).get("volume_no")
        overdue = await self._plot.check_overdue_foreshadowing(
            project_id=project_id,
            current_chapter_no=chapter_no,
            current_volume_no=resolved_volume_no,
            include_optional=False,
            limit=50,
        )
        extra_issues = []
        for item in overdue:
            severity = "error" if item.get("overdue_policy") == "block" else "warning"
            extra_issues.append(
                {
                    "severity": severity,
                    "type": "overdue_must_payoff_foreshadowing",
                    "key": item.get("key"),
                    "title": item.get("title"),
                    "overdue_policy": item.get("overdue_policy"),
                }
            )
        issues = validation["issues"] + extra_issues
        blocking_count = len([issue for issue in issues if issue.get("severity") in {"error", "blocking"}])
        return {
            "ok": blocking_count == 0,
            "context_pack": pack,
            "validation": {**validation, "issues": issues, "issue_count": len(issues), "blocking_count": blocking_count, "ok": blocking_count == 0},
            "can_generate": blocking_count == 0,
        }

    async def prepare_segment_context(
        self,
        project_id: str,
        chapter_no: int,
        segment: str,
        purpose: str,
        focus: list[str],
        budget: dict[str, Any],
        volume_no: int | None = None,
        scope_refs: list[str] | None = None,
        scope_types: list[str] | None = None,
        active_event_keys: list[str] | None = None,
        pov_mode: str = "omniscient",
    ) -> dict[str, Any]:
        segment_defaults = {
            "opening": {"recent_count": 5, "memory_limit": 10, "foreshadowing_limit": 15},
            "middle": {"recent_count": 8, "memory_limit": 20, "foreshadowing_limit": 20},
            "ending": {"recent_count": 10, "memory_limit": 15, "foreshadowing_limit": 35},
        }
        merged_budget = {**segment_defaults.get(segment, {}), **budget, "segment": segment}
        pack = await self.prepare_chapter_context(
            project_id=project_id,
            chapter_no=chapter_no,
            purpose=f"{purpose}:{segment}",
            focus=focus,
            budget=merged_budget,
            volume_no=volume_no,
            scope_refs=scope_refs,
            scope_types=scope_types,
            active_event_keys=active_event_keys,
            pov_mode=pov_mode,
        )
        guidance = {
            "segment": segment,
            "focus": focus,
            "instruction": {
                "opening": "Prioritize entry state, scene continuity, hook setup, and POV-safe information.",
                "middle": "Prioritize conflict escalation, active entity state, and relevant recent memory.",
                "ending": "Prioritize payoff checks, chapter-end hook, state deltas, and unresolved foreshadowing.",
            }.get(segment, "Use the bounded context according to the requested segment."),
        }
        sections = list(pack.get("sections") or [])
        sections.append(self._section("segment_guidance", guidance, 1))
        await self._db.execute(
            "UPDATE context_packs SET sections = $3::jsonb WHERE project_id = $1 AND id = $2",
            project_id,
            pack["id"],
            json_dumps(sections),
        )
        pack["sections"] = sections
        return pack
