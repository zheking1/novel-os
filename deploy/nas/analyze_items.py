import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Get all items from plot_trope to analyze and re-categorize
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT uk.id::text, uk.topic, uk.summary, uk.content FROM universal_knowledge uk JOIN ref_categories rc ON uk.category_id = rc.id WHERE rc.slug = 'plot_trope' AND uk.status = 'active' ORDER BY uk.id;\" -t -A",
    timeout=30
)
rows = stdout.read().decode().strip().split('\n')
print(f"plot_trope items: {len([r for r in rows if r.strip()])}")

# Get all items from char_template
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT uk.id::text, uk.topic, uk.summary FROM universal_knowledge uk JOIN ref_categories rc ON uk.category_id = rc.id WHERE rc.slug = 'char_template' AND uk.status = 'active' ORDER BY uk.id;\" -t -A",
    timeout=15
)
rows = stdout.read().decode().strip().split('\n')
print(f"char_template items: {len([r for r in rows if r.strip()])}")

# Get all items from geography
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT uk.id::text, uk.topic, uk.summary FROM universal_knowledge uk JOIN ref_categories rc ON uk.category_id = rc.id WHERE rc.slug = 'geography' AND uk.status = 'active' ORDER BY uk.id;\" -t -A",
    timeout=15
)
rows = stdout.read().decode().strip().split('\n')
print(f"geography items: {len([r for r in rows if r.strip()])}")

ssh.close()
