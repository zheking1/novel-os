import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check each nginx config file
for conf in ['api.conf', 'mcp.conf', 'ruoyi.conf', 'agentmemory.conf']:
    stdin, stdout, stderr = ssh.exec_command(
        f'docker exec nginx cat /etc/nginx/conf.d/{conf} 2>&1',
        timeout=10
    )
    print(f"=== {conf} ===")
    print(stdout.read().decode())

# Check what's listening on 48084
stdin, stdout, stderr = ssh.exec_command(
    'netstat -tlnp | grep 48084 || ss -tlnp | grep 48084',
    timeout=10
)
print("=== Port 48084 ===")
print(stdout.read().decode())

# Check all nginx listening ports
stdin, stdout, stderr = ssh.exec_command(
    'docker exec nginx netstat -tlnp 2>/dev/null || docker exec nginx ss -tlnp 2>/dev/null',
    timeout=10
)
print("=== Nginx ports ===")
print(stdout.read().decode())

ssh.close()
