-- Migration 212: Skill Management System
-- Skills 表 + Skill Steps 表

-- Skills 主表
CREATE TABLE IF NOT EXISTS skills (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(100) NOT NULL UNIQUE,
  description TEXT,
  content TEXT NOT NULL,
  trigger_words TEXT[] DEFAULT '{}',
  tool_hints TEXT[] DEFAULT '{}',
  embedding_id TEXT,
  is_active BOOLEAN DEFAULT true,
  sort_order INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Skill 步骤表
CREATE TABLE IF NOT EXISTS skill_steps (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  skill_id UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  step_order INT NOT NULL,
  step_name VARCHAR(100) NOT NULL,
  tool_name VARCHAR(100),
  description TEXT,
  parameters JSONB DEFAULT '{}',
  optional BOOLEAN DEFAULT false,
  conditional TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_skill_name ON skills(name);
CREATE INDEX IF NOT EXISTS idx_skill_active ON skills(is_active);
CREATE INDEX IF NOT EXISTS idx_step_skill ON skill_steps(skill_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_step_order ON skill_steps(skill_id, step_order);
