import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check current category distribution
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT c.slug, c.name, COUNT(uk.id) as item_count FROM ref_categories c LEFT JOIN universal_knowledge uk ON uk.category_id = c.id WHERE c.parent_id IS NULL GROUP BY c.id, c.slug, c.name ORDER BY item_count DESC;\"",
    timeout=15
)
print("=== Old category item counts ===")
print(stdout.read().decode())

# Check which category_id maps to which slug
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT id, slug, name FROM ref_categories WHERE parent_id IS NULL ORDER BY slug;\"",
    timeout=15
)
print("=== Category IDs ===")
print(stdout.read().decode())

ssh.close()
