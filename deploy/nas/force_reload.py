import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Force reload nginx
stdin, stdout, stderr = ssh.exec_command(
    'docker exec nginx nginx -s reload 2>&1',
    timeout=10
)
print("=== Nginx reload ===")
print(stdout.read().decode())

# Verify container file has the new content
stdin, stdout, stderr = ssh.exec_command(
    'docker exec novel-os-web grep -A 2 "知识包" /app/index.html | head -10',
    timeout=10
)
print("=== Container file content ===")
print(stdout.read().decode())

# Check web container is healthy
stdin, stdout, stderr = ssh.exec_command(
    'docker exec novel-os-web wget -qO- http://localhost:8790/ | grep -c "知识包"',
    timeout=10
)
print("=== Web response knowledge-pack count ===")
print(stdout.read().decode())

ssh.close()
