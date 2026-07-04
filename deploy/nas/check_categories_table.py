import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check categories table - top level only
print("=== categories (top-level, parent_id IS NULL) ===")
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT slug, name, parent_id::text, level FROM categories WHERE parent_id IS NULL ORDER BY sort_order LIMIT 20;\"",
    timeout=15
)
print(stdout.read().decode())

# Check categories - count by level
print("=== categories by level ===")
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT level, COUNT(*) FROM categories GROUP BY level ORDER BY level;\"",
    timeout=15
)
print(stdout.read().decode())

# Check categories - sample with parent
print("=== categories (with parent, sample) ===")
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT c.slug, c.name, c.parent_id::text, p.slug as parent_slug, c.level FROM categories c LEFT JOIN categories p ON c.parent_id = p.id WHERE c.parent_id IS NOT NULL ORDER BY c.level, c.sort_order LIMIT 30;\"",
    timeout=15
)
print(stdout.read().decode())

ssh.close()
