import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Step 1: Check ALL categories in DB
print("=" * 60)
print("STEP 1: Database - All categories")
print("=" * 60)
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT id::text, slug, name, parent_id::text, sort_order FROM ref_categories ORDER BY sort_order;\" -t -A",
    timeout=15
)
rows = stdout.read().decode().strip().split('\n')
for row in rows:
    if row.strip():
        parts = row.split('|')
        if len(parts) >= 4:
            pid = parts[3] if parts[3] else 'NULL'
            print(f"  slug={parts[1]:25s} name={parts[2]:15s} parent={pid}")

# Step 2: Check parent-child relationships
print("\n" + "=" * 60)
print("STEP 2: Parent-child relationships")
print("=" * 60)
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT c.slug as child, p.slug as parent FROM ref_categories c LEFT JOIN ref_categories p ON c.parent_id = p.id WHERE c.parent_id IS NOT NULL ORDER BY p.slug, c.sort_order;\"",
    timeout=15
)
print(stdout.read().decode())

# Step 3: Check if kb.category.tree API works
print("=" * 60)
print("STEP 3: Test kb.category.list include_all")
print("=" * 60)
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT rc.id::text, rc.slug, rc.name, rc.parent_id::text, (SELECT COUNT(*) FROM ref_categories child WHERE child.parent_id = rc.id) as child_count FROM ref_categories rc ORDER BY rc.sort_order;\"",
    timeout=15
)
print(stdout.read().decode())

ssh.close()
