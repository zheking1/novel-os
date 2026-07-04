import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check web server.py
stdin, stdout, stderr = ssh.exec_command(
    'cat /opt/novel-os/novel-os-web/server.py 2>&1',
    timeout=10
)
print("=== server.py ===")
print(stdout.read().decode())

# Check web container logs for errors
stdin, stdout, stderr = ssh.exec_command(
    'docker logs novel-os-web --tail 50 2>&1',
    timeout=10
)
print("=== Web logs ===")
print(stdout.read().decode())

# Check if index.html is being served correctly
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -I http://127.0.0.1:8790/ 2>&1',
    timeout=10
)
print("=== HTTP headers ===")
print(stdout.read().decode())

# Check file modification time
stdin, stdout, stderr = ssh.exec_command(
    'ls -la /opt/novel-os/novel-os-web/index.html 2>&1',
    timeout=10
)
print("=== File info ===")
print(stdout.read().decode())

# Check container file modification time
stdin, stdout, stderr = ssh.exec_command(
    'docker exec novel-os-web ls -la /app/index.html 2>&1',
    timeout=10
)
print("=== Container file info ===")
print(stdout.read().decode())

ssh.close()
