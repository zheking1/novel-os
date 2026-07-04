#!/usr/bin/env python3
import asyncio
import csv
import json
import os
import re
import sys
from pathlib import Path
from uuid import uuid4

import asyncpg

OPENCODE_CSV_DIR = Path('/opt/novel-os/Github/webnovel-writer-opencode-master/.opencode/references/csv')

CSV_CATEGORY_MAP = {
    "命名规则.csv": "naming",
    "写作技法.csv": "writing_technique",
    "桥段套路.csv": "plot_archetype",
    "人设与关系.csv": "character",
    "爽点与节奏.csv": "pacing",
    "场景写法.csv": "scene_template",
    "金手指与设定.csv": "skill",
    "题材与调性推理.csv": "genre_guide",
    "裁决规则.csv": "genre_guide",
}

CODE_PREFIX_MAP = {
    "命名规则.csv": "NR",
    "写作技法.csv": "WT",
    "桥段套路.csv": "TR",
    "人设与关系.csv": "CH",
    "爽点与节奏.csv": "PA",
    "场景写法.csv": "SP",
    "金手指与设定.csv": "SY",
    "题材与调性推理.csv": "GR",
    "裁决规则.csv": "RS",
}

def parse_csv_file(csv_path: Path) -> list[dict]:
    records = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get('编号'):
                continue
            records.append(row)
    return records

def extract_genres(genre_str: str) -> list[str]:
    if not genre_str:
        return []
    genres = [g.strip() for g in genre_str.replace('|', ',').split(',') if g.strip()]
    if '全部' in genres:
        return ['all']
    return genres

def extract_keywords(keyword_str: str) -> list[str]:
    if not keyword_str:
        return []
    return [k.strip() for k in keyword_str.replace('|', ',').split(',') if k.strip()]

def extract_skills(skill_str: str) -> list[str]:
    if not skill_str:
        return []
    return [s.strip() for s in skill_str.replace('|', ',').split(',') if s.strip()]

def build_content_from_record(record: dict) -> str:
    parts = []
    if record.get('核心摘要'):
        parts.append(record['核心摘要'])
    if record.get('详细展开'):
        parts.append(record['详细展开'])
    if record.get('大模型指令'):
        parts.append(f"指令：{record['大模型指令']}")
    if record.get('正例'):
        parts.append(f"正例：{record['正例']}")
    if record.get('反例'):
        parts.append(f"反例：{record['反例']}")
    if record.get('毒点'):
        parts.append(f"毒点：{record['毒点']}")
    return '\n'.join(parts)

def build_metadata_from_record(record: dict) -> dict:
    metadata = {}
    if record.get('编号'):
        metadata['original_code'] = record['编号']
    if record.get('适用技能'):
        metadata['applicable_skills'] = extract_skills(record['适用技能'])
    if record.get('分类'):
        metadata['subcategory'] = record['分类']
    if record.get('层级'):
        metadata['level'] = record['层级']
    if record.get('关键词'):
        metadata['keywords'] = extract_keywords(record['关键词'])
    if record.get('意图与同义词'):
        metadata['intent_synonyms'] = record['意图与同义词']
    if record.get('大模型指令'):
        metadata['llm_instruction'] = record['大模型指令']
    if record.get('毒点'):
        metadata['pitfalls'] = record['毒点']
    if record.get('前置铺垫'):
        metadata['prerequisites'] = record['前置铺垫']
    if record.get('核心爽点'):
        metadata['core_payoff'] = record['核心爽点']
    if record.get('转折设计'):
        metadata['twist_design'] = record['转折设计']
    if record.get('反套路变种'):
        metadata['anti_trope_variants'] = record['反套路变种']
    if record.get('人设类型'):
        metadata['character_type'] = record['人设类型']
    if record.get('核心动机'):
        metadata['core_motivation'] = record['核心动机']
    if record.get('行为逻辑'):
        metadata['behavior_logic'] = record['行为逻辑']
    if record.get('互动模式'):
        metadata['interaction_pattern'] = record['互动模式']
    if record.get('技法类型'):
        metadata['technique_type'] = record['技法类型']
    if record.get('技法名称'):
        metadata['technique_name'] = record['技法名称']
    if record.get('适用场景'):
        metadata['applicable_scenes'] = record['适用场景']
    if record.get('节奏类型'):
        metadata['pacing_type'] = record['节奏类型']
    if record.get('情绪调动手法'):
        metadata['emotion_techniques'] = record['情绪调动手法']
    if record.get('命名对象'):
        metadata['naming_target'] = record['命名对象']
    if record.get('规则'):
        metadata['naming_rules'] = record['规则']
    if record.get('设定类型'):
        metadata['setting_type'] = record['设定类型']
    if record.get('场景类型'):
        metadata['scene_type'] = record['场景类型']
    return metadata

