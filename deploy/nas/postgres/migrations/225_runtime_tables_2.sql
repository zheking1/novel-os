-- Migration: 225_runtime_tables_2.sql
-- Description: 补齐代码已在读写、但仓库缺失建表 SQL 的运行时表
--              （discussion_sessions / tasks / workflows / workflow_steps）
--              以及 review_jobs / review_reports 的列漂移
-- Date: 2026-10-11
-- Depends: init/010_core_schema.sql (projects / chapters / review_jobs / review_reports)
--
-- 【列定义来源】全部由 novel-os-mcp 源码中的 SQL 语句反推，逐列证据见下方注释。
-- 全部语句幂等（CREATE TABLE IF NOT EXISTS / ADD COLUMN IF NOT EXISTS / CREATE INDEX IF NOT EXISTS）。
-- ⚠️ 若目标库已手工建过这些表，本迁移不会改动其结构；列差异需先 \d 比对后手工 ALTER 补齐
--    （尤其 discussion_sessions.id 是 UUID 还是 TEXT、project_id 是否存在）。

-- ========================================
-- 1. 多模型讨论室会话表
-- ========================================

CREATE TABLE IF NOT EXISTS discussion_sessions (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    -- 存 workspace slug（非 id），见 discussion_room.py:107/194/685
    workspace          TEXT NOT NULL,
    -- 存 project slug（非 id），见 discussion_room.py:107/194；novel_wizard.py:1551
    project            TEXT NOT NULL,
    topic              TEXT NOT NULL,
    control_model      TEXT NOT NULL,
    -- discussion_room.py:109 显式 $6::text[]
    discussion_models  TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    -- analyzing / proposing / review_rN / completed；不建 CHECK 以免新 phase 写不进去
    phase              TEXT NOT NULL DEFAULT 'analyzing',
    round              INTEGER NOT NULL DEFAULT 0,
    -- running / completed / partial / pending_admin / applied / rate_limited
    status             TEXT NOT NULL DEFAULT 'running',
    -- JSONB 数组，元素 {role, model, phase, content, timestamp}；追加用 responses || $n::jsonb
    responses          JSONB NOT NULL DEFAULT '[]'::jsonb,
    -- JSONB：{data_source, data_category, output_type}
    history            JSONB NOT NULL DEFAULT '{}'::jsonb,
    consensus_reached  BOOLEAN NOT NULL DEFAULT false,
    summary            TEXT,
    -- 弱证据列：仅 discussion_room.py:730 被 SELECT，INSERT 路径从不写入，故可空
    -- 未加外键：若库中存在非 UUID 脏值会插入失败
    project_id         UUID,
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_discussion_sessions_ws_proj
    ON discussion_sessions(workspace, project, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_discussion_sessions_status
    ON discussion_sessions(status);
CREATE INDEX IF NOT EXISTS idx_discussion_sessions_project_id
    ON discussion_sessions(project_id) WHERE project_id IS NOT NULL;

COMMENT ON TABLE discussion_sessions IS '多模型讨论室会话表 - discussion_room.* 读写，消息存于 responses(JSONB 数组)';
COMMENT ON COLUMN discussion_sessions.round IS '当前讨论轮次，0 起';
COMMENT ON COLUMN discussion_sessions.status IS 'running / completed / partial / pending_admin / applied / rate_limited';
COMMENT ON COLUMN discussion_sessions.phase IS 'analyzing / proposing / review_rN / completed';

-- ========================================
-- 2. 写作任务表（WorkflowService）
-- ========================================

CREATE TABLE IF NOT EXISTS tasks (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id    UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title         TEXT NOT NULL,
    description   TEXT,
    task_type     TEXT NOT NULL DEFAULT 'writing',
    -- urgent / high / normal / 其它；ORDER BY 用 CASE 排序，不用 ENUM
    priority      TEXT NOT NULL DEFAULT 'normal',
    -- 负责人 username（字符串，非 users.id）
    assigned_to   TEXT,
    chapter_id    UUID REFERENCES chapters(id) ON DELETE SET NULL,
    due_date      TIMESTAMPTZ,
    -- todo / in_progress / completed
    status        TEXT NOT NULL DEFAULT 'todo',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at  TIMESTAMPTZ,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_project_created ON tasks(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to) WHERE assigned_to IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;

COMMENT ON TABLE tasks IS '写作任务表 - WorkflowService.create_task/get_tasks/update_task/get_task_stats 读写';

-- ========================================
-- 3. 工作流与步骤（WorkflowService）
-- ========================================

CREATE TABLE IF NOT EXISTS workflows (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id     UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name           TEXT NOT NULL,
    description    TEXT,
    workflow_type  TEXT,
    status         TEXT NOT NULL DEFAULT 'draft',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_workflows_project ON workflows(project_id, created_at DESC);

COMMENT ON TABLE workflows IS '工作流定义表 - WorkflowService.create_workflow/get_workflow/update_workflow 读写';

CREATE TABLE IF NOT EXISTS workflow_steps (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id   UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    name          TEXT NOT NULL,
    step_type     TEXT,
    step_order    INTEGER NOT NULL DEFAULT 0,
    config        JSONB NOT NULL DEFAULT '{}'::jsonb,
    dependencies  JSONB NOT NULL DEFAULT '[]'::jsonb,
    status        TEXT NOT NULL DEFAULT 'pending',
    result        JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_workflow_steps_workflow ON workflow_steps(workflow_id, step_order);

COMMENT ON TABLE workflow_steps IS '工作流步骤表 - WorkflowService.add_step/list_steps/update_step 读写';

-- ========================================
-- 4. review_jobs / review_reports 列漂移
--    代码写入的列名在 010_core_schema.sql 的建表语句中不存在
-- ========================================

-- services/review.py:268-273 INSERT 含 chapter_no / session_id
ALTER TABLE review_jobs ADD COLUMN IF NOT EXISTS chapter_no INTEGER;
ALTER TABLE review_jobs ADD COLUMN IF NOT EXISTS session_id TEXT;
-- discussion_room.py:723 SET aggregated_at = NOW()
ALTER TABLE review_jobs ADD COLUMN IF NOT EXISTS aggregated_at TIMESTAMPTZ;

-- discussion_room.py:745-751 INSERT 用 reviewer_model / raw_content
-- （注意：不要 rename 已有的 model_id / findings，其它路径可能仍在使用）
ALTER TABLE review_reports ADD COLUMN IF NOT EXISTS reviewer_model TEXT;
ALTER TABLE review_reports ADD COLUMN IF NOT EXISTS raw_content TEXT;

CREATE INDEX IF NOT EXISTS idx_review_jobs_session_id ON review_jobs(session_id) WHERE session_id IS NOT NULL;

-- ========================================
-- Migration Complete
-- ========================================

SELECT 'Migration 225_runtime_tables_2 completed successfully' AS status;
