import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Get all knowledge items with full content
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT uk.id::text, uk.topic, uk.summary, uk.content, rc.slug as category_slug FROM universal_knowledge uk LEFT JOIN ref_categories rc ON uk.category_id = rc.id WHERE uk.status = 'active' ORDER BY rc.slug, uk.id;\" -t -A",
    timeout=30
)
rows = stdout.read().decode().strip().split('\n')
items = []
for row in rows:
    if row.strip():
        parts = row.split('|')
        if len(parts) >= 5:
            items.append({
                'id': parts[0],
                'topic': parts[1][:300] if parts[1] else '',
                'summary': parts[2][:300] if parts[2] else '',
                'content': parts[3][:1000] if parts[3] else '',
                'category': parts[4],
            })

print(f"Total items: {len(items)}")

# Group by category
from collections import Counter
cat_counts = Counter(i['category'] for i in items)
print("\n=== Items by category ===")
for cat, count in cat_counts.most_common():
    print(f"  {cat}: {count}")

# Save to file
with open(r'D:\Project\novels codex\deploy\nas\knowledge_data.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
print(f"\nSaved {len(items)} items to knowledge_data.json")

ssh.close()
