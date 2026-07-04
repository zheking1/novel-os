import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check for nginx or proxy
stdin, stdout, stderr = ssh.exec_command(
    'docker ps --format "{{.Names}} {{.Ports}}" | grep -i "48084\\|nginx\\|proxy\\|traefik"',
    timeout=10
)
print("=== Proxy containers ===")
print(stdout.read().decode())

# Check if index.html is actually updated on NAS
stdin, stdout, stderr = ssh.exec_command(
    'grep -c "知识包" /opt/novel-os/novel-os-web/index.html',
    timeout=10
)
print("=== NAS index.html 知识包 count ===")
print(stdout.read().decode())

# Check web container's mounted file
stdin, stdout, stderr = ssh.exec_command(
    'docker exec novel-os-web grep -c "知识包" /app/index.html',
    timeout=10
)
print("=== Container /app/index.html 知识包 count ===")
print(stdout.read().decode())

# Check if there's a reverse proxy config
stdin, stdout, stderr = ssh.exec_command(
    'cat /etc/nginx/conf.d/*.conf 2>/dev/null | head -50 || echo "No nginx config found"',
    timeout=10
)
print("=== Nginx config ===")
print(stdout.read().decode())

ssh.close()
