import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Restart with correct path
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d novel-os-web 2>&1',
    timeout=30
)
print("=== Up ===")
print(stdout.read().decode())

import time
time.sleep(5)

# Test via nginx
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -D - http://127.0.0.1:48084/ -o /dev/null 2>&1 | head -15',
    timeout=10
)
print("=== Via nginx 48084 ===")
print(stdout.read().decode())

# Test direct
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -D - http://127.0.0.1:8790/ -o /dev/null 2>&1 | head -15',
    timeout=10
)
print("=== Direct 8790 ===")
print(stdout.read().decode())

# Verify container has new server.py
stdin, stdout, stderr = ssh.exec_command(
    'docker exec novel-os-web grep "Cache-Control" /app/server.py',
    timeout=10
)
print("=== Container server.py ===")
print(stdout.read().decode())

ssh.close()
