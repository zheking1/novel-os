import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def run(ssh, cmd):
    stdin, stdout, stderr = ssh.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace'), stderr.read().decode('utf-8', errors='replace')

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)
    
    print("=== 检查knowledge_base表结构 ===")
    cmd = "docker exec novel-postgres psql -U novel_os -d novel_os -c \"\\d knowledge_base\""
    out, err = run(ssh, cmd)
    print(out)
    if err:
        print("错误:", err)
    
    print("\n=== 添加code字段唯一约束 ===")
    cmd = "docker exec novel-postgres psql -U novel_os -d novel_os -c \"ALTER TABLE knowledge_base ADD CONSTRAINT unique_code UNIQUE (code);\""
    out, err = run(ssh, cmd)
    print("输出:", out)
    if err:
        print("错误:", err)
    
    print("\n=== 再次执行导入脚本 ===")
    cmd = "docker exec -i novel-os-mcp python /app/import_presets_data.py --file /app/PRESETS.md"
    out, err = run(ssh, cmd)
    print("===== 脚本输出 =====")
    print(out)
    if err:
        print("===== 错误信息 =====")
        print(err)
    
    print("\n=== 验证导入结果 ===")
    cmd = "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT count(*) FROM knowledge_base;\""
    out, err = run(ssh, cmd)
    print("知识库条目总数:", out)
    
    cmd = "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT slug, name, count(*) as cnt FROM categories c LEFT JOIN knowledge_base kb ON c.id = kb.category_id GROUP BY c.slug, c.name ORDER BY cnt DESC LIMIT 25;\""
    out, err = run(ssh, cmd)
    print("\n各分类数据统计:")
    print(out)
    
    ssh.close()

if __name__ == '__main__':
    main()
