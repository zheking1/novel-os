import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Check workspace ID for 'default' slug
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT id::text, slug FROM workspaces WHERE slug = 'default'\""
)
print("=== Default Workspace ===")
print(stdout.read().decode('utf-8', errors='replace'))

# Check all workspaces
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT id::text, slug FROM workspaces LIMIT 5\""
)
print("=== All Workspaces ===")
print(stdout.read().decode('utf-8', errors='replace'))

# Check model_profiles with project workspace
stdin, stdout, stderr = ssh.exec_command(
    """docker exec novel-postgres psql -U novel_os -d novel_os -c "
    SELECT mp.profile_key, mp.project_id::text, p.slug as project_slug, p.workspace_id::text
    FROM model_profiles mp
    JOIN projects p ON mp.project_id = p.id
    LIMIT 10
    " """
)
print("=== Model Profiles with Project Info ===")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
