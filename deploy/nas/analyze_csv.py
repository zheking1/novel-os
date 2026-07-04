import csv
from collections import Counter

files = [
    'D:/Project/novels codex/Github/webnovel-writer-opencode-master/.opencode/references/csv/金手指与设定.csv',
    'D:/Project/novels codex/Github/webnovel-writer-opencode-master/.opencode/references/csv/人设与关系.csv',
    'D:/Project/novels codex/Github/webnovel-writer-opencode-master/.opencode/references/csv/题材与调性推理.csv',
    'D:/Project/novels codex/Github/webnovel-writer-opencode-master/.opencode/references/csv/桥段套路.csv',
    'D:/Project/novels codex/Github/webnovel-writer-opencode-master/.opencode/references/csv/爽点与节奏.csv',
    'D:/Project/novels codex/Github/webnovel-writer-opencode-master/.opencode/references/csv/场景写法.csv',
    'D:/Project/novels codex/Github/webnovel-writer-opencode-master/.opencode/references/csv/写作技法.csv',
    'D:/Project/novels codex/Github/webnovel-writer-opencode-master/.opencode/references/csv/命名规则.csv',
    'D:/Project/novels codex/Github/webnovel-writer-opencode-master/.opencode/references/csv/裁决规则.csv',
]

for fp in files:
    filename = fp.split('/')[-1]
    print(f'=== {filename} ===')
    with open(fp, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        print(f'  Columns: {list(reader.fieldnames)}')
        counter = Counter()
        subcats = {}
        for row in reader:
            cat = row.get('分类', '')
            counter[cat] += 1
            if cat not in subcats:
                subcats[cat] = set()
            subcat_fields = ['设定类型', '人设类型', '桥段名称', '爽点名称', '场景名称', '规则名称', '题材名称', '技法名称']
            subcat = ''
            for field in subcat_fields:
                if field in row and row[field]:
                    subcat = row[field]
                    break
            subcats[cat].add(subcat)
        for cat, cnt in counter.most_common():
            print(f'  分类: {cat}, 数量: {cnt}')
            if subcats[cat]:
                examples = [s for s in list(subcats[cat]) if s]
                print(f'  子类型示例: {examples[:5]}')
        print()