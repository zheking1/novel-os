import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check items in old writing category
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT uk.id, uk.topic, uk.category_id, rc.slug as old_slug FROM universal_knowledge uk JOIN ref_categories rc ON uk.category_id = rc.id WHERE rc.slug IN ('writing','era','genre','history','professional') LIMIT 20;\"",
    timeout=15
)
print("=== Items in old categories ===")
print(stdout.read().decode())

# Check items in old child categories
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT uk.id, uk.topic, uk.category_id, rc.slug as old_slug FROM universal_knowledge uk JOIN ref_categories rc ON uk.category_id = rc.id WHERE rc.slug LIKE 'kb_%' OR rc.slug IN ('politics','economy','society','culture','technology','xianxia','xuanhuan','scifi','horror','post_apocalyptic','game','urban','historical_figure','historical_event','historical_process','historical_geo') LIMIT 30;\"",
    timeout=15
)
print("=== Items in old child categories ===")
print(stdout.read().decode())

ssh.close()
