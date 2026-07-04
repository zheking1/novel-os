import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check categories table (used by knowledge.category.list)
print("=" * 60)
print("categories table (knowledge.category.list)")
print("=" * 60)
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT id::text, slug, name, parent_id::text, p.slug as parent_slug, level FROM categories c LEFT JOIN categories p ON c.parent_id = p.id ORDER BY c.sort_order, c.name;\"",
    timeout=15
)
print(stdout.read().decode())

# Check ref_categories table (used by kb.category.list/tree)
print("=" * 60)
print("ref_categories table (kb.category.list/tree)")
print("=" * 60)
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT id::text, slug, name, parent_id::text, p.slug as parent_slug FROM ref_categories c LEFT JOIN ref_categories p ON c.parent_id = p.id ORDER BY c.sort_order;\"",
    timeout=15
)
print(stdout.read().decode())

# Count items in each
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT 'categories' as tbl, COUNT(*) FROM categories UNION ALL SELECT 'ref_categories', COUNT(*) FROM ref_categories;\"",
    timeout=15
)
print("=== Table counts ===")
print(stdout.read().decode())

ssh.close()
