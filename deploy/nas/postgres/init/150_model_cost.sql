CREATE TABLE IF NOT EXISTS model_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    profile_key TEXT NOT NULL,
    display_name TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    task_types TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    tier TEXT NOT NULL DEFAULT 'standard',
    default_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    cost_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    rate_limit_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(project_id, profile_key)
);

CREATE INDEX IF NOT EXISTS idx_model_profiles_project_status
  ON model_profiles(project_id, status, tier);

CREATE INDEX IF NOT EXISTS idx_model_profiles_task_types
  ON model_profiles(project_id, status)
  WHERE task_types && ARRAY[]::TEXT[] = false;

CREATE TABLE IF NOT EXISTS model_route_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_type TEXT NOT NULL,
    profile_key TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 100,
    conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
    fallback_profile_keys TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    status TEXT NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(project_id, task_type, profile_key)
);

CREATE INDEX IF NOT EXISTS idx_model_route_rules_project_task
  ON model_route_rules(project_id, task_type, status, priority);

CREATE TABLE IF NOT EXISTS model_usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    profile_key TEXT,
    provider TEXT,
    model_name TEXT,
    task_type TEXT NOT NULL,
    source_type TEXT,
    source_id TEXT,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cached_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    cost_amount NUMERIC(12, 6) NOT NULL DEFAULT 0,
    currency TEXT NOT NULL DEFAULT 'USD',
    latency_ms INTEGER,
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error_code TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_model_usage_project_created
  ON model_usage_records(project_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_model_usage_project_task
  ON model_usage_records(project_id, task_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_model_usage_project_profile
  ON model_usage_records(project_id, profile_key, created_at DESC);
