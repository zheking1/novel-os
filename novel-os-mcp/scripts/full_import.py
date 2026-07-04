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
    
    print("=== 步骤1: 上传更新后的导入脚本 ===")
    sftp = ssh.open_sftp()
    src = r'D:\Project\novels codex\novel-os-mcp\scripts\import_presets_data.py'
    dst = '/opt/novel-os/scripts/import_presets_data.py'
    sftp.put(src, dst)
    print("上传成功")
    sftp.close()
    
    print("\n=== 步骤2: 复制到容器 ===")
    cmd = "docker cp /opt/novel-os/scripts/import_presets_data.py novel-os-mcp:/app/"
    out, err = run(ssh, cmd)
    print("输出:", out)
    
    print("\n=== 步骤3: 删除之前导入的错误数据 ===")
    cmd = "docker exec novel-postgres psql -U novel_os -d novel_os -c \"DELETE FROM knowledge_base WHERE code LIKE 'PR%';\""
    out, err = run(ssh, cmd)
    print("删除结果:", out)
    
    print("\n=== 步骤4: 重新执行导入 ===")
    cmd = "docker exec -i novel-os-mcp python /app/import_presets_data.py --file /app/PRESETS.md"
    out, err = run(ssh, cmd)
    print("===== 脚本输出 =====")
    print(out)
    if err:
        print("===== 错误信息 =====")
        print(err)
    
    print("\n=== 步骤5: 验证导入结果 ===")
    cmd = "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT count(*) FROM knowledge_base WHERE code LIKE 'PR%';\""
    out, err = run(ssh, cmd)
    print("PRESETS导入的数据量:", out)
    
    cmd = """
    docker exec novel-postgres psql -U novel_os -d novel_os -c "
        SELECT c.slug, c.name, count(kb.id) as cnt
        FROM categories c 
        LEFT JOIN knowledge_base kb ON c.id = kb.category_id 
        WHERE c.slug IN (
            'narrative_structure', 'core_conflict', 'world_tone', 'reader_groups',
            'story_complexity', 'writing_technique', 'emotion_driver', 'theme_depth',
            'genre_guide', 'style_categories', 'era_setting', 'narrative_perspective',
            'language_choice', 'identity_occupation', 'platform_style', 'writing_style',
            'title_structure', 'cheat_types', 'male_protagonist', 'female_protagonist',
            'antagonist', 'growth_templates', 'romance_templates', 'adventure_templates',
            'politics_templates', 'mystery_templates', 'daily_templates',
            'setting_background', 'ending_types'
        )
        GROUP BY c.slug, c.name 
        ORDER BY cnt DESC;
    "
    """
    out, err = run(ssh, cmd)
    print("\n各分类数据统计:")
    print(out)
    
    ssh.close()

if __name__ == '__main__':
    main()
