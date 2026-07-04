import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check web container mount
stdin, stdout, stderr = ssh.exec_command(
    'docker inspect novel-os-web --format="{{.Mounts}}" 2>&1',
    timeout=10
)
print("=== Web mounts ===")
print(stdout.read().decode())

# Check Dockerfile
stdin, stdout, stderr = ssh.exec_command(
    'cat /opt/novel-os/novel-os-web/Dockerfile 2>&1',
    timeout=10
)
print("=== Web Dockerfile ===")
print(stdout.read().decode())

# Direct curl to container
stdin, stdout, stderr = ssh.exec_command(
    'curl -s http://127.0.0.1:8790/ | grep -c "知识包"',
    timeout=10
)
print("=== Direct curl to 8790 ===")
print(stdout.read().decode())

# Check if web container is using old image
stdin, stdout, stderr = ssh.exec_command(
    'docker images novel-os-web --format "{{.Repository}}:{{.Tag}} {{.CreatedAt}}"',
    timeout=10
)
print("=== Web images ===")
print(stdout.read().decode())

ssh.close()
