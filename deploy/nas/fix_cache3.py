import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Read server.py
sftp = ssh.open_sftp()
with sftp.open('/opt/novel-os/novel-os-web/server.py', 'r') as f:
    content = f.read()

# Find the do_GET method and add cache headers
old_text = '''        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST'''

new_text = '''        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(body)

    def do_POST'''

if old_text in content:
    content = content.replace(old_text, new_text)
    with sftp.open('/opt/novel-os/novel-os-web/server.py', 'w') as f:
        f.write(content)
    print("=== server.py updated ===")
else:
    print("=== Pattern not found ===")

sftp.close()

# Restart container
stdin, stdout, stderr = ssh.exec_command(
    'docker restart novel-os-web 2>&1',
    timeout=30
)
print("=== Restart ===")
print(stdout.read().decode())

# Wait and test
import time
time.sleep(4)
stdin, stdout, stderr = ssh.exec_command(
    'curl -s -I http://127.0.0.1:8790/ 2>&1',
    timeout=10
)
print("=== Headers ===")
print(stdout.read().decode())

ssh.close()
