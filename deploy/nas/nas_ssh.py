#!/usr/bin/env python3
import sys
import paramiko

NAS_HOST = '${NAS_HOST}'
NAS_PORT = 22
NAS_USER = 'root'
NAS_PASSWORD = '${NAS_SSH_PASSWORD}'

def ssh_exec(command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(NAS_HOST, port=NAS_PORT, username=NAS_USER, password=NAS_PASSWORD, timeout=10)
        stdin, stdout, stderr = ssh.exec_command(command, timeout=60)
        stdout.channel.set_combine_stderr(True)
        output = stdout.read().decode('utf-8', errors='replace')
        return output.strip()
    finally:
        ssh.close()

def ssh_exec_long(command):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(NAS_HOST, port=NAS_PORT, username=NAS_USER, password=NAS_PASSWORD, timeout=10)
        stdin, stdout, stderr = ssh.exec_command(command)
        stdout.channel.set_combine_stderr(True)
        for line in iter(stdout.readline, ''):
            print(line, end='')
        return stdout.channel.recv_exit_status()
    finally:
        ssh.close()

def ssh_scp(local_path, remote_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(NAS_HOST, port=NAS_PORT, username=NAS_USER, password=NAS_PASSWORD, timeout=10)
        sftp = ssh.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
        print(f"✅ 文件已上传: {local_path} -> {remote_path}")
    finally:
        ssh.close()

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python nas_ssh.py exec <command>        - 执行SSH命令")
        print("  python nas_ssh.py exec_long <command>  - 执行长时间SSH命令（实时输出）")
        print("  python nas_ssh.py scp <local> <remote> - 上传文件")
        print("  python nas_ssh.py docker_ps            - 查看Docker容器状态")
        print("  python nas_ssh.py deploy_import        - 部署并执行导入脚本")
        print("  python nas_ssh.py import               - 执行数据导入")
        print("  python nas_ssh.py verify               - 验证数据分类")
        return
    
    action = sys.argv[1]
    
    if action == 'exec':
        if len(sys.argv) < 3:
            print("缺少命令参数")
            return
        command = ' '.join(sys.argv[2:])
        result = ssh_exec(command)
        print(result)
    
    elif action == 'exec_long':
        if len(sys.argv) < 3:
            print("缺少命令参数")
            return
        command = ' '.join(sys.argv[2:])
        ssh_exec_long(command)
    
    elif action == 'scp':
        if len(sys.argv) < 4:
            print("缺少文件路径参数")
            return
        local_path = sys.argv[2]
        remote_path = sys.argv[3]
        ssh_scp(local_path, remote_path)
    
    elif action == 'docker_ps':
        result = ssh_exec('cd /opt/novel-os && docker compose ps')
        print(result)
    
    elif action == 'deploy_import':
        print("📦 创建目录...")
        ssh_exec('mkdir -p /opt/novel-os/deploy/nas')
        print("📦 上传导入脚本...")
        ssh_scp('deploy/nas/import_opencode_subcategory.py', '/opt/novel-os/deploy/nas/import_opencode_subcategory.py')
        print("📦 安装依赖...")
        ssh_exec('pip3 install asyncpg -q')
        print("\n🚀 执行数据导入...")
        ssh_exec_long('cd /opt/novel-os && python3 deploy/nas/import_opencode_subcategory.py')
    
    elif action == 'import':
        print("🚀 执行数据导入...")
        ssh_exec_long('cd /opt/novel-os && python3 deploy/nas/import_opencode_subcategory.py')
    
    elif action == 'verify':
        print("📊 验证数据分类...")
        command = '''cd /opt/novel-os && docker compose exec -T postgres psql -U novel_os -d novel_os <<'SQL'
SELECT c.slug, c.name, c.level, COUNT(k.id) as count
FROM categories c
LEFT JOIN knowledge_base k ON k.category_id = c.id AND k.source = 'opencode'
GROUP BY c.id, c.slug, c.name, c.level
ORDER BY c.level, c.sort_order;
SQL'''
        result = ssh_exec(command)
        print(result)
    
    elif action == 'presets_import':
        print("📦 上传PRESETS.md...")
        ssh_scp('Github/PRESETS.md', '/opt/novel-os/Github/PRESETS.md')
        print("📦 上传导入脚本...")
        ssh_scp('deploy/nas/import_presets.py', '/opt/novel-os/deploy/nas/import_presets.py')
        print("\n🚀 执行PRESETS导入...")
        ssh_exec_long('cd /opt/novel-os && python3 deploy/nas/import_presets.py')
    
    elif action == 'presets_verify':
        print("📊 验证PRESETS导入...")
        command = '''cd /opt/novel-os && docker compose exec -T postgres psql -U novel_os -d novel_os <<'SQL'
SELECT c.slug, c.name, COUNT(k.id) as count
FROM categories c
LEFT JOIN knowledge_base k ON k.category_id = c.id AND k.source = 'presets'
GROUP BY c.id, c.slug, c.name
ORDER BY count DESC
LIMIT 30;
SQL'''
        result = ssh_exec(command)
        print(result)
    
    else:
        print(f"未知操作: {action}")

if __name__ == "__main__":
    main()