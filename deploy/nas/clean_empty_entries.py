import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Find entries with empty content
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT COUNT(*) FROM universal_knowledge WHERE (content IS NULL OR content = '' OR content = topic) AND status = 'active';\"",
    timeout=15
)
print("=== Empty content entries ===")
print(stdout.read().decode())

# Delete them
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"DELETE FROM universal_knowledge WHERE (content IS NULL OR content = '' OR content = topic) AND status = 'active';\"",
    timeout=15
)
print("=== Delete result ===")
print(stdout.read().decode())

# Verify
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT COUNT(*) as total, COUNT(CASE WHEN content IS NOT NULL AND content != '' AND content != topic THEN 1 END) as with_content FROM universal_knowledge WHERE status = 'active';\"",
    timeout=15
)
print("=== After cleanup ===")
print(stdout.read().decode())

# Show category distribution
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT c.slug, c.name, p.slug as parent, COUNT(uk.id) as items FROM ref_categories c LEFT JOIN ref_categories p ON c.parent_id = p.id LEFT JOIN universal_knowledge uk ON uk.category_id = c.id GROUP BY c.id, c.slug, c.name, p.slug HAVING COUNT(uk.id) > 0 ORDER BY items DESC;\"",
    timeout=15
)
print("=== Final distribution ===")
print(stdout.read().decode())

ssh.close()
