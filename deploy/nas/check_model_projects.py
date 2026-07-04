import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Check project distribution of model profiles
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT project_id::text, COUNT(*) FROM model_profiles GROUP BY project_id\""
)
print("=== Model Profiles by Project ===")
print(stdout.read().decode('utf-8', errors='replace'))

# Check if there's a default project
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT slug, title FROM projects WHERE slug = 'default'\""
)
print("=== Default Project ===")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
