import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Check model_profiles table structure
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"\\d model_profiles\""
)
print("=== Model Profiles Schema ===")
print(stdout.read().decode('utf-8', errors='replace'))

# Check if user_id column exists
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT column_name FROM information_schema.columns WHERE table_name = 'model_profiles'\""
)
print("=== Columns ===")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
