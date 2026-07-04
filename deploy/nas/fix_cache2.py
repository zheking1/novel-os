import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Use sed to add cache headers
stdin, stdout, stderr = ssh.exec_command(
    '''sed -i '/self.send_header("Content-Length", str(len(body)))/a\\        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")\\n        self.send_header("Pragma", "no-cache")\\n        self.send_header("Expires", "0")' /opt/novel-os/novel-os-web/server.py''',
    timeout=10
)
print("=== sed result ===")
print(stdout.read().decode())
print(stderr.read().decode())

# Verify
stdin, stdout, stderr = ssh.exec_command(
    'grep -A 5 "Content-Length" /opt/novel-os/novel-os-web/server.py | head -10',
    timeout=10
)
print("=== Verify ===")
print(stdout.read().decode())

# Restart
stdin, stdout, stderr = ssh.exec_command(
    'docker restart novel-os-web 2>&1',
    timeout=30
)
print("=== Restart ===")
print(stdout.read().decode())

# Test
import time
time.sleep(3)
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -I http://127.0.0.1:8790/ 2>&1 | grep -i "cache\\|content-type"',
    timeout=10
)
print("=== Headers ===")
print(stdout.read().decode())

ssh.close()
