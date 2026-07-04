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
    
    print("=== 检查新分类数据（使用正确的关联方式）===")
    cmd = """
    docker exec novel-postgres psql -U novel_os -d novel_os -c "
        SELECT 
            c.slug, 
            c.name, 
            count(kb.id) as cnt
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
    print(out)
    if err:
        print("错误:", err)
    
    print("\n=== 检查分类是否存在 ===")
    cmd = """
    docker exec novel-postgres psql -U novel_os -d novel_os -c "
        SELECT id, slug, name, parent_id FROM categories 
        WHERE slug IN ('narrative_structure', 'core_conflict', 'world_tone')
        ORDER BY slug;
    "
    """
    out, err = run(ssh, cmd)
    print(out)
    
    print("\n=== 检查知识库条目的category_id ===")
    cmd = """
    docker exec novel-postgres psql -U novel_os -d novel_os -c "
        SELECT kb.code, kb.title, kb.category_id, c.name as category_name
        FROM knowledge_base kb 
        LEFT JOIN categories c ON kb.category_id = c.id 
        WHERE kb.code LIKE 'PR%' 
        LIMIT 10;
    "
    """
    out, err = run(ssh, cmd)
    print(out)
    
    print("\n=== 检查总数据量 ===")
    cmd = "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT count(*) FROM knowledge_base WHERE code LIKE 'PR%';\""
    out, err = run(ssh, cmd)
    print("PRESETS导入的数据量:", out)
    
    ssh.close()

if __name__ == '__main__':
    main()
