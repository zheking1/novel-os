import paramiko

def run(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode(), stderr.read().decode()

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)
    
    print("=== Docker容器 ===")
    out, err = run(ssh, 'docker ps')
    print(out)
    if err:
        print("错误:", err)
    
    print("\n=== SQL文件位置 ===")
    out, err = run(ssh, 'find /opt/novel-os -name "*.sql" 2>/dev/null | head -20')
    print(out)
    
    print("\n=== PRESETS.md位置 ===")
    out, err = run(ssh, 'find /opt/novel-os -name "PRESETS.md" 2>/dev/null')
    print(out)
    
    print("\n=== 目录结构 ===")
    out, err = run(ssh, 'ls -la /opt/novel-os/')
    print(out)
    
    print("\n=== scripts目录 ===")
    out, err = run(ssh, 'ls -la /opt/novel-os/scripts/')
    print(out)
    
    ssh.close()

if __name__ == '__main__':
    main()
