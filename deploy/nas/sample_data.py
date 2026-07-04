import paramiko, json
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Get sample items from each category
for cat in ['plot_trope', 'char_template', 'geography', 'char_personality', 'special_item', 'structure_template', 'style_guide', 'writing_ref', 'naming_rules']:
    stdin, stdout, stderr = ssh.exec_command(
        f"docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT uk.id::text, uk.topic, uk.summary, uk.content FROM universal_knowledge uk JOIN ref_categories rc ON uk.category_id = rc.id WHERE rc.slug = '{cat}' AND uk.status = 'active' ORDER BY uk.topic LIMIT 5;\" -t -A",
        timeout=15
    )
    rows = stdout.read().decode().strip().split('\n')
    print(f"\n=== {cat} (sample) ===")
    for row in rows:
        if row.strip():
            parts = row.split('|')
            if len(parts) >= 4:
                print(f"  ID: {parts[0]}")
                print(f"  Topic: {parts[1][:100]}")
                print(f"  Summary: {parts[2][:150] if parts[2] else 'N/A'}")
                print(f"  Content: {parts[3][:200] if parts[3] else 'N/A'}")
                print()

ssh.close()
