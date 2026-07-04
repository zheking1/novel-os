import paramiko

def run(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode(), stderr.read().decode()

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)
    
    print("=== 步骤1: 执行SQL迁移脚本创建分类 ===")
    sql_path = '/opt/novel-os/novel-os-mcp/deploy/nas/postgres/migrations/193_presets_categories.sql'
    cmd = f"cat {sql_path} | docker exec -i novel-postgres psql -U novel_os -d novel_os"
    out, err = run(ssh, cmd)
    print("输出:", out[:500] if out else "无")
    if err:
        print("错误:", err[:500])
    
    print("\n=== 步骤2: 在容器内执行数据导入脚本 ===")
    cmd = "docker exec -i novel-os-mcp python /opt/novel-os/scripts/import_presets_data.py --file /opt/novel-os/Github/PRESETS.md"
    out, err = run(ssh, cmd)
    print("输出:", out)
    if err:
        print("错误:", err)
    
    ssh.close()

if __name__ == '__main__':
    main()
