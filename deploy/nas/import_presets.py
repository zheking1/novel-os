#!/usr/bin/env python3
"""
PRESETS.md 数据导入脚本
功能：
1. 解析Markdown表格数据
2. 转换为knowledge_base格式
3. 导入到对应分类
"""

import asyncio
import json
import re
import sys
from pathlib import Path
from uuid import uuid4

import asyncpg

PRESETS_FILE = Path('/opt/novel-os/Github/PRESETS.md')

# PRESETS章节到数据库分类的映射
SECTION_MAP = {
    '1': {'slug': 'narrative_structure', 'name': '叙事结构', 'code_prefix': 'NS'},
    '2': {'slug': 'core_conflict', 'name': '核心冲突', 'code_prefix': 'CC'},
    '3': {'slug': 'world_tone', 'name': '世界观基调', 'code_prefix': 'WT'},
    '4': {'slug': 'reader_groups', 'name': '读者群体', 'code_prefix': 'RG'},
    '5': {'slug': 'story_complexity', 'name': '故事复杂度', 'code_prefix': 'SC'},
    '6': {'slug': 'pacing', 'name': '叙事节奏', 'code_prefix': 'NP'},
    '7': {'slug': 'emotion_driver', 'name': '情感驱动力', 'code_prefix': 'ED'},
    '8': {'slug': 'theme_depth', 'name': '主题深度', 'code_prefix': 'TD'},
    '9': {'slug': 'genre_guide', 'name': '题材分类', 'code_prefix': 'GC'},
    '10': {'slug': 'style_categories', 'name': '风格分类', 'code_prefix': 'SK'},
    '11': {'slug': 'era_setting', 'name': '年代设定', 'code_prefix': 'ES'},
    '12': {'slug': 'language_choice', 'name': '语言与视角', 'code_prefix': 'LV'},  # 需要拆分处理
    '13': {'slug': 'identity_occupation', 'name': '身份职业', 'code_prefix': 'IO'},
    '14': {'slug': 'platform_style', 'name': '平台风格', 'code_prefix': 'PS'},
    '15': {'slug': 'writing_style', 'name': '预设文风', 'code_prefix': 'WS'},
    '16': {'slug': 'title_structure', 'name': '标题结构', 'code_prefix': 'TS'},
    '17': {'slug': 'cheat_types', 'name': '金手指类型', 'code_prefix': 'CT'},
    '18': {'slug': 'male_protagonist', 'name': '男主人设', 'code_prefix': 'MP'},
    '19': {'slug': 'female_protagonist', 'name': '女主人设', 'code_prefix': 'FP'},
    '20': {'slug': 'antagonist', 'name': '反派人设', 'code_prefix': 'AN'},
    '21': {'slug': 'plot_templates', 'name': '情节模板', 'code_prefix': 'PT'},  # 需要拆分到子分类
    '22': {'slug': 'setting_background', 'name': '时空背景', 'code_prefix': 'SB'},
    '23': {'slug': 'ending_types', 'name': '结局类型', 'code_prefix': 'ET'},
}

# 情节模板子分类映射
PLOT_SUBCATEGORY_MAP = {
    '成长': 'growth_templates',
    '感情': 'romance_templates',
    '冒险': 'adventure_templates',
    '权谋': 'politics_templates',
    '悬疑': 'mystery_templates',
    '日常': 'daily_templates',
}


def parse_markdown_tables(content: str) -> dict:
    """解析Markdown文件，提取各章节的表格数据"""
    sections = {}
    
    # 查找所有章节标题 (格式: ## N. 章节名称)
    section_pattern = r'## (\d+)\. (.+?)\n'
    section_matches = list(re.finditer(section_pattern, content))
    
    for i, match in enumerate(section_matches):
        section_num = match.group(1)
        section_name = match.group(2).strip()
        start_pos = match.end()
        
        # 确定结束位置：下一个章节开始或文件结束
        if i + 1 < len(section_matches):
            end_pos = section_matches[i + 1].start()
        else:
            end_pos = len(content)
        
        section_content = content[start_pos:end_pos]
        
        # 提取表格数据
        tables = extract_tables(section_content)
        if tables:
            sections[section_num] = {
                'name': section_name,
                'tables': tables
            }
    
    return sections


