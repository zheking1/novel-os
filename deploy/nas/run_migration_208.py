import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

with open(r'D:\Project\novels codex\deploy\nas\postgres\migrations\208_restructure_knowledge_categories.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

stdin, stdout, stderr = ssh.exec_command(
    "docker exec -i novel-postgres psql -U novel_os -d novel_os",
    timeout=30
)
stdin.write(sql)
stdin.channel.shutdown_write()
out = stdout.read().decode()
err = stderr.read().decode()
print("=== Migration 208 ===")
print(out)
if err and "NOTICE" not in err:
    print("=== Error ===")
    print(err)

# Verify
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT slug, name FROM ref_categories WHERE parent_id IS NULL ORDER BY sort_order;\"",
    timeout=15
)
print("=== New top-level categories ===")
print(stdout.read().decode())

ssh.close()
