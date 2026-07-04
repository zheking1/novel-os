import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Check prompt templates in DB
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT id::text, template_key, name, template_type, is_active, LENGTH(template_content) as content_len FROM prompt_templates ORDER BY template_key\""
)
print("=== Prompt Templates in DB ===")
print(stdout.read().decode('utf-8', errors='replace'))

# Check if table has project_id column
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"\\d prompt_templates\""
)
print("=== Table Schema ===")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
