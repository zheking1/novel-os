import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check what kb.category.list returns
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT id::text, slug, name, parent_id::text, sort_order FROM ref_categories ORDER BY sort_order;\" -t -A",
    timeout=15
)
rows = stdout.read().decode().strip().split('\n')
print("=== All categories in DB ===")
for row in rows:
    if row.strip():
        parts = row.split('|')
        if len(parts) >= 4:
            print(f"  slug={parts[1]}, name={parts[2]}, parent={parts[3]}")

ssh.close()
