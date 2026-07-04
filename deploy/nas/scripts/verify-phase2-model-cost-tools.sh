#!/usr/bin/env sh
set -eu

cd /opt/novel-os

docker compose -f docker-compose.yml -f docker-compose.app.example.yml exec -T novel-os-mcp python - <<'PY'
import asyncio
import secrets

from novel_os_mcp.config import get_settings
from novel_os_mcp.db import Database
from novel_os_mcp.services import ModelCostService, WorkspaceService


async def main() -> None:
    suffix = secrets.token_hex(4)
    username = f"verify_model_cost_{suffix}"
    workspace_slug = f"verify-model-cost-ws-{suffix}"
    project_slug = f"verify-model-cost-project-{suffix}"

    db = Database(get_settings())
    await db.connect()
    workspace = WorkspaceService(db)
    model_cost = ModelCostService(db)
    try:
        await workspace.create_workspace(workspace_slug, "Verify Model Cost Workspace", username)
        project = await workspace.create_project(
            workspace_slug,
            project_slug,
            "Verify Model Cost Project",
            "temporary phase2 model cost verification",
            username,
        )
        project_id = project["id"]

        cheap = await model_cost.upsert_profile(
            project_id=project_id,
            profile_key="cheap_model",
            display_name="Cheap Model",
            provider="openai",
            model_name="gpt-4o-mini",
            task_types=["outline", "summary", "embedding"],
            tier="cheap",
            cost_config={"input_per_1k": 0.00015, "output_per_1k": 0.0006},
            is_default=False,
        )
        assert cheap["profile_key"] == "cheap_model"
        assert cheap["tier"] == "cheap"
        assert cheap["cost_config"]["input_per_1k"] == 0.00015

        standard = await model_cost.upsert_profile(
            project_id=project_id,
            profile_key="standard_model",
            display_name="Standard Model",
            provider="openai",
            model_name="gpt-4o",
            task_types=["chapter_draft", "chapter_segment", "polish", "review"],
            tier="standard",
            cost_config={"input_per_1k": 0.0025, "output_per_1k": 0.01},
            is_default=True,
        )
        assert standard["is_default"] is True
        assert standard["tier"] == "standard"

        premium = await model_cost.upsert_profile(
            project_id=project_id,
            profile_key="premium_model",
            display_name="Premium Model",
            provider="anthropic",
            model_name="claude-3-opus",
            task_types=["review", "compliance_review", "rule_extraction"],
            tier="premium",
            cost_config={"input_per_1k": 0.015, "output_per_1k": 0.075},
            is_default=False,
        )
        assert premium["tier"] == "premium"

        all_profiles = await model_cost.list_profiles(project_id=project_id)
        assert len(all_profiles) == 3
        assert all_profiles[0]["is_default"] is True

        review_profiles = await model_cost.list_profiles(
            project_id=project_id, task_type="review"
        )
        assert len(review_profiles) >= 2

        outline_route = await model_cost.route_model(
            project_id=project_id, task_type="outline"
        )
        assert outline_route["primary"] is not None
        assert outline_route["source"] == "task_type_default"

        await model_cost.upsert_route_rule(
            project_id=project_id,
            task_type="review",
            profile_key="premium_model",
            priority=10,
            fallback_profile_keys=["standard_model"],
        )

        review_route = await model_cost.route_model(
            project_id=project_id, task_type="review"
        )
        assert review_route["primary"]["profile_key"] == "premium_model"
        assert review_route["source"] == "route_rule"
        assert len(review_route["fallbacks"]) >= 1

        usage1 = await model_cost.record_usage(
            project_id=project_id,
            task_type="chapter_draft",
            profile_key="standard_model",
            source_type="generation",
            input_tokens=1000,
            output_tokens=2000,
            latency_ms=1500,
            username=username,
        )
        assert usage1["total_tokens"] == 3000
        assert usage1["cost_amount"] > 0
        assert usage1["success"] is True

        usage2 = await model_cost.record_usage(
            project_id=project_id,
            task_type="review",
            profile_key="premium_model",
            source_type="review",
            input_tokens=3000,
            output_tokens=500,
            cached_tokens=500,
            latency_ms=3000,
            username=username,
        )
        assert usage2["total_tokens"] == 4000
        assert usage2["cost_amount"] > 0

        error_usage = await model_cost.record_usage(
            project_id=project_id,
            task_type="outline",
            profile_key="cheap_model",
            source_type="generation",
            input_tokens=500,
            output_tokens=0,
            success=False,
            error_code="rate_limit_exceeded",
            username=username,
        )
        assert error_usage["success"] is False
        assert error_usage["error_code"] == "rate_limit_exceeded"

        day_report = await model_cost.cost_report(
            project_id=project_id, group_by="day"
        )
        assert day_report["summary"]["usage_count"] == 3
        assert day_report["summary"]["total_tokens"] == 7500
        assert day_report["summary"]["success_count"] == 2
        assert day_report["summary"]["error_count"] == 1
        assert len(day_report["groups"]) >= 1

        task_report = await model_cost.cost_report(
            project_id=project_id, group_by="task_type"
        )
        assert task_report["summary"]["usage_count"] == 3
        assert len(task_report["groups"]) == 3

        profile_report = await model_cost.cost_report(
            project_id=project_id, group_by="profile"
        )
        assert profile_report["summary"]["usage_count"] == 3
        assert len(profile_report["groups"]) == 3

        filtered = await model_cost.cost_report(
            project_id=project_id,
            group_by="task_type",
            task_types=["chapter_draft", "review"],
        )
        assert filtered["summary"]["usage_count"] == 2

        rules = await model_cost.list_route_rules(project_id=project_id)
        assert len(rules) == 1
        assert rules[0]["task_type"] == "review"
        assert rules[0]["profile_key"] == "premium_model"

        print("phase2 model cost tools smoke ok")
    finally:
        await db.execute("DELETE FROM workspaces WHERE slug = $1", workspace_slug)
        await db.close()


asyncio.run(main())
PY
