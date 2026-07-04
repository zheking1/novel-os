import re
from typing import Dict, List, Any

class PresetsParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        with open(file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()

    def parse(self):
        lines = self.content.split('\n')
        sections = []
        current_section = None
        current_table = []
        in_table = False
        tables = []
        pending_header = None

        for line_num, line in enumerate(lines, 1):
            chapter_match = re.match(r'^##\s*(\d+)\.\s*(.+?)$', line)
            if chapter_match:
                if current_section and (current_section.get('content') or tables or current_table):
                    if current_table:
                        tables.append(self._parse_table(current_table))
                    if tables:
                        if len(tables) == 1:
                            current_section['table'] = tables[0]
                        else:
                            current_section['tables'] = tables
                    sections.append(current_section)

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

            sub_title_match = re.match(r'^###\s*(.+?)$', line)
            if sub_title_match and current_section:
                if in_table and current_table:
                    tables.append(self._parse_table(current_table))
                    current_table = []
                    in_table = False
                pending_header = None
                current_section['content'] += line + '\n'
                continue

            if line.startswith('|') and re.match(r'^\|[-:|]+\|$', line):
                in_table = True
                current_table = []
                if pending_header:
                    current_table.append(pending_header)
                current_table.append(line)
                pending_header = None
                continue

            if in_table and line.startswith('|'):
                current_table.append(line)
                continue

            if line.startswith('|') and not re.match(r'^\|[-:|]+\|$', line):
                pending_header = line
                continue

            if pending_header:
                if current_section:
                    current_section['content'] += pending_header + '\n'
                pending_header = None

            if current_section:
                current_section['content'] += line + '\n'

        if current_section and (current_section.get('content') or tables or current_table):
            if current_table:
                tables.append(self._parse_table(current_table))
            if tables:
                if len(tables) == 1:
                    current_section['table'] = tables[0]
                else:
                    current_section['tables'] = tables
            sections.append(current_section)

        return sections

    def _parse_table(self, table_lines):
        if len(table_lines) < 2:
            return []
        header_line = table_lines[0].strip('|')
        headers = [h.strip() for h in header_line.split('|')]
        data_rows = []
        for line in table_lines[1:]:
            if not line.strip():
                continue
            if re.match(r'^\|[-:|]+\|$', line):
                continue
            line = line.strip('|')
            values = [v.strip() for v in line.split('|')]
            row = dict(zip(headers, values))
            data_rows.append(row)
        return data_rows

parser = PresetsParser(r'D:\Project\novels codex\Github\PRESETS.md')
sections = parser.parse()

for sec in sections[:3]:
    print(f"\n=== 章节{sec['chapter']}: {sec['title']} ===")
    table = sec.get('table', [])
    if table:
        print(f"表头: {list(table[0].keys())}")
        for i, row in enumerate(table[:3]):
            print(f"行{i}: {row}")
            print(f"  ID值: '{row.get('ID', '')}'")
            print(f"  ID类型: {type(row.get('ID', ''))}")