import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Apply migration 213
with open('D:\\Project\\novels codex\\deploy\\nas\\postgres\\migrations\\213_model_profiles_user_id.sql', 'r') as f:
    sql = f.read()

# Copy to container
stdin, stdout, stderr = ssh.exec_command('cat > /tmp/mig213.sql << \'EOF\'\n' + sql + '\nEOF')
print(stdout.read().decode())
print(stderr.read().decode())

# Execute
stdin, stdout, stderr = ssh.exec_command('docker cp /tmp/mig213.sql novel-postgres:/tmp/ && docker exec novel-postgres psql -U novel_os -d novel_os -f /tmp/mig213.sql')
print("=== Migration Output ===")
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
