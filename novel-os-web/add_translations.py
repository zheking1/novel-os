path = r'd:\Project\novels codex\novel-os-web\index.html'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

en_options = {
    'option.world': 'world',
    'option.character': 'character',
    'option.magic': 'magic',
    'option.timeline': 'timeline',
    'option.setting': 'setting',
    'option.other': 'other',
    'option.active': 'active',
    'option.draft': 'draft',
    'option.archived': 'archived',
    'option.global': 'global',
    'option.volume': 'volume',
    'option.chapter': 'chapter',
    'option.faction': 'faction',
    'option.location': 'location',
    'option.item': 'item',
    'option.inactive': 'inactive',
    'option.deceased': 'deceased',
    'option.low': 'low',
    'option.medium': 'medium',
    'option.high': 'high',
    'option.critical': 'critical',
    'option.persistent': 'persistent',
    'option.temporary': 'temporary',
    'option.scene': 'scene',
    'option.friend': 'friend',
    'option.enemy': 'enemy',
    'option.family': 'family',
    'option.mentor': 'mentor',
    'option.student': 'student',
    'option.allied': 'allied',
    'option.romantic': 'romantic',
    'option.positive': 'positive',
    'option.neutral': 'neutral',
    'option.negative': 'negative',
    'option.ambivalent': 'ambivalent',
}

zh_options = {
    'option.world': '世界观',
    'option.character': '人物',
    'option.magic': '法术',
    'option.timeline': '时间线',
    'option.setting': '设定',
    'option.other': '其他',
    'option.active': '启用',
    'option.draft': '草稿',
    'option.archived': '归档',
    'option.global': '全局',
    'option.volume': '卷',
    'option.chapter': '章',
    'option.faction': '势力',
    'option.location': '地点',
    'option.item': '物品',
    'option.inactive': '停用',
    'option.deceased': '已故',
    'option.low': '低',
    'option.medium': '中',
    'option.high': '高',
    'option.critical': '关键',
    'option.persistent': '持续',
    'option.temporary': '临时',
    'option.scene': '场景',
    'option.friend': '朋友',
    'option.enemy': '敌人',
    'option.family': '家人',
    'option.mentor': '导师',
    'option.student': '学生',
    'option.allied': '盟友',
    'option.romantic': '恋爱',
    'option.positive': '正面',
    'option.neutral': '中立',
    'option.negative': '负面',
    'option.ambivalent': '矛盾',
}

en_marker = '"option.proposed":'
en_insert = '\n'.join([f'        "{k}": "{v}",' for k, v in en_options.items()])
content = content.replace(en_marker, en_insert + '\n        "option.proposed":')

zh_marker = '"option.proposed": "提案中",'
zh_insert = '\n'.join([f'        "{k}": "{v}",' for k, v in zh_options.items()])
content = content.replace(zh_marker, zh_insert + '\n        "option.proposed": "提案中",')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Added translations')