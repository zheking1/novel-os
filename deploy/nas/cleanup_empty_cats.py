import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Delete all empty categories (no items, no children with items)
delete_sql = """
-- First, get all category IDs that have items
WITH categories_with_items AS (
    SELECT DISTINCT category_id FROM universal_knowledge WHERE category_id IS NOT NULL
),
-- Get all ancestor categories of categories with items
ancestor_categories AS (
    SELECT c.id FROM ref_categories c
    WHERE c.id IN (SELECT category_id FROM categories_with_items)
    UNION
    SELECT c.parent_id FROM ref_categories c
    WHERE c.id IN (SELECT category_id FROM categories_with_items) AND c.parent_id IS NOT NULL
)
-- Delete categories that have no items and are not ancestors of categories with items
DELETE FROM ref_categories
WHERE id NOT IN (SELECT id FROM ancestor_categories)
AND id NOT IN (SELECT category_id FROM universal_knowledge WHERE category_id IS NOT NULL);
"""

stdin, stdout, stderr = ssh.exec_command(
    "docker exec -i novel-postgres psql -U novel_os -d novel_os",
    timeout=15
)
stdin.write(delete_sql)
stdin.channel.shutdown_write()
out = stdout.read().decode()
err = stderr.read().decode()
print("=== Delete empty categories ===")
print(out)
if err and "NOTICE" not in err:
    print("=== Error ===")
    print(err)

# Verify final structure
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
