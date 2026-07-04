import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Restart web container and nginx
stdin, stdout, stderr = ssh.exec_command(
    'docker restart novel-os-web && docker exec nginx nginx -s reload',
    timeout=30
)
print("=== Restart ===")
print(stdout.read().decode())

import time
time.sleep(5)

# Verify
stdin, stdout, stderr = ssh.exec_command(
    'curl -s http://127.0.0.1:48084/ | grep -c "知识包"',
    timeout=10
)
print("=== Web response check ===")
print(stdout.read().decode())

ssh.close()
