import paramiko

def run(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode(), stderr.read().decode()

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)
    
    print("=== 容器内目录结构 ===")
    cmd = "docker exec novel-os-mcp ls -la /opt/novel-os/"
    out, err = run(ssh, cmd)
    print(out)
    if err:
        print("错误:", err)
    
    print("\n=== 容器内scripts目录 ===")
    cmd = "docker exec novel-os-mcp ls -la /opt/novel-os/scripts/"
    out, err = run(ssh, cmd)
    print(out)
    
    print("\n=== 容器内Github目录 ===")
    cmd = "docker exec novel-os-mcp ls -la /opt/novel-os/Github/"
    out, err = run(ssh, cmd)
    print(out)
    
    ssh.close()

if __name__ == '__main__':
    main()
