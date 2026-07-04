import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Drop existing tables
drop_sql = """
DROP TABLE IF EXISTS setting_index CASCADE;
DROP TABLE IF EXISTS review_index CASCADE;
DROP TABLE IF EXISTS chapter_index CASCADE;
DROP TABLE IF EXISTS local_projects CASCADE;
"""
cmd = f"docker exec novel-postgres psql -U novel_os -d novel_os -c \"{drop_sql}\""
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
print("=== Drop ===")
print(stdout.read().decode())

# Run fixed migration
with open(r'D:\Project\novels codex\deploy\nas\postgres\migrations\206_local_storage_index.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

# Use file-based approach to avoid escaping issues
stdin, stdout, stderr = ssh.exec_command(
    "docker exec -i novel-postgres psql -U novel_os -d novel_os",
    timeout=30
)
stdin.write(sql)
stdin.channel.shutdown_write()
out = stdout.read().decode()
err = stderr.read().decode()
print("=== Migration ===")
print(out)
if err and "NOTICE" not in err:
    print("=== Error ===")
    print(err)

ssh.close()
