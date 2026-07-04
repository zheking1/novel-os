import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Get categories as JSON
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT row_to_json(t) FROM (SELECT rc.id::text, rc.slug, rc.name, rc.description, rc.parent_id::text, rc.genre_tags, rc.sort_order, rc.is_system, (SELECT COUNT(*) FROM ref_categories child WHERE child.parent_id = rc.id) as child_count FROM ref_categories rc ORDER BY rc.sort_order) t;\" -t -A",
    timeout=15
)
rows = stdout.read().decode().strip().split('\n')
print("=== API Response (kb.category.tree) ===")
print(f"Total categories: {len([r for r in rows if r.strip()])}")
for row in rows:
    if row.strip():
        try:
            cat = json.loads(row)
            parent = cat.get('parent_id') or 'NULL'
            print(f"  slug={cat['slug']:25s} name={cat['name']:15s} parent={parent:40s} child_count={cat['child_count']}")
        except:
            print(f"  Parse error: {row[:100]}")

ssh.close()
