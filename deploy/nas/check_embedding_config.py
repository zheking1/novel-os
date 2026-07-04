import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Check default_params for embedding models
stdin, stdout, stderr = ssh.exec_command(
    """docker exec novel-postgres psql -U novel_os -d novel_os -c "
    SELECT profile_key, default_params 
    FROM model_profiles 
    WHERE task_types && ARRAY['embedding', 'rerank']::varchar[]
    ORDER BY profile_key
    " """
)
print("=== Embedding/Rerank Config ===")
print(stdout.read().decode('utf-8', errors='replace'))

# Check cost_config for API keys
stdin, stdout, stderr = ssh.exec_command(
    """docker exec novel-postgres psql -U novel_os -d novel_os -c "
    SELECT profile_key, cost_config 
    FROM model_profiles 
    WHERE task_types && ARRAY['embedding', 'rerank']::varchar[]
    ORDER BY profile_key
    " """
)
print("\n=== Cost Config (might have API key) ===")
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
