import logging
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts

logger = logging.getLogger("novel_os_mcp.services.model_cost")


class ModelCostService:
    """模型成本服务 - 跟踪API使用和成本"""

    def __init__(self, db: Database):
        self._db = db

    async def record_usage(
        self,
        project_id: str,
        model_name: str,
        operation_type: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float | None = None,
        chapter_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO model_usage
              (project_id, model_name, operation_type, input_tokens, output_tokens,
               cost_usd, chapter_id, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id::text, project_id::text, model_name, operation_type,
                      input_tokens, output_tokens, cost_usd, chapter_id::text,
                      metadata, created_at
            """,
            project_id,
            model_name,
            operation_type,
            input_tokens,
            output_tokens,
            cost_usd,
            chapter_id,
            json_dumps(metadata) if metadata else None,
        )
        r = row_to_dict(row)
        if r.get("metadata"):
            try:
                import json
                r["metadata"] = json.loads(r["metadata"]) if isinstance(r["metadata"], str) else r["metadata"]
            except Exception:
                pass
        return r

    async def get_usage_summary(
        self,
        project_id: str,
        days: int = 30,
        model_name: str | None = None,
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
              COUNT(*)::int AS total_requests,
              SUM(input_tokens)::bigint AS total_input_tokens,
              SUM(output_tokens)::bigint AS total_output_tokens,
              SUM(cost_usd)::float AS total_cost_usd,
              AVG(cost_usd)::float AS avg_cost_per_request,
              AVG(input_tokens)::float AS avg_input_tokens,
              AVG(output_tokens)::float AS avg_output_tokens
            FROM model_usage
            WHERE {' AND '.join(conditions)}
            """,
            *params,
        )
        return row_to_dict(row) if row else {}

    async def get_usage_by_model(
        self,
        project_id: str,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT
              model_name,
              COUNT(*)::int AS requests,
              SUM(input_tokens)::bigint AS input_tokens,
              SUM(output_tokens)::bigint AS output_tokens,
              SUM(cost_usd)::float AS total_cost,
              AVG(cost_usd)::float AS avg_cost
            FROM model_usage
            WHERE project_id = $1 AND created_at > NOW() - INTERVAL '1 day' * $2
            GROUP BY model_name
            ORDER BY total_cost DESC
            """,
            project_id,
            days,
        )
        return rows_to_dicts(rows)

    async def get_daily_usage(
        self,
        project_id: str,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT
              DATE(created_at) AS date,
              COUNT(*)::int AS requests,
              SUM(input_tokens)::bigint AS input_tokens,
              SUM(output_tokens)::bigint AS output_tokens,
              SUM(cost_usd)::float AS total_cost
            FROM model_usage
            WHERE project_id = $1 AND created_at > NOW() - INTERVAL '1 day' * $2
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """,
            project_id,
            days,
        )
        return rows_to_dicts(rows)

    async def set_budget_alert(
        self,
        project_id: str,
        alert_type: str,
        threshold_usd: float,
        notification_method: str = "log",
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO budget_alerts (project_id, alert_type, threshold_usd, notification_method, enabled)
            VALUES ($1, $2, $3, $4, true)
            ON CONFLICT (project_id, alert_type) DO UPDATE
            SET threshold_usd = $3, notification_method = $4, enabled = true
            RETURNING id::text, project_id::text, alert_type, threshold_usd,
                      notification_method, enabled, created_at
            """,
            project_id,
            alert_type,
            threshold_usd,
            notification_method,
        )
        return row_to_dict(row)

    async def check_budget_alerts(
        self,
        project_id: str,
    ) -> list[dict[str, Any]]:
        summary = await self.get_usage_summary(project_id, days=30)
        total_cost = summary.get("total_cost_usd") or 0

        rows = await self._db.fetch(
            """
            SELECT id::text, alert_type, threshold_usd, notification_method
            FROM budget_alerts
            WHERE project_id = $1 AND enabled = true
            """,
            project_id,
        )

        triggered = []
        for row in rows:
            alert = row_to_dict(row)
            if total_cost >= alert["threshold_usd"]:
                alert["current_cost"] = total_cost
                triggered.append(alert)

        return triggered

    async def get_cost_forecast(
        self,
        project_id: str,
        forecast_days: int = 30,
    ) -> dict[str, Any]:
        daily = await self.get_daily_usage(project_id, days=30)
        if not daily:
            return {"forecast_cost": 0, "daily_average": 0, "forecast_days": forecast_days}

        total_cost = sum(d.get("total_cost") or 0 for d in daily)
        days_with_data = len(daily)
        daily_avg = total_cost / days_with_data if days_with_data > 0 else 0

        return {
            "forecast_cost": round(daily_avg * forecast_days, 4),
            "daily_average": round(daily_avg, 4),
            "forecast_days": forecast_days,
            "based_on_days": days_with_data,
        }

    # ========== Model Profile Management ==========

    async def list_profiles(
        self,
        project_id: str,
        task_type: str | None = None,
        status: str | None = "active",
        tier: str | None = None,
    ) -> list[dict[str, Any]]:
        """List model profiles for a specific project."""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if status:
            conditions.append(f"status = ${idx}")
            params.append(status)
            idx += 1
        if tier:
            conditions.append(f"tier = ${idx}")
            params.append(tier)
            idx += 1
        if task_type:
            conditions.append(f"${idx} = ANY(task_types)")
            params.append(task_type)
            idx += 1

        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, profile_key, display_name, provider, model_name,
                   task_types, tier, default_params, cost_config, rate_limit_config,
                   is_default, status, metadata, created_at, updated_at
            FROM model_profiles
            WHERE {' AND '.join(conditions)}
            ORDER BY is_default DESC, tier, display_name
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def list_profiles_by_user(
        self,
        username: str,
        task_type: str | None = None,
        status: str | None = "active",
        tier: str | None = None,
    ) -> list[dict[str, Any]]:
        """List all model profiles for a user (cross-project, user-scoped)."""
        conditions = ["(mp.user_id = $1 OR mp.user_id IS NULL)"]
        params: list[Any] = [username]
        idx = 2

        if status:
            conditions.append(f"mp.status = ${idx}")
            params.append(status)
            idx += 1
        if tier:
            conditions.append(f"mp.tier = ${idx}")
            params.append(tier)
            idx += 1
        if task_type:
            conditions.append(f"${idx} = ANY(mp.task_types)")
            params.append(task_type)
            idx += 1

        rows = await self._db.fetch(
            f"""
            SELECT mp.id::text, mp.profile_key, mp.display_name,
                   mp.provider, mp.model_name, mp.task_types, mp.tier,
                   mp.default_params, mp.cost_config, mp.rate_limit_config,
                   mp.is_default, mp.status, mp.metadata, mp.created_at, mp.updated_at
            FROM model_profiles mp
            WHERE {' AND '.join(conditions)}
            ORDER BY mp.is_default DESC, mp.tier, mp.display_name
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def upsert_profile(
        self,
        profile_key: str,
        display_name: str | None = None,
        provider: str | None = None,
        model_name: str | None = None,
        task_types: list[str] | None = None,
        tier: str | None = None,
        default_params: dict[str, Any] | None = None,
        cost_config: dict[str, Any] | None = None,
        rate_limit_config: dict[str, Any] | None = None,
        is_default: bool | None = None,
        status: str | None = None,
        metadata: dict[str, Any] | None = None,
        username: str | None = None,
        is_contributed: bool | None = None,
    ) -> dict[str, Any]:
        """Create or update a model profile. None fields keep existing values."""
        # Fetch existing by username + profile_key
        existing = await self._db.fetchrow(
            "SELECT * FROM model_profiles WHERE user_id = $1 AND profile_key = $2",
            username, profile_key,
        )

        if existing:
            # Merge: use new value if provided, otherwise keep existing
            merged = dict(existing)
            if display_name is not None: merged["display_name"] = display_name
            if provider is not None: merged["provider"] = provider
            if model_name is not None: merged["model_name"] = model_name
            if task_types is not None: merged["task_types"] = task_types
            if tier is not None: merged["tier"] = tier
            if default_params is not None: merged["default_params"] = default_params
            if cost_config is not None: merged["cost_config"] = cost_config
            if rate_limit_config is not None: merged["rate_limit_config"] = rate_limit_config
            if is_default is not None: merged["is_default"] = is_default
            if status is not None: merged["status"] = status
            if metadata is not None: merged["metadata"] = metadata
            if username is not None: merged["user_id"] = username
            if is_contributed is not None: merged["is_contributed"] = is_contributed
        else:
            # Creating new: display_name, provider, model_name required
            if not display_name or not provider or not model_name:
                raise ValueError("新建模型配置需要 display_name、provider、model_name")
            merged = {
                "display_name": display_name, "provider": provider,
                "model_name": model_name, "task_types": task_types or [],
                "tier": tier or "standard", "default_params": default_params or {},
                "cost_config": cost_config or {}, "rate_limit_config": rate_limit_config or {},
                "is_default": is_default or False, "status": status or "active",
                "metadata": metadata or {}, "user_id": username,
                "is_contributed": is_contributed or False,
            }

        row = await self._db.fetchrow(
            """
            INSERT INTO model_profiles
              (user_id, profile_key, display_name, provider, model_name, task_types,
               tier, default_params, cost_config, rate_limit_config, is_default, status, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT (user_id, profile_key) DO UPDATE
            SET display_name = $3, provider = $4, model_name = $5, task_types = $6,
                tier = $7, default_params = $8, cost_config = $9, rate_limit_config = $10,
                is_default = $11, status = $12, metadata = $13, updated_at = NOW()
            RETURNING id::text, uuid, profile_key, display_name, provider, model_name,
                      task_types, tier, default_params, cost_config, rate_limit_config,
                      is_default, status, metadata, created_at, updated_at
            """,
            username, profile_key,
            merged["display_name"], merged["provider"], merged["model_name"],
            merged["task_types"],
            merged["tier"], json_dumps(merged["default_params"]),
            json_dumps(merged["cost_config"]), json_dumps(merged["rate_limit_config"]),
            merged["is_default"], merged["status"], json_dumps(merged["metadata"]),
            merged["user_id"],
        )
        result = row_to_dict(row) if row else {}
        if is_contributed is not None:
            await self._db.execute(
                "UPDATE model_profiles SET is_contributed=$1 WHERE user_id=$2 AND profile_key=$3",
                is_contributed, username, profile_key,
            )
        return result

    async def route_model(
        self,
        project_id: str,
        task_type: str,
        chapter_no: int | None = None,
        volume_no: int | None = None,
    ) -> dict[str, Any]:
        """Route to best model config for task type."""
        # First check for specific route rules
        rule_row = await self._db.fetchrow(
            """
            SELECT r.profile_key, r.conditions, r.fallback_profile_keys,
                   mp.provider, mp.model_name, mp.default_params, mp.cost_config
            FROM model_route_rules r
            JOIN model_profiles mp ON r.profile_key = mp.profile_key AND (mp.project_id = $1 OR mp.project_id IS NULL)
            WHERE r.project_id = $1 AND r.task_type = $2 AND r.status = 'active'
            ORDER BY r.priority DESC
            LIMIT 1
            """,
            project_id, task_type,
        )

        if rule_row:
            return row_to_dict(rule_row)

        # Fallback to default profile for task type
        profile_row = await self._db.fetchrow(
            """
            SELECT profile_key, provider, model_name, default_params, cost_config
            FROM model_profiles
            WHERE project_id = $1 AND $2 = ANY(task_types) AND status = 'active'
            ORDER BY is_default DESC, tier
            LIMIT 1
            """,
            project_id, task_type,
        )

        if profile_row:
            return row_to_dict(profile_row)

        return {"error": f"No model profile found for task_type={task_type}"}

    async def upsert_route_rule(
        self,
        project_id: str,
        task_type: str,
        profile_key: str,
        priority: int = 100,
        conditions: dict[str, Any] | None = None,
        fallback_profile_keys: list[str] | None = None,
        status: str = "active",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create or update a model route rule."""
        row = await self._db.fetchrow(
            """
            INSERT INTO model_route_rules
              (project_id, task_type, profile_key, priority, conditions, fallback_profile_keys, status, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (project_id, task_type, profile_key) DO UPDATE
            SET priority = $4, conditions = $5, fallback_profile_keys = $6, status = $7, metadata = $8, updated_at = NOW()
            RETURNING id::text, project_id::text, task_type, profile_key, priority,
                      conditions, fallback_profile_keys, status, metadata, created_at, updated_at
            """,
            project_id, task_type, profile_key, priority,
            json_dumps(conditions), fallback_profile_keys, status, json_dumps(metadata),
        )
        return row_to_dict(row) if row else {}

    async def list_route_rules(
        self,
        project_id: str,
        task_type: str | None = None,
        status: str | None = "active",
    ) -> list[dict[str, Any]]:
        """List model route rules."""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if status:
            conditions.append(f"status = ${idx}")
            params.append(status)
            idx += 1
        if task_type:
            conditions.append(f"task_type = ${idx}")
            params.append(task_type)
            idx += 1

        rows = await self._db.fetch(
            f"""
            SELECT r.id::text, r.project_id::text, r.task_type, r.profile_key, r.priority,
                   r.conditions, r.fallback_profile_keys, r.status, r.metadata, r.created_at, r.updated_at,
                   mp.display_name as profile_display_name, mp.provider, mp.model_name
            FROM model_route_rules r
            JOIN model_profiles mp ON r.profile_key = mp.profile_key AND mp.project_id = r.project_id
            WHERE {' AND '.join(conditions)}
            ORDER BY r.priority DESC, r.task_type
            """,
            *params,
        )
        return rows_to_dicts(rows)

    # ========== Cost Reporting ==========

    async def cost_report(
        self,
        project_id: str,
        group_by: str = "day",
        task_types: list[str] | None = None,
        profile_keys: list[str] | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict[str, Any]:
        """Generate cost report grouped by time period."""
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if from_date:
            conditions.append(f"created_at >= ${idx}")
            params.append(from_date)
            idx += 1
        if to_date:
            conditions.append(f"created_at <= ${idx}")
            params.append(to_date + " 23:59:59")
            idx += 1
        if task_types:
            conditions.append(f"operation_type = ANY(${'{idx}'})")
            params.append(task_types)
            idx += 1
        if profile_keys:
            conditions.append(f"model_name = ANY(${'{idx}'})")
            params.append(profile_keys)
            idx += 1

        where_clause = " AND ".join(conditions)

        # Get summary stats
        stats_row = await self._db.fetchrow(
            f"""
            SELECT
                COUNT(*)::int AS total_requests,
                SUM(input_tokens)::bigint AS total_input_tokens,
                SUM(output_tokens)::bigint AS total_output_tokens,
                SUM(cost_usd)::float AS total_cost
            FROM model_usage
            WHERE {where_clause}
            """,
            *params,
        )

        # Get grouped data
        if group_by == "day":
            group_sql = "DATE(created_at)"
        elif group_by == "week":
            group_sql = "DATE_TRUNC('week', created_at)"
        elif group_by == "month":
            group_sql = "DATE_TRUNC('month', created_at)"
        else:
            group_sql = "DATE(created_at)"

        group_rows = await self._db.fetch(
            f"""
            SELECT
                {group_sql} AS key,
                COUNT(*)::int AS request_count,
                SUM(input_tokens)::bigint AS input_tokens,
                SUM(output_tokens)::bigint AS output_tokens,
                SUM(cost_usd)::float AS cost
            FROM model_usage
            WHERE {where_clause}
            GROUP BY {group_sql}
            ORDER BY key DESC
            LIMIT 100
            """,
            *params,
        )

        return {
            "total_cost": stats_row["total_cost"] if stats_row else 0,
            "total_requests": stats_row["total_requests"] if stats_row else 0,
            "total_input_tokens": stats_row["total_input_tokens"] if stats_row else 0,
            "total_output_tokens": stats_row["total_output_tokens"] if stats_row else 0,
            "avg_latency_ms": stats_row["avg_latency_ms"] if stats_row else 0,
            "groups": rows_to_dicts(group_rows),
            "stats": row_to_dict(stats_row) if stats_row else {},
        }
