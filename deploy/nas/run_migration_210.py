import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

with open(r'D:\Project\novels codex\deploy\nas\postgres\migrations\210_restructure_categories.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

stdin, stdout, stderr = ssh.exec_command(
    "docker exec -i novel-postgres psql -U novel_os -d novel_os",
    timeout=30
)
stdin.write(sql)
stdin.channel.shutdown_write()
out = stdout.read().decode()
err = stderr.read().decode()
print("=== Migration 210 ===")
print(out)
if err and "NOTICE" not in err:
    print("=== Error ===")
    print(err)

# Verify
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT c.slug, c.name, p.slug as parent, COUNT(uk.id) as items FROM ref_categories c LEFT JOIN ref_categories p ON c.parent_id = p.id LEFT JOIN universal_knowledge uk ON uk.category_id = c.id GROUP BY c.id, c.slug, c.name, p.slug HAVING COUNT(uk.id) > 0 ORDER BY items DESC;\"",
    timeout=15
)
print("=== Categories with items ===")
print(stdout.read().decode())

ssh.close()
