-- Migration: Add password_hash column to users table
-- Date: 2026-07-03
-- Description: Enable password-based authentication for WebUI

-- Add password_hash column
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMPTZ;

-- Add comment for documentation
COMMENT ON COLUMN users.password_hash IS 'BCrypt hashed password for WebUI login';
COMMENT ON COLUMN users.last_login_at IS 'Last successful login timestamp';

-- Set default password '123456' for existing users (bcrypt with cost 10)
-- Note: This is a temporary measure. Users should change password after first login.
UPDATE users 
SET password_hash = '$2b$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi'
WHERE password_hash IS NULL;

-- Create index for faster lookup (if not exists)
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
