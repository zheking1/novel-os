import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Check new categories
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT c.slug, c.name, c.parent_id::text, p.slug as parent_slug FROM ref_categories c LEFT JOIN ref_categories p ON c.parent_id = p.id WHERE p.slug IN ('character_ref','equipment','creature','world_setting','power_system','history_culture','plot_ref','writing_ref','general_material') ORDER BY p.sort_order, c.sort_order;\"",
    timeout=15
)
print("=== New categories ===")
print(stdout.read().decode())

ssh.close()
