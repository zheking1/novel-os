import os, uuid, psycopg2

conn = psycopg2.connect(host='localhost', port=5432, database='novel_os', user='novel_os', password='${POSTGRES_PASSWORD}')
cur = conn.cursor()

cur.execute('SELECT id, slug FROM categories')
cats = {row[1]: row[0] for row in cur.fetchall()}

genres_dir = '/opt/novel-os/Github/webnovel-writer-opencode-master/.opencode/genres'
refs_dir = '/opt/novel-os/Github/webnovel-writer-opencode-master/.opencode/references'

# 获取当前最大编号
cur.execute("SELECT code FROM knowledge_base WHERE code LIKE 'WLD-%' ORDER BY code DESC LIMIT 1")
last_wld = cur.fetchone()
wld_num = int(last_wld[0].replace('WLD-', '')) if last_wld else 0

cur.execute("SELECT code FROM knowledge_base WHERE code LIKE 'PLT-%' ORDER BY code DESC LIMIT 1")
last_plt = cur.fetchone()
plt_num = int(last_plt[0].replace('PLT-', '')) if last_plt else 0

cur.execute("SELECT code FROM knowledge_base WHERE code LIKE 'RDR-%' ORDER BY code DESC LIMIT 1")
last_rdr = cur.fetchone()
rdr_num = int(last_rdr[0].replace('RDR-', '')) if last_rdr else 0

total = 0
print('=== 导入MD文件 ===')

# 世界观
world_files = [
    ('xuanhuan/power-systems.md', '力量体系设计'),
    ('xuanhuan/cultivation-levels.md', '修炼等级体系'),
    ('period-drama/historical-setting.md', '历史背景设定'),
    ('rules-mystery/core-elements.md', '规则悬疑核心元素'),
]

for fp, title_prefix in world_files:
    filepath = os.path.join(genres_dir, fp)
    if not os.path.exists(filepath):
        print('Missing: ' + fp)
        continue
    if 'world' not in cats:
        print('No world category')
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    title = ''
    for line in lines[:10]:
        if line.startswith('#'):
            title = line.replace('#', '').strip()
            break
    if not title:
        title = title_prefix
    
    wld_num += 1
    code = 'WLD-' + str(wld_num).zfill(3)
    summary = content[:500]
    
    cur.execute('INSERT INTO knowledge_base (id, code, title, content, summary, category_id, source, status, level) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (str(uuid.uuid4()), code, title, content, summary, cats['world'], 'opencode', 'active', 'knowledge'))
    total += 1
    print(fp + ': 1')

# 节模板
plot_files = [
    ('dog-blood-romance/plot-templates.md', '狗血言情剧情模板'),
    ('xuanhuan/xuanhuan-plot-patterns.md', '玄幻情节模式'),
    ('period-drama/plot-patterns.md', '古言情节模式'),
    ('realistic/plot-logic.md', '现实题材情节逻辑'),
    ('zhihu-short/genre-templates.md', '知乎短篇模板'),
]

for fp, title_prefix in plot_files:
    filepath = os.path.join(genres_dir, fp)
    if not os.path.exists(filepath):
        print('Missing: ' + fp)
        continue
    if 'plot_templates' not in cats:
        print('No plot_templates category')
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    title = ''
    for line in lines[:10]:
        if line.startswith('#'):
            title = line.replace('#', '').strip()
            break
    if not title:
        title = title_prefix
    
    plt_num += 1
    code = 'PLT-' + str(plt_num).zfill(3)
    summary = content[:500]
    
    cur.execute('INSERT INTO knowledge_base (id, code, title, content, summary, category_id, source, status, level) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (str(uuid.uuid4()), code, title, content, summary, cats['plot_templates'], 'opencode', 'active', 'knowledge'))
    total += 1
    print(fp + ': 1')

# 读者分析
reader_files = [
    ('reading-power-taxonomy.md', '追读力分类标准'),
    ('genre-profiles.md', '题材画像'),
]

for fp, title_prefix in reader_files:
    filepath = os.path.join(refs_dir, fp)
    if not os.path.exists(filepath):
        print('Missing: ' + fp)
        continue
    if 'reader_analysis' not in cats:
        print('No reader_analysis category')
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    title = ''
    for line in lines[:10]:
        if line.startswith('#'):
            title = line.replace('#', '').strip()
            break
    if not title:
        title = title_prefix
    
    rdr_num += 1
    code = 'RDR-' + str(rdr_num).zfill(3)
    summary = content[:500]
    
    cur.execute('INSERT INTO knowledge_base (id, code, title, content, summary, category_id, source, status, level) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
        (str(uuid.uuid4()), code, title, content, summary, cats['reader_analysis'], 'opencode', 'active', 'knowledge'))
    total += 1
    print(fp + ': 1')

conn.commit()
print('MD导入完成: ' + str(total) + '条')

# 终验
cur.execute('SELECT COUNT(*) FROM knowledge_base')
print('数据库总数: ' + str(cur.fetchone()[0]))

cur.execute('SELECT c.slug, COUNT(kb.id) FROM categories c LEFT JOIN knowledge_base kb ON c.id = kb.category_id GROUP BY c.slug ORDER BY COUNT(kb.id) DESC')
print('=== 各分类数据 ===')
for row in cur.fetchall():
    print(row[0] + ': ' + str(row[1]) + '条')

conn.close()