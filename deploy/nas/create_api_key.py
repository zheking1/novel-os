import paramiko
import secrets
import hashlib

# Generate a secure API key
api_key = 'nsk-' + secrets.token_urlsafe(32)
print(f"Generated API Key: {api_key}")

# Calculate SHA256 hash
token_hash = hashlib.sha256(api_key.encode('utf-8')).hexdigest()
print(f"Token Hash: {token_hash}")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Insert API token into database
sql = f"""
INSERT INTO api_tokens 
  (user_id, name, token_hash, scopes, workspace_id, expires_at, created_at, updated_at)
VALUES 
  (
    (SELECT id FROM users WHERE username='admin' LIMIT 1),
    'cli-access-token',
    '{token_hash}',
    ARRAY['admin', 'write', 'read'],
    (SELECT id FROM workspaces WHERE slug='default' LIMIT 1),
    NULL,
    NOW(),
    NOW()
  )
ON CONFLICT (token_hash) DO UPDATE
SET scopes = ARRAY['admin', 'write', 'read'],
    updated_at = NOW(),
    revoked_at = NULL
RETURNING id::text, name, scopes, created_at;
"""

stdin, stdout, stderr = ssh.exec_command(f"docker exec novel-postgres psql -U novel_os -d novel_os -c \"{sql}\"")
result = stdout.read().decode()
error = stderr.read().decode()

print("=== Result ===")
print(result)
if error:
    print("Error:", error)

ssh.close()

print("\n" + "="*60)
print("API KEY CREATED SUCCESSFULLY!")
print("="*60)
print(f"\nYour API Key: {api_key}")
print("\nUse this header in requests:")
print(f'Authorization: ApiKey {api_key}')
print("\nOr:")
print(f'Authorization: Bearer {api_key}')
print("="*60)

# Save to file for reference
with open('D:\\Project\\novels codex\\api_key.txt', 'w') as f:
    f.write(f"API Key: {api_key}\n")
    f.write(f"Created: 2024-07-03\n")
    f.write(f"Scopes: admin, write, read\n")
    f.write(f"Workspace: default\n")

print("\nAPI Key also saved to: api_key.txt")
