import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check server.py
stdin, stdout, stderr = ssh.exec_command(
    'cat /opt/novel-os/novel-os-web/server.py 2>&1',
    timeout=10
)
print("=== server.py ===")
print(stdout.read().decode())

ssh.close()