def extract_tables(text: str) -> list:
    """从文本中提取Markdown表格"""
    tables = []
    
    # 表格行模式
    table_pattern = r'^\|.+\|$'
    lines = text.split('\n')
    
    current_table = []
    for line in lines:
        if re.match(table_pattern, line.strip()):
            current_table.append(line.strip())
        elif current_table:
            if len(current_table) > 2:  # 至少有表头和分隔行
                tables.append(current_table)
            current_table = []
    
    if len(current_table) > 2:
        tables.append(current_table)
    
    return tables


def parse_table_rows(table: list) -> list[dict]:
    """解析表格行，返回字典列表"""
    if len(table) < 2:
        return []
    
    # 解析表头
    headers = [h.strip() for h in table[0].split('|') if h.strip()]
    
    # 跳过分隔行（第二行）
    rows = []
    for row_line in table[2:]:
        cells = [c.strip() for c in row_line.split('|') if c.strip()]
        if len(cells) >= 2:
            row = {}
            for i, cell in enumerate(cells):
                if i < len(headers):
                    row[headers[i]] = cell
                else:
                    row[f'col_{i}'] = cell
            rows.append(row)
    
    return rows


def build_record_from_row(section_num: str, row: dict, row_index: int) -> dict:
    """将表格行转换为knowledge_base记录格式"""
    section_info = SECTION_MAP.get(section_num, {'slug': 'unknown', 'name': '未知', 'code_prefix': 'XX'})
    
    # 提取标题（通常是第二列）
    title_fields = ['类型', '类型名称', '结构类型', '冲突类型', '基调类型', '群体定位', 
                    '层级名称', '节奏模式', '驱动力类型', '名称', '题材名称', '风格名称',
                    '年代名称', '身份职业', '平台名称', '文风名称', '结构名称', '金手指名称',
                    '人设名称', '模板名称', '背景名称', '结局类型', '主角类型']
    
    title = ''
    for field in title_fields:
        if field in row and row[field]:
            title = row[field]
            break
    
    if not title:
        title = row.get('ID', f'类型{row_index}')
    
    # 构建内容（合并所有字段）
    content_parts = []
    content_fields = ['说明', '核心特点', '适用场景', '写作要点', '读者要求', 
                      '适合题材', '写作策略', '人物弧光', '写作建议', '特征',
                      '代表作', '核心要素', '表现形式', '典型情节']
    
    for field in content_fields:
        if field in row and row[field]:
            content_parts.append(f"**{field}**：{row[field]}")
    
    content = '\n'.join(content_parts)
    
    # 构建摘要
    summary = row.get('说明', row.get('核心特点', title))
    
    # 构建metadata
    metadata = {
        'source_section': section_num,
        'source_name': SECTION_MAP.get(section_num, {}).get('name', '未知'),
        'row_id': row.get('ID', row_index),
    }
    
    # 添加其他字段到metadata
    for key, value in row.items():
        if key not in ['ID', '类型', '类型名称', '说明', '核心特点'] and value:
            metadata[key] = value
    
    # 确定分类
    category_slug = section_info['slug']
    subcategory = None
    
    # 特殊处理：情节模板需要根据类型拆分到子分类
    if section_num == '21':
        template_type = row.get('类型', row.get('模板类型', ''))
        if template_type in PLOT_SUBCATEGORY_MAP:
            category_slug = PLOT_SUBCATEGORY_MAP[template_type]
    
    # 生成code - 处理ID可能是字符串的情况
    id_value = row.get('ID', row_index)
    if isinstance(id_value, int) or (isinstance(id_value, str) and id_value.isdigit()):
        code = f"{section_info['code_prefix']}-{int(id_value):03d}"
    else:
        # 对于非数字ID，直接使用字符串
        code = f"{section_info['code_prefix']}-{id_value}"
    
    return {
        'code': code,
        'title': title,
        'content': content,
        'summary': summary[:200] if len(summary) > 200 else summary,
        'metadata': metadata,
        'category_slug': category_slug,
        'subcategory': subcategory,
        'source': 'presets',
        'level': 'knowledge',
    }


