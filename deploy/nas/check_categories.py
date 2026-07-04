import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check current categories
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT id, slug, name, parent_id::text FROM ref_categories WHERE parent_id IS NULL ORDER BY sort_order LIMIT 20;\"",
    timeout=15
)
print("=== Current top-level categories ===")
print(stdout.read().decode())

# Check child categories
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT c.slug, c.name, c.parent_id::text, p.slug as parent_slug FROM ref_categories c LEFT JOIN ref_categories p ON c.parent_id = p.id WHERE c.parent_id IS NOT NULL ORDER BY p.slug, c.sort_order LIMIT 50;\"",
    timeout=15
)
print("=== Current child categories ===")
print(stdout.read().decode())

ssh.close()
