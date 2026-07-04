import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

with open(r'D:\Project\novels codex\deploy\nas\postgres\migrations\207_knowledge_pack_system.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

stdin, stdout, stderr = ssh.exec_command(
    "docker exec -i novel-postgres psql -U novel_os -d novel_os",
    timeout=30
)
stdin.write(sql)
stdin.channel.shutdown_write()
out = stdout.read().decode()
err = stderr.read().decode()
print("=== Migration 207 ===")
print(out)
if err and "NOTICE" not in err:
    print("=== Error ===")
    print(err)

ssh.close()
