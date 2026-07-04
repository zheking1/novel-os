import logging
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts

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