async def get_database_pool():
    database_url = "postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os"
    return await asyncpg.create_pool(database_url, min_size=1, max_size=10)


async def ensure_category(pool, slug: str, name: str, parent_id: str = None, level: int = 0) -> str:
    """确保分类存在"""
    row = await pool.fetchrow("SELECT id FROM categories WHERE slug = $1", slug)
    if row:
        return row['id']
    
    # 创建新分类
    row = await pool.fetchrow('''
        INSERT INTO categories (slug, name, name_en, description, parent_id, level, is_system)
        VALUES ($1, $2, $3, $4, $5, $6, false)
        RETURNING id
    ''', slug, name, name, 'from PRESETS.md', parent_id, level)
    return row['id']


async def import_section(pool, section_num: str, section_data: dict) -> int:
    """导入单个章节的数据"""
    print(f"\n📄 处理章节: {section_num}. {section_data['name']}")
    
    imported = 0
    for table in section_data['tables']:
        rows = parse_table_rows(table)
        print(f"   解析表格: {len(rows)} 行")
        
        for i, row in enumerate(rows):
            try:
                record = build_record_from_row(section_num, row, i + 1)
                
                # 确保分类存在
                category_id = await ensure_category(pool, record['category_slug'], 
                                                    SECTION_MAP.get(section_num, {}).get('name', record['category_slug']))
                
                # 插入记录
                await pool.execute('''
                    INSERT INTO knowledge_base (
                        id, code, title, content, summary, metadata,
                        source, source_file, category_id, level, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ''',
                    str(uuid4()),
                    record['code'],
                    record['title'],
                    record['content'],
                    record['summary'],
                    json.dumps(record['metadata']),
                    record['source'],
                    'PRESETS.md',
                    category_id,
                    record['level'],
                    'active'
                )
                imported += 1
            except Exception as e:
                print(f"   ⚠️ 导入失败 (行{i+1}): {e}")
                continue
    
    print(f"   ✅ 成功导入: {imported} 条")
    return imported


async def get_statistics(pool):
    """统计导入结果"""
    print("\n" + "=" * 50)
    print("📊 导入统计")
    print("=" * 50)
    
    total = await pool.fetchval("SELECT COUNT(*) FROM knowledge_base WHERE source = 'presets'")
    print(f"\n总记录数: {total}")
    
    print("\n按分类统计:")
    rows = await pool.fetch('''
        SELECT c.slug, c.name, COUNT(k.id) as count
        FROM categories c
        LEFT JOIN knowledge_base k ON k.category_id = c.id AND k.source = 'presets'
        GROUP BY c.id, c.slug, c.name
        ORDER BY count DESC
        LIMIT 30
    ''')
    
    for row in rows:
        print(f"  {row['slug']:30} ({row['name']}): {row['count']:4} 条")


async def main():
    print("=" * 50)
    print("🚀 PRESETS.md 数据导入脚本")
    print("=" * 50)
    
    if not PRESETS_FILE.exists():
        print(f"\n❌ 文件不存在: {PRESETS_FILE}")
        return
    
    print(f"\n📁 数据源: {PRESETS_FILE}")
    
    # 读取文件
    content = PRESETS_FILE.read_text(encoding='utf-8')
    print(f"📄 文件大小: {len(content)} 字符")
    
    # 解析表格
    print("\n🔍 解析表格...")
    sections = parse_markdown_tables(content)
    print(f"✅ 找到 {len(sections)} 个章节")
    
    # 连接数据库
    print("\n🔌 连接数据库...")
    pool = await get_database_pool()
    print("✅ 数据库连接成功")
    
    try:
        # 清理旧数据
        print("\n🗑️ 清理旧数据...")
        await pool.execute("DELETE FROM knowledge_base WHERE source = 'presets'")
        print("✅ 旧数据已清理")
        
        # 导入各章节
        total_imported = 0
        for section_num, section_data in sorted(sections.items(), key=lambda x: int(x[0])):
            imported = await import_section(pool, section_num, section_data)
            total_imported += imported
        
        # 统计结果
        await get_statistics(pool)
        
        print("\n" + "=" * 50)
        print(f"✅ 导入完成！总计: {total_imported} 条记录")
        print("=" * 50)
        
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())