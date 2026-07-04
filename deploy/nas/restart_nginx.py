import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Restart nginx completely
stdin, stdout, stderr = ssh.exec_command(
    'docker restart nginx 2>&1',
    timeout=30
)
print("=== Nginx restart ===")
print(stdout.read().decode())

# Verify
stdin, stdout, stderr = ssh.exec_command(
    'curl -s http://127.0.0.1:48084/ | grep -c "知识包"',
    timeout=10
)
print("=== Via nginx 48084 ===")
print(stdout.read().decode())

ssh.close()
