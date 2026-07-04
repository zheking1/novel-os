import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check top of server.py for INDEX definition
stdin, stdout, stderr = ssh.exec_command(
    'head -60 /opt/novel-os/novel-os-web/server.py 2>&1',
    timeout=10
)
print("=== server.py top ===")
print(stdout.read().decode())

ssh.close()
