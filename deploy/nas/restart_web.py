import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Restart web container
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml restart novel-os-web 2>&1',
    timeout=30
)
print(stdout.read().decode())
print(stderr.read().decode())

# Verify
stdin, stdout, stderr = ssh.exec_command(
    'docker ps --format "{{.Names}} {{.Status}}" | grep novel',
    timeout=10
)
print("=== Containers ===")
print(stdout.read().decode())

ssh.close()
