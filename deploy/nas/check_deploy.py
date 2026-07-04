import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check if the file on NAS has the debug code
stdin, stdout, stderr = ssh.exec_command(
    'grep -c "renderUkTree CALLED" /opt/novel-os/novel-os-web/index.html',
    timeout=10
)
print("=== NAS file check ===")
print("renderUkTree CALLED count:", stdout.read().decode().strip())

# Check the container's file
stdin, stdout, stderr = ssh.exec_command(
    'docker exec novel-os-web grep -c "renderUkTree CALLED" /app/index.html',
    timeout=10
)
print("=== Container file check ===")
print("renderUkTree CALLED count:", stdout.read().decode().strip())

# Check if nginx is serving the right file
stdin, stdout, stderr = ssh.exec_command(
    'curl -s http://127.0.0.1:48084/ | grep -c "renderUkTree CALLED"',
    timeout=10
)
print("=== Via nginx check ===")
print("renderUkTree CALLED count:", stdout.read().decode().strip())

ssh.close()
