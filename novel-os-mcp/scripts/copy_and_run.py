import paramiko

def run(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode(), stderr.read().decode()

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)
    
    print("=== 步骤1: 将脚本复制到容器内 ===")
    cmd = "docker cp /opt/novel-os/scripts/import_presets_data.py novel-os-mcp:/app/"
    out, err = run(ssh, cmd)
    print("输出:", out)
    if err:
        print("错误:", err)
    
    print("\n=== 步骤2: 将PRESETS.md复制到容器内 ===")
    cmd = "docker cp /opt/novel-os/Github/PRESETS.md novel-os-mcp:/app/"
    out, err = run(ssh, cmd)
    print("输出:", out)
    if err:
        print("错误:", err)
    
    print("\n=== 步骤3: 在容器内执行导入脚本 ===")
    cmd = "docker exec -i novel-os-mcp python /app/import_presets_data.py --file /app/PRESETS.md"
    out, err = run(ssh, cmd)
    print("输出:", out)
    if err:
        print("错误:", err)
    
    ssh.close()

if __name__ == '__main__':
    main()
