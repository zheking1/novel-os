import paramiko

def run(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode(), stderr.read().decode()

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)
    
    print("=== 容器内根目录 ===")
    cmd = "docker exec novel-os-mcp ls -la /"
    out, err = run(ssh, cmd)
    print(out)
    
    print("\n=== 容器内home目录 ===")
    cmd = "docker exec novel-os-mcp ls -la /home/"
    out, err = run(ssh, cmd)
    print(out)
    
    print("\n=== 容器内app目录 ===")
    cmd = "docker exec novel-os-mcp ls -la /app/"
    out, err = run(ssh, cmd)
    print(out)
    
    print("\n=== docker-compose配置 ===")
    cmd = "cat /opt/novel-os/docker-compose.yml"
    out, err = run(ssh, cmd)
    print(out)
    
    ssh.close()

if __name__ == '__main__':
    main()
