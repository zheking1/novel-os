-- Optional bootstrap rows for a fresh local deployment.
-- The MCP implementation should replace this with a proper user/token
-- bootstrap command before production use.

INSERT INTO users (username, display_name, status)
VALUES ('admin', 'Default Admin', 'active')
ON CONFLICT (username) DO NOTHING;

INSERT INTO workspaces (slug, name, owner_user_id)
SELECT 'default', 'Default Workspace', users.id
FROM users
WHERE users.username = 'admin'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO workspace_members (workspace_id, user_id, role)
SELECT workspaces.id, users.id, 'owner'
FROM workspaces, users
WHERE workspaces.slug = 'default'
  AND users.username = 'admin'
ON CONFLICT (workspace_id, user_id) DO NOTHING;

