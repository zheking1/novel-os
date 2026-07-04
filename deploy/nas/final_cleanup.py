import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Move kb_writing_technique items to writing_ref
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"UPDATE universal_knowledge SET category_id = (SELECT id FROM ref_categories WHERE slug = 'style_guide') WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'kb_writing_technique');\"",
    timeout=15
)
print("=== Move result ===")
print(stdout.read().decode())

# Delete kb_writing_technique
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"DELETE FROM ref_categories WHERE slug = 'kb_writing_technique';\"",
    timeout=15
)
print("=== Delete result ===")
print(stdout.read().decode())

# Final verification
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT c.slug, c.name, COUNT(uk.id) as items FROM ref_categories c LEFT JOIN universal_knowledge uk ON uk.category_id = c.id WHERE c.parent_id IS NULL GROUP BY c.id, c.slug, c.name ORDER BY c.sort_order;\"",
    timeout=15
)
print("=== Final top-level ===")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT c.slug, c.name, COUNT(uk.id) as items FROM ref_categories c LEFT JOIN universal_knowledge uk ON uk.category_id = c.id WHERE c.parent_id IS NOT NULL GROUP BY c.id, c.slug, c.name ORDER BY items DESC;\"",
    timeout=15
)
print("=== Final child categories ===")
print(stdout.read().decode())

ssh.close()
