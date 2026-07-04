#!/usr/bin/env python3
"""
PRESETS.md数据导入脚本
解析PRESETS.md文档，按章节拆分内容并导入到knowledge_base表

章节与分类映射：
1. 叙事结构类型 -> narrative_structure
2. 核心冲突类型 -> core_conflict
3. 世界观基调 -> world_tone
4. 读者群体定位 -> reader_groups
5. 故事复杂层级 -> story_complexity
6. 叙事节奏模式 -> writing_technique (写作技法)
7. 情感驱动力 -> emotion_driver
8. 主题深度 -> theme_depth
9. 40种题材分类 -> genre_guide (题材指南)
10. 40种风格分类 -> style_categories
11. 10种年代分类 -> era_setting
12. 语言与视角 -> language_choice / narrative_perspective
13. 100种角色身份职业 -> identity_occupation
14. 10种发表平台风格 -> platform_style
15. 7种预设文风 -> writing_style
16. 50种标题结构 -> title_structure
17. 金手指体系 -> cheat_types
18. 100种男主人设预设 -> male_protagonist
19. 100种女主人设预设 -> female_protagonist
20. 100种反派人设预设 -> antagonist
21. 300种情节模板 -> growth_templates/romance_templates/adventure_templates/politics_templates/mystery_templates/daily_templates
22. 200种时空背景 -> setting_background
23. 500种结局类型 -> ending_types
24. 500种时空背景（扩展）-> setting_background
"""

import os
import re
import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from novel_os_mcp.db import Database
from novel_os_mcp.config import Settings
from novel_os_mcp.knowledge_service import KnowledgeService


class PresetsParser:
    """PRESETS.md解析器"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = self._read_file()
        self.sections = []

    def _read_file(self) -> str:
        """读取文件内容"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def parse(self) -> List[Dict[str, Any]]:
        """解析整个文档"""
        lines = self.content.split('\n')
        sections = []
        current_section = None
        current_table = []
        in_table = False
        tables = []
        pending_header = None

        for line_num, line in enumerate(lines, 1):
            # 检测章节标题 (## X. 标题名称)
            chapter_match = re.match(r'^##\s*(\d+)\.\s*(.+?)$', line)
            if chapter_match:
                # 保存上一个章节
                if current_section and (current_section.get('content') or tables or current_table):
                    if current_table:
                        tables.append(self._parse_table(current_table))
                        current_table = []
                    if tables:
                        if len(tables) == 1:
                            current_section['table'] = tables[0]
                        else:
                            current_section['tables'] = tables
                    sections.append(current_section)

                # 开始新章节
                chapter_num = int(chapter_match.group(1))
                chapter_title = chapter_match.group(2).strip()
                current_section = {
                    'chapter': chapter_num,
                    'title': chapter_title,
                    'content': '',
                    'table': None,
                    'tables': None,
                    'line_start': line_num
                }
                in_table = False
                tables = []
                pending_header = None
                continue

            # 检测子标题 (### 标题)
            sub_title_match = re.match(r'^###\s*(.+?)$', line)
            if sub_title_match and current_section:
                # 如果之前在表格中，先保存当前表格
                if in_table and current_table:
                    tables.append(self._parse_table(current_table))
                    current_table = []
                    in_table = False
                pending_header = None
                current_section['content'] += line + '\n'
                continue

            # 检测表格分隔线 (|----|----|)
            if line.startswith('|') and re.match(r'^\|[-:|]+\|$', line):
                in_table = True
                current_table = []
                if pending_header:
                    current_table.append(pending_header)
                current_table.append(line)
                pending_header = None
                continue

            # 检测表格行
            if in_table and line.startswith('|'):
                current_table.append(line)
                continue

            # 检测可能的表头行（以|开头但不是分隔线）
            if line.startswith('|') and not re.match(r'^\|[-:|]+\|$', line):
                pending_header = line
                continue

            # 如果有待处理的表头但不是表格，添加到内容中
            if pending_header:
                if current_section:
                    current_section['content'] += pending_header + '\n'
                pending_header = None

            # 普通内容
            if current_section:
                current_section['content'] += line + '\n'

        # 保存最后一个章节
        if current_section and (current_section.get('content') or tables or current_table):
            if current_table:
                tables.append(self._parse_table(current_table))
            if tables:
                if len(tables) == 1:
                    current_section['table'] = tables[0]
                else:
                    current_section['tables'] = tables
            sections.append(current_section)

        self.sections = sections
        return sections

    def _parse_table(self, table_lines: List[str]) -> List[Dict[str, str]]:
        """解析markdown表格"""
        if len(table_lines) < 2:
            return []

        # 提取表头
        header_line = table_lines[0].strip('|')
        headers = [h.strip() for h in header_line.split('|')]

        # 提取数据行（跳过分隔线）
        data_rows = []
        for line in table_lines[1:]:
            if not line.strip():
                continue
            # 跳过分隔线
            if re.match(r'^\|[-:|]+\|$', line):
                continue
            line = line.strip('|')
            values = [v.strip() for v in line.split('|')]
            row = dict(zip(headers, values))
            data_rows.append(row)

        return data_rows


