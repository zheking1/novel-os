import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Rebuild web image
stdin, stdout, stderr = ssh.exec_command(
    'cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml build novel-os-web 2>&1',
    timeout=120
)
print("=== Build ===")
print(stdout.read().decode())

# Restart
stdin, stdout, stderr = ssh.exec_command(
    'docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d novel-os-web 2>&1',
    timeout=30
)
print("=== Up ===")
print(stdout.read().decode())

import time
time.sleep(5)

# Test
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -D - http://127.0.0.1:8790/ -o /dev/null 2>&1 | head -15',
    timeout=10
)
print("=== After rebuild ===")
print(stdout.read().decode())

ssh.close()
