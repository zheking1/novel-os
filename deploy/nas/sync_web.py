import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)
sftp = ssh.open_sftp()

# Upload index.html
local = r'D:\Project\novels codex\novel-os-web\index.html'
remote = '/opt/novel-os/novel-os-web/index.html'
sftp.put(local, remote)
print("index.html uploaded")

sftp.close()
ssh.close()
print("Done!")
