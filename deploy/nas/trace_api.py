import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Simulate what kb.category.list returns (include_all=True)
# This is what kb.category.tree calls
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT json_agg(row_to_json(t)) FROM (SELECT rc.id::text, rc.slug, rc.name, rc.description, rc.parent_id::text, rc.genre_tags, rc.sort_order, rc.is_system, (SELECT COUNT(*) FROM ref_categories child WHERE child.parent_id = rc.id) as child_count FROM ref_categories rc ORDER BY rc.sort_order) t;\"",
    timeout=15
)
raw = stdout.read().decode().strip()
print("=== API Response (kb.category.tree) ===")
try:
    data = json.loads(raw)
    if data and len(data) > 0:
        print(f"Total categories: {len(data)}")
        for cat in data:
            parent = cat.get('parent_id', 'NULL')
            if parent is None:
                parent = 'NULL'
            print(f"  slug={cat['slug']:25s} name={cat['name']:15s} parent={parent:40s} child_count={cat['child_count']}")
except Exception as e:
    print(f"Parse error: {e}")
    print(f"Raw: {raw[:500]}")

ssh.close()
