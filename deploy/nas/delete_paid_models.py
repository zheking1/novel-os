import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Delete paid models (OpenAI GPT-4)
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"DELETE FROM model_profiles WHERE provider = 'openai' OR profile_key = 'test_model_draft'\""
)
print("=== Delete Result ===")
print(stdout.read().decode())
print(stderr.read().decode())

# Show remaining active models
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT profile_key, display_name, provider, model_name, status, is_default FROM model_profiles WHERE status = 'active' ORDER BY is_default DESC, profile_key\""
)
print("=== Remaining Active Models ===")
print(stdout.read().decode())

ssh.close()
print("Done!")
