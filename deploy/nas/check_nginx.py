import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check nginx config
stdin, stdout, stderr = ssh.exec_command(
    'docker exec nginx cat /etc/nginx/nginx.conf 2>&1 | head -100',
    timeout=15
)
print("=== Nginx main config ===")
print(stdout.read().decode())

# Check nginx conf.d
stdin, stdout, stderr = ssh.exec_command(
    'docker exec nginx ls -la /etc/nginx/conf.d/ 2>&1',
    timeout=10
)
print("=== Nginx conf.d ===")
print(stdout.read().decode())

# Check for novel-os-web config
stdin, stdout, stderr = ssh.exec_command(
    'docker exec nginx cat /etc/nginx/conf.d/*.conf 2>&1 | head -100',
    timeout=10
)
print("=== Nginx conf.d files ===")
print(stdout.read().decode())

# Check nginx logs for 401 errors
stdin, stdout, stderr = ssh.exec_command(
    'docker logs nginx --tail 30 2>&1 | grep -i "401\\|error\\|novel"',
    timeout=10
)
print("=== Nginx logs (401/errors) ===")
print(stdout.read().decode())

ssh.close()
