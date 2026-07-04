import re

path = r'd:\Project\novels codex\novel-os-web\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

select_options = [
    ('all', '全部'),
    ('world', '世界观'),
    ('character', '人物'),
    ('magic', '法术'),
    ('timeline', '时间线'),
    ('setting', '设定'),
    ('other', '其他'),
    ('active', '启用'),
    ('draft', '草稿'),
    ('archived', '归档'),
    ('global', '全局'),
    ('volume', '卷'),
    ('chapter', '章'),
    ('faction', '势力'),
    ('location', '地点'),
    ('item', '物品'),
    ('inactive', '停用'),
    ('deceased', '已故'),
    ('low', '低'),
    ('medium', '中'),
    ('high', '高'),
    ('critical', '关键'),
    ('persistent', '持续'),
    ('temporary', '临时'),
    ('scene', '场景'),
    ('friend', '朋友'),
    ('enemy', '敌人'),
    ('family', '家人'),
    ('mentor', '导师'),
    ('student', '学生'),
    ('allied', '盟友'),
    ('romantic', '恋爱'),
    ('positive', '正面'),
    ('neutral', '中立'),
    ('negative', '负面'),
    ('ambivalent', '矛盾'),
    ('proposed', '提案中'),
    ('approved', '已批准'),
    ('rejected', '已拒绝'),
    ('open', '未完成'),
    ('done', '已完成'),
]

def add_option_i18n(match):
    value = match.group(1)
    original_text = match.group(2).strip()
    
    for en, zh in select_options:
        if value == en or original_text.lower() == en.lower():
            return f'<option value="{value}" data-i18n="option.{value}">{en}</option>'
    
    return match.group(0)

pattern = r'<option\s+value="([^"]*)"[^>]*>([^<]*)</option>'
content = re.sub(pattern, add_option_i18n, content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Added data-i18n to options')