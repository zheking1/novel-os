-- Migration: Add user_id to model_profiles for user-level model config

ALTER TABLE model_profiles ADD COLUMN IF NOT EXISTS user_id TEXT;

-- Create index for user_id queries
CREATE INDEX IF NOT EXISTS idx_model_profiles_user_id ON model_profiles(user_id);

-- Update existing records to have a default user (from auth context)
-- This will be populated via API calls

-- Update timestamp
UPDATE model_profiles SET updated_at = NOW() WHERE user_id IS NULL;
