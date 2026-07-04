import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check what the container sees
stdin, stdout, stderr = ssh.exec_command(
    'docker exec novel-os-web grep -A 3 "Cache-Control" /app/server.py 2>&1',
    timeout=10
)
print("=== Container server.py ===")
print(stdout.read().decode())

# Check mount
stdin, stdout, stderr = ssh.exec_command(
    'docker inspect novel-os-web --format="{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}"',
    timeout=10
)
print("=== Mounts ===")
print(stdout.read().decode())

# Force recreate
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --force-recreate novel-os-web 2>&1',
    timeout=30
)
print("=== Force recreate ===")
print(stdout.read().decode())

import time
time.sleep(5)

# Test again
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -D - http://127.0.0.1:8790/ -o /dev/null 2>&1 | head -15',
    timeout=10
)
print("=== After recreate ===")
print(stdout.read().decode())

ssh.close()
