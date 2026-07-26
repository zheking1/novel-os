-- Migration 210: Add summary/description/portrait_url to state_entities
ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS portrait_url TEXT;