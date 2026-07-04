import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Test with GET and verbose headers
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -D - http://127.0.0.1:8790/ -o /dev/null 2>&1 | head -15',
    timeout=10
)
print("=== GET Headers ===")
print(stdout.read().decode())

# Verify cache headers are in server.py
stdin, stdout, stderr = ssh.exec_command(
    'grep -A 3 "Cache-Control" /opt/novel-os/novel-os-web/server.py',
    timeout=10
)
print("=== server.py Cache-Control ===")
print(stdout.read().decode())

ssh.close()
