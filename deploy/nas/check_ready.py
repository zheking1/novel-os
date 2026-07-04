import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Check projects
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT slug, title, description FROM projects WHERE status = 'active' LIMIT 5\""
)
print("=== Projects ===")
print(stdout.read().decode())

# Check skills
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT name, is_active FROM skills WHERE is_active = true ORDER BY name\""
)
print("=== Skills ===")
print(stdout.read().decode())

# Check knowledge count
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT COUNT(*) as uk_entries FROM universal_knowledge WHERE status = 'active'\""
)
print("=== Knowledge Base ===")
print(stdout.read().decode())

# Check prompt templates
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT template_key, name, template_type FROM prompt_templates LIMIT 5\""
)
print("=== Prompt Templates ===")
print(stdout.read().decode())

ssh.close()
