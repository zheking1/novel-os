import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

stdin, stdout, stderr = ssh.exec_command(
    "grep -c 'knowledge-pack' /opt/novel-os/novel-os-web/index.html",
    timeout=10
)
print("NAS file knowledge-pack count:", stdout.read().decode().strip())

stdin, stdout, stderr = ssh.exec_command(
    "grep -c '知识包' /opt/novel-os/novel-os-web/index.html",
    timeout=10
)
print("NAS file 知识包 count:", stdout.read().decode().strip())

ssh.close()
