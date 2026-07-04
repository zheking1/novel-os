import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check docker-compose config
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml config 2>&1 | grep -A 10 novel-os-web',
    timeout=15
)
print("=== Web Config ===")
print(stdout.read().decode())

# Check web container logs
stdin, stdout, stderr = ssh.exec_command(
    'docker logs novel-os-web --tail 20 2>&1',
    timeout=15
)
print("=== Web Logs ===")
print(stdout.read().decode())

# Check ports
stdin, stdout, stderr = ssh.exec_command(
    'docker port novel-os-web 2>&1',
    timeout=10
)
print("=== Web Ports ===")
print(stdout.read().decode())

ssh.close()