class PresetsImporter:
    """PRESETS数据导入器"""

    def __init__(self, db: Database):
        self.db = db
        self.service = KnowledgeService(db)
        self.chapter_category_map = {
            1: 'narrative_structure',
            2: 'core_conflict',
            3: 'world_tone',
            4: 'reader_groups',
            5: 'story_complexity',
            6: 'writing_technique',
            7: 'emotion_driver',
            8: 'theme_depth',
            9: 'genre_guide',
            10: 'style_categories',
            11: 'era_setting',
            12: 'narrative_perspective',
            13: 'identity_occupation',
            14: 'platform_style',
            15: 'writing_style',
            16: 'title_structure',
            17: 'cheat_types',
            18: 'male_protagonist',
            19: 'female_protagonist',
            20: 'antagonist',
            21: 'growth_templates',
            22: 'setting_background',
            23: 'ending_types',
            24: 'setting_background',
        }

    async def import_all(self, sections: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
        """导入所有章节数据"""
        results = {
            'total_sections': len(sections),
            'imported': 0,
            'skipped': 0,
            'errors': [],
            'section_results': []
        }

        for section in sections:
            try:
                result = await self._import_section(section, dry_run)
                results['section_results'].append(result)
                results['imported'] += result.get('imported', 0)
                results['skipped'] += result.get('skipped', 0)
                if result.get('errors'):
                    results['errors'].extend(result['errors'])
            except Exception as e:
                results['errors'].append(f"章节{section['chapter']} {section['title']}: {str(e)}")
                results['section_results'].append({
                    'chapter': section['chapter'],
                    'title': section['title'],
                    'imported': 0,
                    'skipped': 0,
                    'errors': [str(e)]
                })

        return results

    async def _import_section(self, section: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
        """导入单个章节"""
        chapter = section['chapter']
        title = section['title']
        table = section.get('table')
        tables = section.get('tables')
        content = section.get('content', '').strip()

        if not table and not tables:
            return {
                'chapter': chapter,
                'title': title,
                'imported': 0,
                'skipped': 0,
                'errors': ['无表格数据']
            }

        # 特殊处理章节12（语言与视角）
        if chapter == 12:
            return await self._import_chapter_12(section, dry_run)

        # 特殊处理章节21（情节模板，按子类型分配）
        if chapter == 21:
            return await self._import_chapter_21(section, dry_run)

        category_slug = self.chapter_category_map.get(chapter)
        if not category_slug:
            return {
                'chapter': chapter,
                'title': title,
                'imported': 0,
                'skipped': 0,
                'errors': [f'未找到对应分类: {chapter}']
            }

        imported = 0
        skipped = 0
        errors = []

        # 处理单个表格或多个表格
        all_tables = [table] if table else tables
        for tbl in all_tables:
            for row in tbl:
                try:
                    item = self._build_item(chapter, row, category_slug, content)
                    if dry_run:
                        print(f"[DRY RUN] 章节{chapter}: {item['code']} - {item['title']}")
                    else:
                        await self.service.upsert_item(**item)
                    imported += 1
                except Exception as e:
                    skipped += 1
                    errors.append(f"Row {row.get('ID', '?')}: {str(e)}")

        return {
            'chapter': chapter,
            'title': title,
            'category': category_slug,
            'imported': imported,
            'skipped': skipped,
            'errors': errors[:5]  # 限制错误数量
        }

    async def _import_chapter_12(self, section: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
        """特殊处理章节12：语言与视角"""
        # 语言部分导入到language_choice
        # 视角部分导入到narrative_perspective
        content = section.get('content', '')
        results = {'imported': 0, 'skipped': 0, 'errors': []}

        # 获取所有表格（单个或多个）
        table = section.get('table')
        tables = section.get('tables', [])
        all_tables = [table] if table else tables
        
        if not all_tables:
            return {**results, 'chapter': 12, 'title': section['title'], 'errors': ['无表格数据']}

        # 处理每个表格
        for tbl in all_tables:
            if not tbl:
                continue
            
            # 根据表头判断是语言还是视角
            first_row = tbl[0]
            if '语言' in first_row:
                category_slug = 'language_choice'
                code_prefix = 'LC'
            else:
                category_slug = 'narrative_perspective'
                code_prefix = 'NP'

            for row in tbl:
                try:
                    item = self._build_item(12, row, category_slug, content, code_prefix=code_prefix)
                    if dry_run:
                        print(f"[DRY RUN] 章节12-{code_prefix}: {item['code']} - {item['title']}")
                    else:
                        await self.service.upsert_item(**item)
                    results['imported'] += 1
                except Exception as e:
                    results['skipped'] += 1
                    results['errors'].append(f"Row {row.get('ID', '?')}: {str(e)}")

        return {
            'chapter': 12,
            'title': section['title'],
            **results
        }

    async def _import_chapter_21(self, section: Dict[str, Any], dry_run: bool) -> Dict[str, Any]:
        """特殊处理章节21：300种情节模板"""
        content = section.get('content', '')
        table = section.get('table')
        tables = section.get('tables', [])
        all_tables = [table] if table else tables
        
        if not all_tables:
            return {'chapter': 21, 'title': section['title'], 'imported': 0, 'skipped': 0, 'errors': ['无表格数据']}

        results = {'imported': 0, 'skipped': 0, 'errors': []}

        for tbl in all_tables:
            if not tbl:
                continue
            
            for row in tbl:
                try:
                    item_id = int(row.get('ID', 0))
                    # 根据ID范围分配到不同分类
                    if 1 <= item_id <= 50:
                        category_slug = 'growth_templates'
                        code_prefix = 'PT-G'
                    elif 51 <= item_id <= 100:
                        category_slug = 'romance_templates'
                        code_prefix = 'PT-R'
                    elif 101 <= item_id <= 150:
                        category_slug = 'adventure_templates'
                        code_prefix = 'PT-A'
                    elif 151 <= item_id <= 200:
                        category_slug = 'politics_templates'
                        code_prefix = 'PT-P'
                    elif 201 <= item_id <= 250:
                        category_slug = 'mystery_templates'
                        code_prefix = 'PT-M'
                    else:
                        category_slug = 'daily_templates'
                        code_prefix = 'PT-D'

                    item = self._build_item(21, row, category_slug, content, code_prefix=code_prefix)
                    if dry_run:
                        print(f"[DRY RUN] 章节21-{code_prefix}: {item['code']} - {item['title']}")
                    else:
                        await self.service.upsert_item(**item)
                    results['imported'] += 1
                except Exception as e:
                    results['skipped'] += 1
                    results['errors'].append(f"Row {row.get('ID', '?')}: {str(e)}")

        return {
            'chapter': 21,
            'title': section['title'],
            **results
        }

    def _build_item(self, chapter: int, row: Dict[str, str], category_slug: str, 
                   section_content: str, code_prefix: Optional[str] = None) -> Dict[str, Any]:
        """构建知识条目"""
        item_id = row.get('ID', '')
        
        # 生成编号
        if not code_prefix:
            code_prefix = f'PR{chapter:02d}'
        code = f'{code_prefix}-{item_id.zfill(3)}'

        # 提取标题
        title_keys = ['结构类型', '冲突类型', '基调类型', '群体定位', '层级名称',
                      '节奏模式', '驱动力类型', '深度层级', '名称', '身份职业',
                      '平台名称', '文风模式', '标题结构', '具体类型', '人设名称',
                      '情节名称', '语言', '视角类型']
        title = ''
        for key in title_keys:
            if key in row:
                title = row[key]
                break
        if not title:
            title = f'预设条目 {code}'

        # 构建内容
        content_parts = []
        for key, value in row.items():
            if value and key != 'ID':
                content_parts.append(f"**{key}**：{value}")
        content = '\n\n'.join(content_parts)

        # 构建摘要（取前200字）
        summary = content[:200] + '...' if len(content) > 200 else content

        # 构建metadata
        metadata = {
            'chapter': chapter,
            'row_data': row,
            'source': 'presets'
        }

        return {
            'code': code,
            'title': title,
            'content': content,
            'summary': summary,
            'detail': section_content,
            'metadata': metadata,
            'category_slug': category_slug,
            'source': 'presets',
            'source_file': 'PRESETS.md',
            'applicable_genres': [],
            'applicable_skills': ['write', 'plan', 'init'],
            'level': 'knowledge',
            'status': 'active'
        }


async def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='导入PRESETS.md数据到知识库')
    parser.add_argument('--dry-run', action='store_true', help='模拟导入，不实际写入数据库')
    parser.add_argument('--file', default='D:/Project/novels codex/Github/PRESETS.md', help='PRESETS.md文件路径')
    parser.add_argument('--db-url', default='postgres://novel_os:${POSTGRES_PASSWORD}@novel-postgres:5432/novel_os', help='数据库连接URL')
    args = parser.parse_args()

    print(f"=== PRESETS.md数据导入工具 ===")
    print(f"文件路径: {args.file}")
    print(f"模拟模式: {'是' if args.dry_run else '否'}")
    print(f"数据库URL: {args.db_url}")
    print()

    # 解析文件
    print("[1/3] 解析PRESETS.md文件...")
    parser = PresetsParser(args.file)
    sections = parser.parse()
    print(f"  共解析出 {len(sections)} 个章节")
    for sec in sections:
            table = sec.get('table', [])
            tables = sec.get('tables', [])
            if table:
                table_count = len(table)
            elif tables:
                table_count = sum(len(t) for t in tables)
            else:
                table_count = 0
            print(f"    章节{sec['chapter']:2d}: {sec['title']} ({table_count}条数据)")
    print()

    if args.dry_run:
        print("[2/3] 模拟导入（仅显示待导入条目）...")
        importer = None
    else:
        print("[2/3] 连接数据库并导入数据...")
        settings = Settings(DATABASE_URL=args.db_url)
        db = Database(settings)
        await db.connect()
        importer = PresetsImporter(db)

    if importer:
        results = await importer.import_all(sections, dry_run=False)
        print()
        print("[3/3] 导入结果:")
        print(f"  总章节数: {results['total_sections']}")
        print(f"  成功导入: {results['imported']} 条")
        print(f"  跳过: {results['skipped']} 条")
        
        if results['errors']:
            print(f"  错误数: {len(results['errors'])}")
            for err in results['errors'][:10]:
                print(f"    - {err}")
        
        print()
        print("章节详情:")
        for res in results['section_results']:
            status = "✓" if res['imported'] > 0 else "✗"
            print(f"  {status} 章节{res['chapter']:2d} {res['title']}: "
                  f"导入{res['imported']}条, 跳过{res['skipped']}条")

        await db.close()
    else:
        print("[2/3] 模拟导入完成（无实际数据库操作）")

    print()
    print("=== 导入完成 ===")


if __name__ == '__main__':
    asyncio.run(main())