import paramiko
import sys
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check containers
stdin, stdout, stderr = ssh.exec_command('docker ps --format "{{.Names}} {{.Status}}" | grep novel', timeout=15)
print("=== Containers ===")
print(stdout.read().decode())

# Check MCP logs (limit + skip unicode)
stdin, stdout, stderr = ssh.exec_command('docker logs novel-os-mcp 2>&1 | tail -10', timeout=15)
print("=== MCP Logs ===")
raw = stdout.read()
try:
    print(raw.decode('utf-8'))
except UnicodeDecodeError:
    print(raw.decode('ascii', errors='replace'))

# Count registered tools
stdin, stdout, stderr = ssh.exec_command(
    'docker exec novel-os-mcp python -c "import sys; sys.path.insert(0,\'/app/src\'); from novel_os_mcp.tools import *; print(\'IMPORT OK\')" 2>&1',
    timeout=30
)
print("=== Import Test ===")
raw2 = stdout.read()
try:
    print(raw2.decode('utf-8'))
except UnicodeDecodeError:
    print(raw2.decode('ascii', errors='replace'))
raw_err = stderr.read()
if raw_err:
    try:
        print(raw_err.decode('utf-8'))
    except UnicodeDecodeError:
        print(raw_err.decode('ascii', errors='replace'))

ssh.close()
