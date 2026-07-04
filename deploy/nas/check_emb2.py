import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Check all fields for embedding models
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT profile_key, provider, model_name, default_params, cost_config FROM model_profiles WHERE profile_key LIKE '%embed%' OR profile_key LIKE '%rerank%' ORDER BY profile_key\""
)
print("=== Embedding/Rerank Models ===")
out = stdout.read().decode('utf-8', errors='replace')
err = stderr.read().decode('utf-8', errors='replace')
print(out)
if err:
    print("ERR:", err)

ssh.close()
