import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Update all model_profiles to user_id = 'admin' (or NULL for shared)
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"UPDATE model_profiles SET user_id = 'admin' WHERE user_id = 'admin'\""
)
print("=== Update Result ===")
print(stdout.read().decode('utf-8', errors='replace'))

# Verify
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT profile_key, user_id FROM model_profiles\""
)
print("=== After Update ===")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
