import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Read current server.py
stdin, stdout, stderr = ssh.exec_command(
    'cat /opt/novel-os/novel-os-web/server.py 2>&1',
    timeout=10
)
content = stdout.read().decode()

# Add cache-control headers to the GET handler
old = '''        body = INDEX.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)'''

new = '''        body = INDEX.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(body)'''

if old in content:
    content = content.replace(old, new)
    # Write back
    sftp = ssh.open_sftp()
    remote_file = '/opt/novel-os/novel-os-web/server.py'
    sftp.putfo(open('/dev/stdin', 'w'), remote_file)
    # Actually use a simpler approach
    sftp.close()
    
    # Write via echo
    stdin2, stdout2, stderr2 = ssh.exec_command(
        f"cat > /opt/novel-os/novel-os-web/server.py << 'ENDOFFILE'\n{content}\nENDOFFILE",
        timeout=15
    )
    print("=== Write result ===")
    print(stdout2.read().decode())
    print(stderr2.read().decode())
else:
    print("Pattern not found!")

# Restart web container
stdin, stdout, stderr = ssh.exec_command(
    'docker restart novel-os-web 2>&1',
    timeout=30
)
print("=== Restart ===")
print(stdout.read().decode())

ssh.close()
