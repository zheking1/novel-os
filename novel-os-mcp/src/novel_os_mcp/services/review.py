import json
import logging
import re
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value

logger = logging.getLogger("novel_os_mcp.services.review")


class ReviewService:
    """审查服务 - 处理章节审查和反馈"""

    def __init__(self, db: Database):
        self._db = db

    async def submit_for_review(
        self,
        project_id: str,
        chapter_id: str,
        reviewer_id: str | None = None,
        review_type: str = "editorial",
        priority: str = "normal",
        due_date: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO reviews
              (project_id, chapter_id, reviewer_id, review_type, priority, due_date, notes, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending')
            RETURNING id::text, project_id::text, chapter_id::text, reviewer_id::text,
                      review_type, priority, due_date, notes, status, created_at
            """,
            project_id,
            chapter_id,
            reviewer_id,
            review_type,
            priority,
            due_date,
            notes,
        )
        return row_to_dict(row)

    async def get_reviews(
        self,
        project_id: str,
        chapter_id: str | None = None,
        status: str | None = None,
        reviewer_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if chapter_id:
            conditions.append(f"chapter_id = ${idx}")
            params.append(chapter_id)
            idx += 1
        if status:
            conditions.append(f"status = ${idx}")
            params.append(status)
            idx += 1
        if reviewer_id:
            conditions.append(f"reviewer_id = ${idx}")
            params.append(reviewer_id)
            idx += 1

        params.append(limit)
        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, chapter_id::text, reviewer_id::text,
                   review_type, priority, status, due_date, notes, created_at, completed_at
            FROM reviews
            WHERE {' AND '.join(conditions)}
            ORDER BY
              CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END,
              created_at DESC
            LIMIT ${idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def update_review_status(
        self,
        review_id: str,
        status: str,
        feedback: str | None = None,
        quality_score: float | None = None,
    ) -> dict[str, Any]:
        if status == "completed":
            row = await self._db.fetchrow(
                """
                UPDATE reviews
                SET status = $2, completed_at = NOW(), feedback = COALESCE($3, feedback),
                    quality_score = COALESCE($4, quality_score)
                WHERE id = $1
                RETURNING id::text, project_id::text, chapter_id::text, reviewer_id::text,
                          review_type, priority, status, feedback, quality_score, created_at, completed_at
                """,
                review_id,
                status,
                feedback,
                quality_score,
            )
        else:
            row = await self._db.fetchrow(
                """
                UPDATE reviews SET status = $2 WHERE id = $1
                RETURNING id::text, project_id::text, chapter_id::text, reviewer_id::text,
                          review_type, priority, status, created_at
                """,
                review_id,
                status,
            )
        return row_to_dict(row) if row else {}

    async def get_review_feedback(
        self,
        review_id: str,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, review_id::text, feedback_type, content, location_ref,
                   severity, status, created_at
            FROM review_feedback
            WHERE review_id = $1
            ORDER BY created_at
            """,
            review_id,
        )
        return rows_to_dicts(rows)

    async def add_review_feedback(
        self,
        review_id: str,
        feedback_type: str,
        content: str,
        location_ref: str | None = None,
        severity: str = "info",
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO review_feedback (review_id, feedback_type, content, location_ref, severity)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id::text, review_id::text, feedback_type, content, location_ref,
                      severity, status, created_at
            """,
            review_id,
            feedback_type,
            content,
            location_ref,
            severity,
        )
        return row_to_dict(row)

    async def update_feedback_status(
        self,
        feedback_id: str,
        status: str,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            UPDATE review_feedback SET status = $2 WHERE id = $1
            RETURNING id::text, review_id::text, feedback_type, content, location_ref,
                      severity, status, created_at
            """,
            feedback_id,
            status,
        )
        return row_to_dict(row) if row else {}

    async def get_pending_review_count(self, project_id: str) -> int:
        row = await self._db.fetchrow(
            """
            SELECT COUNT(*)::int AS cnt
            FROM reviews
            WHERE project_id = $1 AND status IN ('pending', 'in_progress')
            """,
            project_id,
        )
        return row["cnt"] if row else 0

    async def get_overdue_reviews(self, project_id: str) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, project_id::text, chapter_id::text, reviewer_id::text,
                   review_type, priority, status, due_date, created_at
            FROM reviews
            WHERE project_id = $1 AND status IN ('pending', 'in_progress')
              AND due_date < NOW()
            ORDER BY due_date
            """,
            project_id,
        )
        return rows_to_dicts(rows)

    async def _gather_review_context(self, project_id: str, chapter_no: int) -> dict[str, str]:
        """收集审核所需的上下文：角色、伏笔、规则、世界状态等。"""
        ctx = {}

        # 前三章摘要
        summaries = await self._db.fetch(
            "SELECT c.chapter_no, s.content FROM chapter_summaries s JOIN chapters c ON c.id = s.chapter_id WHERE s.project_id = $1 ORDER BY c.chapter_no DESC LIMIT 3",
            project_id,
        )
        ctx["previous_summaries"] = "\n".join([f"第{s['chapter_no']}章: {s['content'][:300]}" for s in summaries]) if summaries else "（无）"

        # 角色状态
        chars = await self._db.fetch(
            "SELECT name, profile FROM state_entities WHERE project_id = $1 AND entity_type = 'character' AND lifecycle_status = 'active' LIMIT 10",
            project_id,
        )
        ctx["character_states"] = "\n".join([
            f"{c['name']}: {ensure_json_value(c.get('profile') or {}).get('personality', '')[:100]}"
            for c in chars
        ]) if chars else "（无活跃角色）"

        # 活跃伏笔
        foreshadow = await self._db.fetch(
            "SELECT title, status, importance, expected_payoff_range FROM foreshadowing WHERE project_id = $1 AND is_deleted = false AND status NOT IN ('paid_off', 'abandoned', 'archived') LIMIT 15",
            project_id,
        )
        ctx["foreshadowings"] = "\n".join([f"  {f['title']} ({f['status']}, {f['importance']})" for f in foreshadow]) if foreshadow else "（无）"

        # 活跃规则
        rules = await self._db.fetch(
            "SELECT title, content, severity FROM canon_rules WHERE project_id = $1 AND status = 'active' LIMIT 15",
            project_id,
        )
        ctx["rules"] = "\n".join([f"  [{r['severity']}] {r['title']}: {r['content'][:200]}" for r in rules]) if rules else "（无）"

        # 世界状态
        world = await self._db.fetchrow(
            "SELECT world_state, story_era FROM world_snapshots WHERE project_id = $1 ORDER BY chapter_no DESC LIMIT 1",
            project_id,
        )
        if world:
            ws = ensure_json_value(world.get("world_state") or {})
            ctx["world_state"] = f"时代: {world['story_era'] or '未知'} | 世界状态: {json.dumps(ws, ensure_ascii=False)[:300]}"
        else:
            ctx["world_state"] = "（无）"

        return ctx

    async def _get_council_models(self, username: str) -> list[str]:
        """获取活跃审核委员会的模型列表。"""
        council = await self._db.fetchrow(
            "SELECT config FROM review_council_configs WHERE user_id = $1 AND is_active = true ORDER BY created_at DESC LIMIT 1",
            username,
        )
        if not council:
            return []
        cfg = council["config"]
        if isinstance(cfg, str):
            cfg = json.loads(cfg)
        reviewers = cfg.get("reviewers", cfg.get("models", []))
        return [r["model"] for r in reviewers if isinstance(r, dict) and r.get("model")]

    async def _create_review_job_record(self, project_id: str, chapter_no: int, dimensions: list[str], session_id: str) -> dict:
        """创建一个 review_job 记录，关联讨论室会话。"""
        ch = await self._db.fetchrow("SELECT id FROM chapters WHERE project_id = $1 AND chapter_no = $2", project_id, chapter_no)
        chapter_id = ch["id"] if ch else None
        row = await self._db.fetchrow(
            """INSERT INTO review_jobs (project_id, chapter_id, chapter_no, status, config, session_id)
               VALUES ($1, $2, $3, 'running', $4::jsonb, $5)
               RETURNING id::text as job_id""",
            project_id, chapter_id, chapter_no,
            json.dumps({"dimensions": dimensions, "report_count": 0, "avg_score": 0}),
            session_id,
        )
        return dict(row) if row else {"job_id": "unknown"}

    async def start_job(self, **kwargs) -> dict[str, Any]:
        """启动审核任务"""
        logger.info(f"start_job called with: {kwargs}")
        project_id = kwargs.get('project_id')
        chapter_no = kwargs.get('chapter_no')
        dimensions = kwargs.get('dimensions', [])
        username = kwargs.get('username')

        # 强制检查：必须有活跃的审核委员会配置
        council = await self._db.fetchrow(
            "SELECT id, config FROM review_council_configs WHERE user_id = $1 AND is_active = true ORDER BY created_at DESC LIMIT 1",
            username,
        )
        if not council:
            raise ValueError("审核委员会未配置或未激活。请在 Web UI → 审核页面 → 审核委员会配置 中创建并激活配置后再试。")
        council_config = council["config"]
        if isinstance(council_config, str):
            import json
            council_config = json.loads(council_config)
        reviewers = council_config.get("reviewers", council_config.get("models", []))
        if len(reviewers) < 2:
            raise ValueError(f"审核委员会至少需要 2 个模型（当前 {len(reviewers)} 个），请在 Web UI 中完善配置。")

        chapter = await self._db.fetchrow(
            "SELECT id FROM chapters WHERE project_id = $1 AND chapter_no = $2",
            project_id, chapter_no
        )
        if not chapter:
            vol_row = await self._db.fetchrow(
                "SELECT volume_no FROM volumes WHERE project_id = $1 AND start_chapter_no <= $2 AND (end_chapter_no IS NULL OR end_chapter_no >= $2) LIMIT 1",
                project_id, chapter_no,
            )
            volume_no = vol_row["volume_no"] if vol_row else 1
            chapter = await self._db.fetchrow(
                "INSERT INTO chapters (project_id, chapter_no, title, volume_no, status) VALUES ($1, $2, $3, $4, 'draft') RETURNING id",
                project_id, chapter_no, f"第{chapter_no}章", volume_no,
            )

        user_id = None
        if username:
            row = await self._db.fetchrow("SELECT id::text FROM users WHERE username = $1", username)
            if row:
                user_id = row['id']

        job = await self._db.fetchrow(
            """
            INSERT INTO review_jobs (project_id, chapter_id, status, config, created_by)
            VALUES ($1, $2, 'pending', $3::jsonb, $4::uuid)
            RETURNING id::text, project_id::text, status, created_at
            """,
            project_id, chapter['id'],
            json_dumps({"dimensions": dimensions, "local_files": kwargs.get('local_files', [])}),
            user_id
        )
        return {"job_id": job['id'], "status": job['status'], "chapter_no": chapter_no}

    async def upsert_council_config(self, **kwargs) -> dict[str, Any]:
        logger.info(f"upsert_council_config called with: {kwargs}")
        user_id = kwargs.get("user_id")
        name = kwargs.get("name", "默认审核委员会")
        config = kwargs.get("config", {})
        is_active = kwargs.get("is_active", False)

        if not user_id:
            raise ValueError("user_id is required")

        existing = await self._db.fetchrow(
            "SELECT id FROM review_council_configs WHERE user_id = $1 AND name = $2",
            user_id, name,
        )

        if existing:
            await self._db.execute(
                "UPDATE review_council_configs SET config = $1::jsonb, is_active = $2, updated_at = now() WHERE id = $3",
                json_dumps(config), is_active, existing["id"],
            )
        else:
            await self._db.execute(
                "INSERT INTO review_council_configs (user_id, project_id, name, config, is_active) VALUES ($1, NULL, $2, $3::jsonb, $4)",
                user_id, name, json_dumps(config), is_active,
            )
        return {"success": True, "name": name}

    async def list_council_configs(self, **kwargs) -> list[dict[str, Any]]:
        logger.info(f"list_council_configs called with: {kwargs}")
        user_id = kwargs.get("user_id")
        if user_id:
            rows = await self._db.fetch(
                "SELECT id::text, user_id, name, config, is_active, created_at, updated_at FROM review_council_configs WHERE user_id = $1 ORDER BY created_at DESC",
                user_id,
            )
        else:
            rows = await self._db.fetch(
                "SELECT id::text, user_id, project_id, name, config, is_active, created_at, updated_at FROM review_council_configs ORDER BY created_at DESC",
            )
        result = []
        for r in rows:
            item = dict(r)
            cfg = item.get("config")
            if isinstance(cfg, str):
                item["config"] = json.loads(cfg)
            elif cfg is None:
                item["config"] = {}
            result.append(item)
        return result

    async def get_council_dispatch(self, **kwargs) -> dict[str, Any]:
        logger.info(f"get_council_dispatch called with: {kwargs}")
        username = kwargs.get("username")
        review_job_id = kwargs.get("review_job_id")
        if not username:
            return {"status": "error", "models": [], "count": 0, "message": "缺少 username"}
        council = await self._db.fetchrow(
            "SELECT config FROM review_council_configs WHERE user_id = $1 AND is_active = true ORDER BY created_at DESC LIMIT 1",
            username,
        )
        if not council:
            return {"status": "no_council", "models": [], "count": 0, "message": "未找到活跃的审核委员会"}
        cfg = council["config"]
        if isinstance(cfg, str):
            cfg = json.loads(cfg)
        reviewers = cfg.get("reviewers", cfg.get("models", []))
        return {"status": "ok", "models": reviewers, "count": len(reviewers)}

    async def list_jobs(self, project_id: str, status: str = "active", limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """SELECT id::text, project_id::text, chapter_id::text, status,
                      dimensions, models, report_count, avg_score, pass_status, created_at, updated_at
               FROM review_jobs WHERE project_id = $1 AND ($2::text IS NULL OR status = $2)
               ORDER BY created_at DESC LIMIT $3 OFFSET $4""",
            project_id, status, limit, offset,
        )
        result = []
        for r in rows:
            d = dict(r)
            ch = await self._db.fetchrow("SELECT chapter_no FROM chapters WHERE id = $1", r["chapter_id"])
            d["chapter_no"] = ch["chapter_no"] if ch else None
            result.append(d)
        return result

    async def submit_model_report(self, **kwargs) -> dict[str, Any]:
        logger.info(f"submit_model_report called")
        project_id = kwargs.get('project_id')
        review_job_id = kwargs.get('review_job_id')
        model_id = kwargs.get('model_id')
        content = kwargs.get('content')
        score_given = kwargs.get('score')
        summary_given = kwargs.get('summary', '')
        findings_given = kwargs.get('findings', [])
        local_report_file = kwargs.get('local_report_file')

        # Get chapter_id from review_job
        job = await self._db.fetchrow(
            "SELECT chapter_id FROM review_jobs WHERE id = $1", review_job_id
        )
        if not job:
            raise ValueError(f"Review job {review_job_id} not found")
        chapter_id = job['chapter_id']

        # 如果传了 content → 系统自动调 LLM 审核
        if content:
            result = await self._auto_review(project_id, model_id, content)
            score = result.get("score", 70)
            summary = result.get("summary", "")
            findings = result.get("findings", [])
        else:
            score = score_given
            summary = summary_given
            findings = findings_given

        row = await self._db.fetchrow(
            """
            INSERT INTO review_reports (project_id, review_job_id, chapter_id, model_id,
                                        report_type, score, findings, summary)
            VALUES ($1, $2, $3, $4, 'model', $5, $6::jsonb, $7)
            RETURNING id::text
            """,
            project_id, review_job_id, chapter_id, model_id,
            score, json_dumps(findings), summary,
        )
        logger.info("Stored model report %s for model %s (score=%s)", row['id'], model_id, score)
        return {
            "success": True,
            "report_id": row['id'],
            "score": score,
            "summary": summary,
            "findings": findings,
        }

    async def _auto_review(self, project_id: str, model_id: str, content: str) -> dict[str, Any]:
        """Auto-review content by calling the configured LLM with gathered context."""
        from ..deps import llm_client

        # 1. 获取模型在委员会中的焦点（用户级，不限制project）
        council = await self._db.fetchrow(
            "SELECT config FROM review_council_configs WHERE is_active = true ORDER BY created_at DESC LIMIT 1"
        )
        focus = ""
        if council:
            cfg = council["config"]
            if isinstance(cfg, str):
                cfg = json.loads(cfg)
            for r in cfg.get("reviewers", []):
                if r.get("model") == model_id:
                    focus = r.get("focus", "")
                    break

        # 2. 拉取上下文
        summaries = await self._db.fetch(
            "SELECT c.chapter_no, s.content FROM chapter_summaries s JOIN chapters c ON c.id = s.chapter_id WHERE s.project_id = $1 ORDER BY c.chapter_no DESC LIMIT 3",
            project_id,
        )
        summary_text = "\n".join([f"第{s['chapter_no']}章: {s['content'][:200]}" for s in summaries]) if summaries else "（无前章数据）"

        rules = await self._db.fetch(
            "SELECT title, content, severity FROM canon_rules WHERE project_id = $1 AND status = 'active' LIMIT 10",
            project_id,
        )
        rule_text = "\n".join([f"  [{r['severity']}] {r['title']}: {r['content'][:200]}" for r in rules]) if rules else "（无活跃规则）"

        # 角色状态（提取正文中可能出现的角色）
        import re
        char_names = re.findall(r'[\u4e00-\u9fa5]{2,4}(?:哥|姐|弟|妹|兄|伯|爷|娘|生|军|主|爷|姐|叔)', content)
        if not char_names:
            char_names = re.findall(r'[\u4e00-\u9fa5]{2,4}', content[:200])
            char_names = list(set(char_names))[:5]
        char_text = ""
        for name in list(set(char_names))[:5]:
            row = await self._db.fetchrow(
                "SELECT name, profile FROM state_entities WHERE project_id = $1 AND name LIKE $2 AND entity_type = 'character' LIMIT 1",
                project_id, f"%{name}%",
            )
            if row:
                profile = ensure_json_value(row.get("profile") or {})
                char_text += f"  {row['name']}: {profile.get('personality', '')} | {profile.get('background', '')[:100]}\n"

        # 伏笔
        foreshadow = await self._db.fetch(
            "SELECT title, status, importance, expected_payoff_range FROM foreshadowing WHERE project_id = $1 AND is_deleted = false AND status NOT IN ('paid_off', 'abandoned', 'archived') LIMIT 10",
            project_id,
        )
        foreshadow_text = "\n".join([f"  {f['title']} ({f['status']}, {f['importance']})" for f in foreshadow]) if foreshadow else "（无活跃伏笔）"

        # 世界状态
        world = await self._db.fetchrow(
            "SELECT world_state, story_era, story_time FROM world_snapshots WHERE project_id = $1 ORDER BY chapter_no DESC LIMIT 1",
            project_id,
        )
        world_text = "（无世界状态）"
        if world:
            ws = ensure_json_value(world.get("world_state") or {})
            world_text = f"时代: {world['story_era'] or '未知'} | {json.dumps(ws, ensure_ascii=False)[:200]}"

        # 文风
        style = await self._db.fetchrow(
            "SELECT profile_name, narrative_pov, tense, tone FROM style_profiles WHERE project_id = $1 LIMIT 1",
            project_id,
        )
        style_text = "（未配置文风档案）"
        if style:
            style_text = f"视角: {style['narrative_pov']} | 时态: {style['tense']} | 基调: {style['tone']}"

        # 3. 构建审核提示词
        prompt = f"""你是一个专业的小说章节审核员。请根据以下上下文和审核要求，对本章正文进行多维度的质量评估。

【前情摘要】
{summary_text}

【角色状态】
{char_text if char_text else "（本章角色未在已有实体表中找到，请根据正文自行判断）"}

【活跃伏笔】
{foreshadow_text}

【活跃规则】
{rule_text}

【世界观状态】
{world_text}

【文风基线】
{style_text}

【待审正文摘要】
{content[:2500]}

【审核要求】
从以下维度评估，每个维度 0-100。

{self._build_dimension_instructions(focus)}

额外：AI痕迹检测。

输出JSON：
{{"score":0,"summary":"","findings":[{{"severity":"warning","category":"","message":"","suggestion":""}}]}}"""
        try:
            result = await llm_client.chat(project_id, "review", [
                {"role": "system", "content": "你是一个专业的小说章节审核员，请严格按JSON格式输出。"},
                {"role": "user", "content": prompt},
            ], temperature=0.3, max_tokens=2048)

            text = result.get("text", "").strip()
            json_match = re.search(r'\{.*"score".*\}', text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    return {"score": parsed.get("score", 70), "summary": parsed.get("summary", text[:200]), "findings": parsed.get("findings", [])}
                except json.JSONDecodeError:
                    pass
            # Fallback: try to find score number
            score_match = re.search(r'(\d{1,3})', text)
            score = min(100, int(score_match.group(1))) if score_match else 60
            return {"score": score, "summary": text[:200], "findings": []}

        except Exception as e:
            logger.warning("LLM review failed for %s: %s", model_id, e)
            return {"score": 50, "summary": f"审核模型异常", "findings": [{"severity": "warning", "category": "system", "message": "自动审核异常，建议人工复核", "suggestion": ""}]}

    def _build_dimension_instructions(self, focus: str) -> str:
        """Build per-model dimension instructions based on focus."""
        dims = {
            "情节": """1. 情节连贯性 - 与前章衔接、伏笔推进、线程进展
   - 本章情节与前章是否有逻辑断层？
   - 已有伏笔是否有推进或回收？
   - 剧情线程（主线/支线）是否有进展？""",
            "角色": """2. 角色一致性 - 行为是否符合设定
   - 角色言行是否与其性格、背景、动机一致？
   - 角色关系变化是否合理？
   - 是否有OOC（脱离角色）的情况？""",
            "文风": """3. 文风一致性 - 语言风格是否匹配
   - 叙事视角是否统一？
   - 语言风格（书面/口语、简洁/华丽）是否与前文一致？
   - 专有名词用法是否正确？""",
            "设定": """4. 设定合规性 - 是否违反世界观规则
   - 是否有与已建立设定矛盾的描述？
   - 是否违反了活跃的创作规则？
   - 世界状态是否被正确反映？""",
            "节奏": """5. 节奏合理性 - 紧张度曲线与结构
   - 本章的起承转合是否完整？
   - 紧张度变化是否合理？
   - 章节长度是否符合预期（2500-4000字）？""",
            "逻辑": """6. 逻辑自洽性 - 时间线、因果、物理规则
   - 事件发生的因果链是否合理？
   - 时间线是否有矛盾？
   - 是否有逻辑漏洞？""",
        }
        instructions = []
        used = []
        # Map focus keywords to dimension names
        f_lower = focus.lower()
        for kw, dim_text in dims.items():
            if kw in f_lower:
                instructions.append(dim_text)
                used.append(kw)
        # If focus didn't match any dimension, assign all
        if not instructions:
            for _, dim_text in dims.items():
                instructions.append(dim_text)
        # Add any dimensions not yet covered
        for kw, dim_text in dims.items():
            if kw not in used:
                instructions.append(dim_text)
        return "\n".join(instructions)

    async def learn_from_review(
        self,
        project_id: str,
        review_job_id: str,
        username: str,
        create_revision_tasks: bool = True,
        create_rule_proposals: bool = True,
        block_on_critical: bool = True,
    ) -> dict[str, Any]:
        """从审核结果中学习。自动创建修订任务和规则提案。"""
        logger.info("learn_from_review: job=%s", review_job_id)

        # 汇总审核结果
        agg_result = await self.aggregate(
            project_id=project_id,
            review_job_id=review_job_id,
            create_revision_tasks=create_revision_tasks,
        )

        # 提取规则提案
        rule_result = await self.extract_rule_proposals(
            project_id=project_id,
            review_job_id=review_job_id,
            username=username,
            create_proposals=create_rule_proposals,
        )

        # 提取状态更新建议
        state_result = await self.extract_state_updates(
            project_id=project_id,
            review_job_id=review_job_id,
        )

        # 提取伏笔更新建议
        foreshadowing_result = await self.extract_foreshadowing_updates(
            project_id=project_id,
            review_job_id=review_job_id,
        )

        # 更新审核任务状态
        await self._db.execute(
            "UPDATE review_jobs SET status = 'aggregated', updated_at = now() WHERE project_id = $1 AND id = $2",
            project_id, review_job_id,
        )

        return {
            "review_job_id": review_job_id,
            "aggregated": agg_result,
            "rule_proposals": rule_result,
            "state_updates": state_result,
            "foreshadowing_updates": foreshadowing_result,
        }

    async def list_revision_tasks(self, **kwargs) -> list[dict[str, Any]]:
        logger.info(f"list_revision_tasks called with: {kwargs}")
        project_id = kwargs.get("project_id")
        review_job_id = kwargs.get("task_id") or kwargs.get("review_job_id")
        status = kwargs.get("status")
        limit = kwargs.get("limit", 100)

        if review_job_id:
            rows = await self._db.fetch(
                """SELECT rj.id::text, rj.project_id::text, rj.chapter_id::text, rj.status,
                          rj.config->>'dimensions' AS dimensions,
                          rj.created_by::text, rj.created_at, rj.updated_at,
                          c.chapter_no,
                          (SELECT COUNT(*) FROM review_reports rr WHERE rr.review_job_id = rj.id) AS report_count,
                          (SELECT ROUND(AVG(rr.score)::numeric, 1) FROM review_reports rr WHERE rr.review_job_id = rj.id AND rr.score IS NOT NULL) AS avg_score,
                          (SELECT string_agg(DISTINCT rr.model_id, ', ') FROM review_reports rr WHERE rr.review_job_id = rj.id) AS models,
                          (SELECT COALESCE(
                            '[' || string_agg(
                              jsonb_build_object(
                                'model_id', rr.model_id,
                                'score', rr.score,
                                'summary', rr.summary,
                                'findings', rr.findings,
                                'report_type', rr.report_type
                              )::text, ','
                            ) || ']', '[]'
                           ) FROM review_reports rr WHERE rr.review_job_id = rj.id) AS reports
                   FROM review_jobs rj
                   LEFT JOIN chapters c ON c.id = rj.chapter_id
                   WHERE rj.id = $1""",
                review_job_id,
            )
        elif project_id:
            conditions = ["rj.project_id = $1"]
            params = [project_id]
            idx = 2
            if status:
                conditions.append(f"rj.status = ${idx}")
                params.append(status)
                idx += 1
            rows = await self._db.fetch(
                f"""SELECT rj.id::text, rj.project_id::text, rj.chapter_id::text, rj.status,
                           rj.config->>'dimensions' AS dimensions,
                           rj.created_by::text, rj.created_at, rj.updated_at,
                           c.chapter_no,
                           (SELECT COUNT(*) FROM review_reports rr WHERE rr.review_job_id = rj.id) AS report_count,
                           (SELECT ROUND(AVG(rr.score)::numeric, 1) FROM review_reports rr WHERE rr.review_job_id = rj.id AND rr.score IS NOT NULL) AS avg_score,
                           (SELECT string_agg(DISTINCT rr.model_id, ', ') FROM review_reports rr WHERE rr.review_job_id = rj.id) AS models,
                           (SELECT rr.summary FROM review_reports rr WHERE rr.review_job_id = rj.id AND rr.summary IS NOT NULL LIMIT 1) AS summary
                    FROM review_jobs rj
                    LEFT JOIN chapters c ON c.id = rj.chapter_id
                    WHERE {' AND '.join(conditions)}
                    ORDER BY rj.created_at DESC LIMIT ${idx} OFFSET ${idx+1}""",
                *params, limit, kwargs.get("offset", 0),
            )
        else:
            return []
        return [dict(r) for r in rows]

    async def update_revision_task(self, **kwargs) -> dict[str, Any]:
        logger.info(f"update_revision_task called with: {kwargs}")
        return {"success": True}

    async def aggregate(self, **kwargs) -> dict[str, Any]:
        logger.info(f"aggregate called")
        project_id = kwargs.get('project_id')
        review_job_id = kwargs.get('review_job_id')
        create_revision_tasks = kwargs.get('create_revision_tasks', True)

        # Get all reports for this job
        reports = await self._db.fetch(
            "SELECT * FROM review_reports WHERE review_job_id = $1 ORDER BY created_at",
            review_job_id,
        )

        if not reports:
            return {"success": True, "evolution_proposals": [], "message": "暂无审查报告"}

        # 强制检查：所有委员会成员是否都已提交报告
        council = await self._db.fetchrow(
            "SELECT config FROM review_council_configs WHERE is_active = true ORDER BY created_at DESC LIMIT 1"
        )
        if council:
            cfg = council["config"]
            if isinstance(cfg, str):
                cfg = json.loads(cfg)
            expected_models = {r.get("model") for r in cfg.get("reviewers", [])}
            submitted_models = {r.get("model_id") for r in reports}
            missing = expected_models - submitted_models
            if missing:
                raise ValueError(
                    f"审核委员会尚有 {len(missing)} 个模型未提交报告（{', '.join(sorted(missing))}），"
                    f"请先调用 review.submit_model_report 为每个模型提交后再汇总。"
                )

        # Collect all findings across models
        all_findings = []
        consensus_scores = []
        for r in reports:
            findings = ensure_json_value(r['findings']) if hasattr(r, 'findings') else (r.get('findings') or [])
            if isinstance(findings, list):
                all_findings.extend(findings)
            if r.get('score') is not None:
                consensus_scores.append(float(r['score']))

        # Calculate consensus score
        avg_score = sum(consensus_scores) / len(consensus_scores) if consensus_scores else 0

        # Auto-generate evolution proposals from findings
        evolution_proposals = await self._extract_evolution_from_findings(
            project_id=project_id,
            review_job_id=review_job_id,
            findings=all_findings,
        )

        # Create revision tasks for critical issues
        revision_tasks_created = 0
        if create_revision_tasks:
            for f in all_findings:
                severity = f.get('severity', 'info')
                if severity in ('critical', 'high'):
                    await self._db.execute(
                        """
                        INSERT INTO revision_tasks (project_id, review_job_id, title, description, severity, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                        """,
                        project_id, review_job_id,
                        f.get('title', f.get('type', '审查问题')),
                        f.get('detail', f.get('description', '')),
                        severity,
                        json_dumps({"finding": f, "source_model": f.get('model_id')}),
                    )
                    revision_tasks_created += 1

        # Mark job as aggregated
        await self._db.execute(
            "UPDATE review_jobs SET status = 'aggregated', aggregated_at = now() WHERE id = $1",
            review_job_id,
        )

        return {
            "success": True,
            "consensus_score": round(avg_score, 2),
            "models_count": len(reports),
            "findings_count": len(all_findings),
            "revision_tasks_created": revision_tasks_created,
            "evolution_proposals": evolution_proposals,
        }

    async def _extract_evolution_from_findings(
        self, project_id: str, review_job_id: str, findings: list[dict],
    ) -> list[dict]:
        """From review findings, auto-extract evolution proposals for system knowledge."""
        proposals = []

        for f in findings:
            ftype = f.get('type', '')
            title = f.get('title', f.get('type', '未知问题'))
            detail = f.get('detail', f.get('description', ''))
            severity = f.get('severity', 'info')

            # Rule proposals: recurring patterns, style violations, compliance issues
            if ftype in ('style_drift', 'compliance_violation', 'rule_conflict', 'pattern_violation'):
                proposals.append({
                    "title": f"规则建议: {title}",
                    "description": detail,
                    "proposal_type": "create",
                    "target_entity_type": "setting_item",
                    "proposed_content": {
                        "category": "review-rules",
                        "title": title,
                        "core_summary": detail,
                        "level": severity == 'critical' and 'defect_compensation' or 'reminder',
                        "ai_instruction": detail,
                    },
                    "evolution_reason": f"多模型审查中发现: {detail}",
                    "source_model": f.get('model_id', 'ai_reviewer'),
                    "evidence": {"finding": f},
                })

            # Character state update proposals
            elif ftype in ('ooc', 'character_inconsistency', 'personality_drift'):
                entity_name = f.get('entity_name', '')
                if entity_name:
                    proposals.append({
                        "title": f"角色更新建议: {entity_name}",
                        "description": detail,
                        "proposal_type": "update",
                        "target_entity_type": "knowledge_item",
                        "proposed_content": {
                            "entity_type": "character",
                            "name": entity_name,
                            "suggested_update": detail,
                        },
                        "evolution_reason": f"角色一致性审查: {detail}",
                        "source_model": f.get('model_id', 'ai_reviewer'),
                        "evidence": {"finding": f},
                    })

            # Pacing/rhythm proposals
            elif ftype in ('pacing_issue', 'rhythm_problem', 'engagement_drop'):
                proposals.append({
                    "title": f"节奏建议: {title}",
                    "description": detail,
                    "proposal_type": "create",
                    "target_entity_type": "setting_item",
                    "proposed_content": {
                        "category": "rhythm-points",
                        "title": title,
                        "core_summary": detail,
                        "level": "reminder",
                    },
                    "evolution_reason": f"节奏审查中发现: {detail}",
                    "source_model": f.get('model_id', 'ai_reviewer'),
                    "evidence": {"finding": f},
                })

        return proposals

    async def submit_evolution_proposals_from_review(
        self, project_id: str, review_job_id: str, findings: list[dict],
    ) -> dict[str, Any]:
        """将审查发现中的可进化内容提交为系统进化提案。"""
        evolution_proposals = await self._extract_evolution_from_findings(
            project_id=project_id,
            review_job_id=review_job_id,
            findings=findings,
        )

        submitted = 0
        for prop in evolution_proposals:
            target_entity_type = prop.get("target_entity_type", "setting_item")
            try:
                row = await self._db.fetchrow(
                    """
                    INSERT INTO system_evolution_proposals
                        (title, description, proposal_type, target_entity_type,
                         proposed_content, evolution_reason, source_project_id,
                         ai_submitter, evidence, status)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9::jsonb, 'applied')
                    RETURNING id
                    """,
                    prop["title"],
                    prop["description"],
                    prop.get("proposal_type", "create"),
                    target_entity_type,
                    json_dumps(prop.get("proposed_content", {})),
                    prop.get("evolution_reason", ""),
                    project_id,
                    prop.get("source_model", "ai_reviewer"),
                    json_dumps(prop.get("evidence", {})),
                )
                submitted += 1
            except Exception as exc:
                logger.warning("Failed to submit evolution proposal: %s", exc)
        return {
                "ok": True,
                "submitted": submitted,
                "discussion_trigger": {
                    "tool": "discussion_room.create_session",
                    "topic": f"审查进化提案（{submitted}条）。" +
                             "请逐条讨论是否应应用于系统。共识后输出JSON：" +
                             "style_drift/rhythm → type=setting/category=review-rules，" +
                             "OOC/角色不一致 → type=entity/entity_type=character，" +
                             "规则冲突/合规违规 → type=rule/rule_type=creative，" +
                             "可直接升级为全局 → type=global_rule/rule_type=creative。" +
                             "有异议则否决不写入。",
                    "data_source": "review_evolution",
                },
            }

    async def extract_rule_proposals(self, **kwargs) -> list[dict[str, Any]]:
        logger.info(f"extract_rule_proposals called")
        review_job_id = kwargs.get('review_job_id')
        project_id = kwargs.get('project_id')
        username = kwargs.get('username')
        create_proposals = kwargs.get('create_proposals', True)
        min_confidence = kwargs.get('min_confidence', 0.0)

        # Get all reports for this job
        reports = await self._db.fetch(
            "SELECT * FROM review_reports WHERE review_job_id = $1", review_job_id
        )

        proposals = []
        for r in reports:
            findings = ensure_json_value(r['findings']) if isinstance(r.get('findings'), str) else (r.get('findings') or [])
            if not isinstance(findings, list):
                continue
            for f in findings:
                ftype = f.get('type', '')
                if ftype in ('style_drift', 'compliance_violation', 'rule_conflict', 'pattern_violation'):
                    title = f.get('title', f.get('type', '规则提案'))
                    detail = f.get('detail', f.get('description', ''))
                    confidence = min(f.get('confidence', 0.5), 1.0)
                    if confidence < min_confidence:
                        continue

                    model_id = f.get('model_id') or r.get('model_id') or 'ai_reviewer'
                    prop = {
                        "title": title,
                        "content": detail,
                        "proposal_type": "style" if ftype == 'style_drift' else
                                        "canon" if ftype == 'compliance_violation' else "lesson",
                        "confidence": confidence,
                        "source_model_id": model_id,
                        "source_finding_key": f.get('id', f.get('key', '')),
                    }

                    if create_proposals:
                        await self._db.execute(
                            """
                            INSERT INTO rule_proposals
                                (project_id, review_job_id, proposal_type, title, content,
                                 confidence, source_model_id, source_finding_key, status)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending')
                            """,
                            project_id, review_job_id,
                            prop["proposal_type"], prop["title"], prop["content"],
                            prop["confidence"], prop["source_model_id"], prop["source_finding_key"],
                        )

                    proposals.append(prop)

        return proposals

    async def extract_state_updates(self, **kwargs) -> list[dict[str, Any]]:
        logger.info(f"extract_state_updates called")
        review_job_id = kwargs.get('review_job_id')
        project_id = kwargs.get('project_id')

        reports = await self._db.fetch(
            "SELECT * FROM review_reports WHERE review_job_id = $1", review_job_id
        )

        updates = []
        for r in reports:
            findings = ensure_json_value(r['findings']) if isinstance(r.get('findings'), str) else (r.get('findings') or [])
            if not isinstance(findings, list):
                continue
            for f in findings:
                if f.get('type') in ('ooc', 'character_inconsistency', 'personality_drift'):
                    entity_name = f.get('entity_name', '')
                    if entity_name:
                        updates.append({
                            "entity_name": entity_name,
                            "entity_type": "character",
                            "suggested_state_change": f.get('detail', f.get('description', '')),
                            "reason": f.get('title', ''),
                            "severity": f.get('severity', 'info'),
                        })

        return updates

    async def extract_foreshadowing_updates(self, **kwargs) -> list[dict[str, Any]]:
        logger.info(f"extract_foreshadowing_updates called")
        review_job_id = kwargs.get('review_job_id')
        project_id = kwargs.get('project_id')

        reports = await self._db.fetch(
            "SELECT * FROM review_reports WHERE review_job_id = $1", review_job_id
        )

        updates = []
        for r in reports:
            findings = ensure_json_value(r['findings']) if isinstance(r.get('findings'), str) else (r.get('findings') or [])
            if not isinstance(findings, list):
                continue
            for f in findings:
                if f.get('type') in ('unresolved_thread', 'dangling_foreshadowing', 'missed_payoff'):
                    updates.append({
                        "foreshadowing_key": f.get('key', ''),
                        "suggested_action": f.get('suggested_action', 'payoff'),
                        "description": f.get('detail', f.get('description', '')),
                        "suggested_chapter": f.get('suggested_chapter_no'),
                        "reason": f.get('title', ''),
                    })

        return updates

    async def evaluate_model_quality(self, **kwargs) -> dict[str, Any]:
        logger.info(f"evaluate_model_quality called with: {kwargs}")
        return {"score": 0, "metrics": {}}

    async def extract_evolution_proposals(self, project_id: str, review_job_id: str, findings: list) -> list[dict[str, Any]]:
        logger.info(f"extract_evolution_proposals called")
        return []


class RuleProposalService:
    """规则提案服务 - 管理规则提案和投票"""

    def __init__(self, db: Database):
        self._db = db

    async def create_proposal(
        self,
        project_id: str,
        proposed_by: str,
        title: str,
        description: str,
        category: str = "quality",
        priority: str = "normal",
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO rule_proposals
              (project_id, proposed_by, title, description, category, priority, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'open')
            RETURNING id::text, project_id::text, proposed_by, title, description,
                      category, priority, status, created_at
            """,
            project_id,
            proposed_by,
            title,
            description,
            category,
            priority,
        )
        return row_to_dict(row)

    async def get_proposals(
        self,
        project_id: str,
        status: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if status:
            conditions.append(f"status = ${idx}")
            params.append(status)
            idx += 1
        if category:
            conditions.append(f"category = ${idx}")
            params.append(category)
            idx += 1

        params.append(limit)
        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, proposed_by, title, description,
                   category, priority, status, created_at, resolved_at
            FROM rule_proposals
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT ${idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def vote_proposal(
        self,
        proposal_id: str,
        voter_id: str,
        vote: str,
        comment: str | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO rule_proposal_votes (proposal_id, voter_id, vote, comment)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (proposal_id, voter_id) DO UPDATE SET vote = $3, comment = $4
            RETURNING id::text, proposal_id::text, voter_id, vote, comment, created_at
            """,
            proposal_id,
            voter_id,
            vote,
            comment,
        )
        return row_to_dict(row)

    async def get_proposal_votes(
        self,
        proposal_id: str,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, proposal_id::text, voter_id, vote, comment, created_at
            FROM rule_proposal_votes
            WHERE proposal_id = $1
            ORDER BY created_at
            """,
            proposal_id,
        )
        return rows_to_dicts(rows)

    async def resolve_proposal(
        self,
        proposal_id: str,
        status: str,
        resolution_notes: str | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            UPDATE rule_proposals
            SET status = $2, resolved_at = NOW(), resolution_notes = $3
            WHERE id = $1
            RETURNING id::text, project_id::text, proposed_by, title, description,
                      category, priority, status, resolution_notes, created_at, resolved_at
            """,
            proposal_id,
            status,
            resolution_notes,
        )
        return row_to_dict(row) if row else {}

    async def get_vote_summary(
        self,
        proposal_id: str,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            SELECT
              COUNT(*)::int AS total_votes,
              COUNT(*) FILTER (WHERE vote = 'approve')::int AS approve_count,
              COUNT(*) FILTER (WHERE vote = 'reject')::int AS reject_count,
              COUNT(*) FILTER (WHERE vote = 'abstain')::int AS abstain_count
            FROM rule_proposal_votes
            WHERE proposal_id = $1
            """,
            proposal_id,
        )
        return row_to_dict(row) if row else {}


class ReviewModelMetricsService:
    """审查模型指标服务"""

    def __init__(self, db: Database):
        self._db = db

    async def record_metrics(
        self,
        project_id: str,
        chapter_id: str,
        review_id: str,
        model_name: str,
        response_time_ms: int,
        token_count: int,
        quality_score: float,
        accuracy_score: float | None = None,
        completeness_score: float | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO review_model_metrics
              (project_id, chapter_id, review_id, model_name, response_time_ms,
               token_count, quality_score, accuracy_score, completeness_score)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id::text, project_id::text, chapter_id::text, review_id::text,
                      model_name, response_time_ms, token_count, quality_score,
                      accuracy_score, completeness_score, created_at
            """,
            project_id,
            chapter_id,
            review_id,
            model_name,
            response_time_ms,
            token_count,
            quality_score,
            accuracy_score,
            completeness_score,
        )
        return row_to_dict(row)

    async def get_metrics_summary(
        self,
        project_id: str,
        model_name: str | None = None,
        days: int = 30,
    ) -> dict[str, Any]:
        conditions = ["project_id = $1", "created_at > NOW() - INTERVAL '1 day' * $2"]
        params: list[Any] = [project_id, days]
        idx = 3

        if model_name:
            conditions.append(f"model_name = ${idx}")
            params.append(model_name)
            idx += 1

        row = await self._db.fetchrow(
            f"""
            SELECT
              COUNT(*)::int AS total_reviews,
              AVG(response_time_ms)::int AS avg_response_time_ms,
              AVG(token_count)::int AS avg_token_count,
              AVG(quality_score)::float AS avg_quality_score,
              AVG(accuracy_score)::float AS avg_accuracy_score,
              AVG(completeness_score)::float AS avg_completeness_score,
               SUM(token_count)::bigint AS total_tokens
            FROM review_model_metrics
            WHERE {' AND '.join(conditions)}
            """,
            *params,
        )
        return row_to_dict(row) if row else {}

    async def start_job(self, **kwargs) -> dict[str, Any]:
        """启动审核任务（简化实现）"""
        logger.info(f"start_job called with: {kwargs}")
        return {"job_id": "mock-job-id", "status": "started"}

    async def upsert_council_config(self, **kwargs) -> dict[str, Any]:
        """创建或更新审核委员会配置（简化实现）"""
        logger.info(f"upsert_council_config called with: {kwargs}")
        return {"id": "mock-config-id", "message": "Config saved"}

    async def list_council_configs(self, **kwargs) -> list[dict[str, Any]]:
        """列出审核委员会配置（简化实现）"""
        logger.info(f"list_council_configs called with: {kwargs}")
        return []

    async def get_council_dispatch(self, **kwargs) -> dict[str, Any]:
        """获取委员会待审核模型（简化实现）"""
        logger.info(f"get_council_dispatch called with: {kwargs}")
        return {"models": [], "count": 0}

    async def submit_model_report(self, **kwargs) -> dict[str, Any]:
        """提交模型审核报告（简化实现）"""
        logger.info(f"submit_model_report called with: {kwargs}")
        return {"success": True}

    async def list_revision_tasks(self, **kwargs) -> list[dict[str, Any]]:
        """列出修订任务（简化实现）"""
        logger.info(f"list_revision_tasks called with: {kwargs}")
        return []

    async def update_revision_task(self, **kwargs) -> dict[str, Any]:
        """更新修订任务（简化实现）"""
        logger.info(f"update_revision_task called with: {kwargs}")
        return {"success": True}

    async def aggregate(self, **kwargs) -> dict[str, Any]:
        """汇总审核结果并创建进化提案。
        
        当发现系统性问题时，自动创建进化提案。
        """
        logger.info(f"aggregate called with: {kwargs}")
        
        project_id = kwargs.get('project', kwargs.get('project_id', ''))
        review_job_id = kwargs.get('review_job_id', 'unknown')
        findings = kwargs.get('findings', [])
        
        # 创建进化提案（从系统性问题）
        evolution_proposals = []
        if findings and project_id:
            try:
                evolution_proposals = await self.extract_evolution_proposals(
                    project_id=project_id,
                    review_job_id=review_job_id,
                    findings=findings
                )
            except Exception as e:
                logger.error(f"Failed to extract evolution proposals: {e}")
        
        result = {
            "score": kwargs.get('score', 0),
            "summary": kwargs.get('summary', ''),
            "findings": findings,
            "evolution_proposals_created": len(evolution_proposals),
            "evolution_proposals": evolution_proposals,
        }
        
        return result

    async def extract_rule_proposals(self, **kwargs) -> list[dict[str, Any]]:
        """提取规则提案（简化实现）"""
        logger.info(f"extract_rule_proposals called with: {kwargs}")
        return []

    async def extract_evolution_proposals(
        self,
        project_id: str,
        review_job_id: str,
        findings: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """从审核发现中提取系统性问题并创建进化提案。
        
        Args:
            project_id: 项目ID
            review_job_id: 审核任务ID
            findings: 审核发现列表
            
        Returns:
            创建的进化提案列表
        """
        proposals = []
        
        for finding in findings:
            # 检测是否为系统性问题
            if self._is_systemic_issue(finding):
                proposal = await self._create_evolution_proposal_from_finding(
                    project_id, review_job_id, finding
                )
                if proposal:
                    proposals.append(proposal)
        
        logger.info(f"Created {len(proposals)} evolution proposals from review {review_job_id}")
        return proposals
    
    def _is_systemic_issue(self, finding: dict) -> bool:
        """判断是否为系统性问题（影响多个项目/章节）。"""
        systemic_categories = [
            'world_rule_conflict',      # 世界观规则冲突
            'character_ooc',            # 角色OOC（系统性角色设定问题）
            'style_inconsistency',      # 文风不一致（系统性文风问题）
            'plot_logic_error',         # 剧情逻辑错误（系统性剧情结构问题）
            'knowledge_gap',            # 知识缺失（知识库需要补充）
            'repeated_issue',           # 重复出现的问题
            'template_inappropriate',   # 模板不适用
        ]
        category = finding.get('category', '').lower()
        return category in systemic_categories or finding.get('is_systemic', False)
    
    async def _create_evolution_proposal_from_finding(
        self,
        project_id: str,
        review_job_id: str,
        finding: dict
    ) -> dict[str, Any] | None:
        """从审核发现创建进化提案。"""
        
        # 映射到目标实体类型
        category_to_entity = {
            'world_rule_conflict': 'knowledge_item',
            'character_ooc': 'style_profile',
            'style_inconsistency': 'style_profile',
            'plot_logic_error': 'prompt_template',
            'knowledge_gap': 'knowledge_item',
            'repeated_issue': 'setting_item',
            'template_inappropriate': 'prompt_template',
        }
        
        category = finding.get('category', '').lower()
        target_type = category_to_entity.get(category)
        
        if not target_type:
            return None
        
        # 检查是否已存在类似提案（最近30天内）
        existing = await self._check_similar_proposal(finding)
        if existing:
            logger.info(f"Similar proposal already exists for finding: {finding.get('id', 'unknown')}")
            return None
        
        # 获取工作区信息
        project = await self._db.fetchrow(
            "SELECT workspace, name FROM projects WHERE id = $1",
            project_id
        )
        workspace = project['workspace'] if project else 'default'
        project_name = project['name'] if project else 'Unknown'
        
        # 构建提案内容
        title = f"【审核发现】{finding.get('title', '系统性问题')}"
        description = finding.get('description', '')
        if finding.get('evidence'):
            description += f"\n\n证据:\n{finding['evidence']}"
        
        proposed_content = {
            'finding_id': finding.get('id'),
            'category': category,
            'severity': finding.get('severity', 'medium'),
            'suggestion': finding.get('suggestion', ''),
        }
        
        evidence = {
            'finding': finding,
            'review_job_id': review_job_id,
            'project_id': project_id,
            'project_name': project_name,
        }
        
        # 插入进化提案
        row = await self._db.fetchrow(
            """
            INSERT INTO system_evolution_proposals
              (title, description, proposal_type, target_entity_type, 
               proposed_content, evolution_reason, evidence, 
               status, source_project_id, submitted_by, ai_submitter, created_at, updated_at)
            VALUES ($1, $2, 'create', $3, $4, $5, $6, 'ai_reviewing', $7, NULL, 'review_agent', NOW(), NOW())
            RETURNING id::text, title, description, target_entity_type, status, created_at
            """,
            title,
            description,
            target_type,
            json_dumps(proposed_content),
            f"从审核任务 {review_job_id} 自动检测到的系统性问题",
            json_dumps(evidence),
            project_id,
        )
        
        if row:
            result = row_to_dict(row)
            logger.info(f"Created evolution proposal: {result['id']} for finding {finding.get('id')}")
            return result
        return None
    
    async def _check_similar_proposal(self, finding: dict) -> bool:
        """检查是否已存在类似提案（最近30天内）。"""
        title_pattern = f"%{finding.get('title', '')[:50]}%"
        
        count = await self._db.fetchval(
            """
            SELECT COUNT(*) FROM system_evolution_proposals
            WHERE title LIKE $1
            AND created_at > NOW() - INTERVAL '30 days'
            AND status NOT IN ('admin_rejected', 'applied')
            """,
            title_pattern
        )
        return count > 0

    async def extract_state_updates(self, **kwargs) -> list[dict[str, Any]]:
        """提取状态更新（简化实现）"""
        logger.info(f"extract_state_updates called with: {kwargs}")
        return []

    async def extract_foreshadowing_updates(self, **kwargs) -> list[dict[str, Any]]:
        """提取伏笔更新（简化实现）"""
        logger.info(f"extract_foreshadowing_updates called with: {kwargs}")
        return []

    async def evaluate_model_quality(self, **kwargs) -> dict[str, Any]:
        """评估模型质量（简化实现）"""
        logger.info(f"evaluate_model_quality called with: {kwargs}")
        return {"score": 0, "metrics": {}}
