import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Check user_id in model_profiles
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT profile_key, user_id FROM model_profiles\""
)
print("=== Model Profiles User ID ===")
print(stdout.read().decode('utf-8', errors='replace'))

# Check current auth user
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT username FROM users WHERE status = 'active' LIMIT 3\""
)
print("=== Active Users ===")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
