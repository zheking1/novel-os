import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Update existing profiles to have user_id = 'admin'
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"UPDATE model_profiles SET user_id = 'admin' WHERE user_id IS NULL\""
)
print("=== Update Result ===")
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
