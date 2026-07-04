import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

cmd = "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT profile_key, task_types, default_params FROM model_profiles WHERE 'embedding' = ANY(task_types) OR 'rerank' = ANY(task_types)\""
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode('utf-8', errors='replace'))

ssh.close()
