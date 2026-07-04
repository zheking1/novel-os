import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Use python inside the container to modify the file
python_script = '''
import re
with open("/opt/novel-os/novel-os-web/server.py", "r") as f:
    content = f.read()

old = 'self.send_header("Content-Length", str(len(body)))\\n        self.end_headers()'
new = 'self.send_header("Content-Length", str(len(body)))\\n        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")\\n        self.send_header("Pragma", "no-cache")\\n        self.send_header("Expires", "0")\\n        self.end_headers()'

if old in content:
    content = content.replace(old, new)
    with open("/opt/novel-os/novel-os-web/server.py", "w") as f:
        f.write(content)
    print("OK")
else:
    print("NOT FOUND")
'''

stdin, stdout, stderr = ssh.exec_command(f'python3 -c "{python_script}"', timeout=15)
print("=== Result ===")
print(stdout.read().decode())
print(stderr.read().decode())

# Restart
stdin, stdout, stderr = ssh.exec_command(
    'docker restart novel-os-web 2>&1',
    timeout=30
)
print("=== Restart ===")
print(stdout.read().decode())

import time
time.sleep(4)

# Test
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -I http://127.0.0.1:8790/ 2>&1',
    timeout=10
)
print("=== Headers ===")
print(stdout.read().decode())

ssh.close()
