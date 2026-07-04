import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Test uk_search with parent category
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT COUNT(*) as total FROM universal_knowledge uk JOIN ref_categories rc ON uk.category_id = rc.id WHERE rc.slug = 'plot_trope' OR rc.parent_id IN (SELECT id FROM ref_categories WHERE slug = 'plot_ref');\"",
    timeout=15
)
print("=== plot_ref items (including children) ===")
print(stdout.read().decode())

# Test knowledge.item.list with parent category
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT COUNT(*) as total FROM knowledge_items k JOIN ref_categories c ON k.category_id = c.id WHERE c.slug = 'plot_trope' OR c.parent_id IN (SELECT id FROM ref_categories WHERE slug = 'plot_ref');\"",
    timeout=15
)
print("=== knowledge_items in plot_ref ===")
print(stdout.read().decode())

# Check all categories with items
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT c.slug, c.name, p.slug as parent, COUNT(uk.id) as items FROM ref_categories c LEFT JOIN universal_knowledge uk ON uk.category_id = c.id LEFT JOIN ref_categories p ON c.parent_id = p.id GROUP BY c.id, c.slug, c.name, p.slug HAVING COUNT(uk.id) > 0 ORDER BY items DESC;\"",
    timeout=15
)
print("=== Categories with items ===")
print(stdout.read().decode())

ssh.close()