def extract_title_from_record(record: dict) -> str:
    if record.get('核心摘要'):
        title = record['核心摘要']
        if len(title) > 100:
            title = title[:100] + '...'
        return title
    if record.get('桥段名称'):
        return record['桥段名称']
    if record.get('技法名称'):
        return record['技法名称']
    if record.get('人设类型'):
        return record['人设类型']
    if record.get('节奏类型'):
        return record['节奏类型']
    if record.get('设定类型'):
        return record['设定类型']
    if record.get('场景类型'):
        return record['场景类型']
    if record.get('编号'):
        return f"规则 {record['编号']}"
    return "未命名"

def make_slug(name: str) -> str:
    slug = name.strip().lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = slug.strip('-')
    return slug or 'unknown'

async def get_database_pool():
    database_url = os.environ.get('DATABASE_URL', "postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    return await asyncpg.create_pool(database_url, min_size=1, max_size=10)

async def ensure_category_exists(pool, category_slug: str, name: str = None, parent_id: str = None, level: int = 0) -> str:
    row = await pool.fetchrow("SELECT id FROM categories WHERE slug = $1", category_slug)
    if row:
        return row['id']
    display_name = name or category_slug.replace('_', ' ').title()
    row = await pool.fetchrow('''
        INSERT INTO categories (slug, name, name_en, description, parent_id, level, is_system)
        VALUES ($1, $2, $3, 'auto-created', $4, $5, false)
        ON CONFLICT (slug) DO UPDATE SET slug = EXCLUDED.slug
        RETURNING id
    ''', category_slug, display_name, display_name, parent_id, level)
    return row['id']

async def get_or_create_subcategory(pool, parent_slug: str, subcategory_name: str) -> str:
    parent_id = await ensure_category_exists(pool, parent_slug)
    sub_slug = f"{parent_slug}_{make_slug(subcategory_name)}"
    return await ensure_category_exists(pool, sub_slug, subcategory_name, parent_id, 1)

async def clear_opencode_data(pool):
    print("\n🗑️ 清理旧数据...")
    await pool.execute("DELETE FROM knowledge_base WHERE source = 'opencode'")
    print("✅ 旧数据已清理")

async def import_csv_file(pool, csv_path: Path) -> int:
    csv_name = csv_path.name
    parent_category_slug = CSV_CATEGORY_MAP.get(csv_name, 'knowledge_qa')
    
    print(f"\n📄 处理文件: {csv_name}")
    print(f"   父分类: {parent_category_slug}")
    
    parent_id = await ensure_category_exists(pool, parent_category_slug)
    
    try:
        records = parse_csv_file(csv_path)
    except Exception as e:
        print(f"   ❌ 解析失败: {e}")
        return 0
    
    print(f"   解析记录: {len(records)} 条")
    
    imported = 0
    code_prefix = CODE_PREFIX_MAP.get(csv_name, 'XX')
    
    for i, record in enumerate(records):
        try:
            subcategory_name = record.get('分类', '').strip()
            
            if subcategory_name:
                category_id = await get_or_create_subcategory(pool, parent_category_slug, subcategory_name)
            else:
                category_id = parent_id
            
            original_code = record.get('编号', '')
            code = f"{code_prefix}-{original_code}" if original_code else str(uuid4())
            title = extract_title_from_record(record)
            content = build_content_from_record(record)
            metadata = build_metadata_from_record(record)
            applicable_genres = extract_genres(record.get('适用题材', ''))
            applicable_skills = extract_skills(record.get('适用技能', ''))
            level = record.get('层级', 'knowledge')
            
            await pool.execute('''
                INSERT INTO knowledge_base (
                    id, code, title, content, summary, metadata,
                    source, source_file, category_id,
                    applicable_genres, applicable_skills, level, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ''',
                str(uuid4()),
                code,
                title,
                content,
                record.get('核心摘要', ''),
                json.dumps(metadata),
                'opencode',
                csv_name,
                category_id,
                applicable_genres,
                applicable_skills,
                level,
                'active'
            )
            imported += 1
            if (i + 1) % 50 == 0:
                print(f"   进度: {i + 1}/{len(records)}")
        except Exception as e:
            print(f"   ⚠️ 导入失败: {e}")
            continue
    
    print(f"   ✅ 成功导入: {imported} 条")
    return imported

async def get_statistics(pool):
    print("\n" + "=" * 50)
    print("📊 导入统计")
    print("=" * 50)
    
    total = await pool.fetchval("SELECT COUNT(*) FROM knowledge_base WHERE source = 'opencode'")
    print(f"\n总记录数: {total}")
    
    print("\n按分类层级统计:")
    rows = await pool.fetch('''
        SELECT c.slug, c.name, c.level, COUNT(k.id) as count
        FROM categories c
        LEFT JOIN knowledge_base k ON k.category_id = c.id AND k.source = 'opencode'
        GROUP BY c.id, c.slug, c.name, c.level
        ORDER BY c.level, c.sort_order
    ''')
    
    for row in rows:
        indent = "  " * row['level']
        print(f"{indent}{row['slug']:35} ({row['name']}): {row['count']:4} 条")
    
    print("\n按一级分类统计:")
    rows = await pool.fetch('''
        SELECT pc.slug, pc.name, COUNT(k.id) as count
        FROM categories pc
        LEFT JOIN categories sc ON sc.parent_id = pc.id
        LEFT JOIN knowledge_base k ON k.category_id IN (pc.id, sc.id) AND k.source = 'opencode'
        WHERE pc.level = 0
        GROUP BY pc.id, pc.slug, pc.name
        ORDER BY pc.sort_order
    ''')
    
    for row in rows:
        print(f"  {row['name']:15}: {row['count']:4} 条")

async def main():
    print("=" * 50)
    print("🚀 opencode 数据导入脚本（支持子分类）")
    print("=" * 50)
    
    if not OPENCODE_CSV_DIR.exists():
        print(f"\n❌ 数据源目录不存在: {OPENCODE_CSV_DIR}")
        return
    
    csv_files = list(OPENCODE_CSV_DIR.glob("*.csv"))
    available_csvs = [f for f in csv_files if f.name in CSV_CATEGORY_MAP]
    
    print(f"\n📁 数据源: {OPENCODE_CSV_DIR}")
    print(f"📄 找到 {len(csv_files)} 个CSV文件")
    print(f"📄 其中 {len(available_csvs)} 个可导入")
    
    for csv_file in csv_files:
        status = "✅" if csv_file.name in CSV_CATEGORY_MAP else "⏭️ "
        print(f"  {status} {csv_file.name}")
    
    if not available_csvs:
        print("\n❌ 没有可导入的CSV文件")
        return
    
    print("\n🔌 连接数据库...")
    try:
        pool = await get_database_pool()
        print("✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return
    
    try:
        await clear_opencode_data(pool)
        
        total_imported = 0
        for csv_file in available_csvs:
            imported = await import_csv_file(pool, csv_file)
            total_imported += imported
        
        await get_statistics(pool)
        
        print("\n" + "=" * 50)
        print(f"✅ 导入完成！总计: {total_imported} 条记录")
        print("=" * 50)
        
    finally:
        await pool.close()

if __name__ == "__main__":
    asyncio.run(main())