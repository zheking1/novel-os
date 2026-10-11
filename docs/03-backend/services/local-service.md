# Local Service — 本地文件管理服务

**源码**: `novel-os-mcp/src/novel_os_mcp/local_service.py` (420 行)

## 概述

Local Service 管理本地小说文件与数据库索引的同步。支持目录扫描、文件读写、章节/设定/审查索引同步。

## 数据库表

| 表名 | 说明 |
|------|------|
| `local_projects` | 本地项目注册 |
| `chapter_index` | 章节索引 (本地文件元数据) |
| `setting_index` | 设定索引 (本地文件元数据) |
| `review_index` | 审查报告索引 |

> 注: `chapters` 表（核心章节表）通过 `update_chapter_source()` 更新 `source_path`，`get_chapter()` 从 DB（非本地文件系统）读取章节元数据。

## 文件命名约定

| 正则 | 匹配 | 说明 |
|------|------|------|
| `第(\d+)章` | 章节目录名 | e.g., `第1章`, `第50章` |
| `ch(\d+)_` | 章节文件名模式 | 备用识别 |

## 索引文件

`.novel-index.json` — 扫描完成后生成:

```json
{
  "version": "1.0",
  "project_id": "...",
  "last_sync": "ISO datetime",
  "chapters": {"1": {...}, "2": {...}},
  "settings": [...]
}
```

---

## 项目注册

### register_project

注册本地项目目录，验证路径存在，UPSERT 到 `local_projects`。

### get_project / list_projects

查询本地项目信息。

---

## 目录扫描 (scan_directory)

### 核心流程

```
scan_directory(project_id, local_root):
  1. 遍历 local_root 下所有子目录
  2. 匹配 "第X章" 目录 → _scan_chapter()
  3. 匹配 "小说设定" 目录 → _scan_settings()
  4. _sync_to_db() → 同步索引到 DB
  5. 写入 .novel-index.json
```

### 章节扫描 (_scan_chapter)

**文件分类**:

| 文件名匹配 | 用途 | 提取字段 |
|------|------|------|
| `*outline*.md` | 大纲 | `outline_path`, `outline_summary` |
| `*draft*.md` | 初稿 | `draft_word_count` |
| `*final*.md` | 终稿 | `word_count`, `status="final"`, `summary` |
| `*revision*.md` | 修订版 | `revisions` 列表 |

**子目录扫描**:
- `审查报告/` → `_scan_reviews()` 扫描审查报告

**状态推断**: 若无明确状态但有 draft → `draft`；否则 `planned`。

### 设定扫描 (_scan_settings)

扫描 `小说设定/` 目录，支持子目录分类映射:

| 目录名 | 映射 category |
|------|------|
| `人物设定` | `character` |
| `世界规则` | `world` |
| `势力关系` | `faction` |
| `写作技巧` | `technique` |
| `设定` | `rule` |
| 其他 | `other` |

**文件类型**:
- `.json` → `structured_data` (JSON 解析)
- `.md` → `summary` + `keywords` (从 YAML front matter 提取)

### 审查扫描 (_scan_reviews)

扫描 `审查报告/` 下的 `.md` 文件，提取 `model_name` (从文件名推断) 和 `summary`。

---

## DB 同步 (_sync_to_db)

### local_projects 更新

```sql
INSERT INTO local_projects (project_id, local_root, file_count, total_words, chapter_count, last_scan_at)
ON CONFLICT (project_id) DO UPDATE
```

### chapter_index 同步

UPSERT 每条章节元数据: `project_id + chapter_no` 为唯一键。

### setting_index 同步

INSERT with `ON CONFLICT DO NOTHING`（不覆盖已有记录）。

---

## 文件读写

### read_file

读取本地文件，含**路径安全验证**:

```python
full_path = os.path.normpath(os.path.join(local_root, relative_path))
if not full_path.startswith(os.path.normpath(local_root)):
    raise ValueError("路径越界")  # 防止路径遍历攻击
```

### write_file

写入本地文件，含路径安全验证。自动创建父目录。返回 `{path, size, word_count}`。

---

## 章节查询 (DB 模式，不依赖本地文件系统)

### list_chapters

从 `chapters` 表按 status 过滤、分页查询。

### get_chapter

从 `chapters` 表获取章节元数据，附加:
- `summary`: 从 `generation_passes` 获取最近 draft 的 `content[:500]`
- `word_count`: 从 generation_passes metadata 中获取 `word_count`
- `local_file_path`: 从 generation_passes metadata 中获取 `local_file_path`

### get_chapter_content

从 `generation_passes` 获取章节最新内容（不依赖本地文件系统）。

### update_chapter_source

更新 `chapters.source_path`（用户在本地文件系统中的正文路径）。

---

## 审查查询

### list_reviews

从 `review_index` 表获取审查列表，支持按 `chapter_no` 过滤。

### get_review_content

通过 `local_projects.local_root` + `review_index.local_path` 读取审查报告全文。

---

## 工具方法

| 方法 | 说明 |
|------|------|
| `_count_chinese_words()` | 从文件统计中文字数 (正则 `[\u4e00-\u9fff]`) |
| `_extract_summary()` | 提取文件前 500 字摘要 (跳过 YAML front matter `---...---`) |
| `_extract_keywords()` | 从 YAML front matter 提取 keywords 字段 |
| `_map_category()` | 目录名 → category 映射 |

---

## 工作流引导

1. 注册项目 → `register_project(project_id, local_root)`
2. 扫描目录 → `scan_directory(project_id, local_root)` → 生成 `.novel-index.json`
3. 读取文件 → `read_file(local_root, rel_path)` / `write_file(...)`
4. 章节管理 → `list_chapters()` / `get_chapter()` / `get_chapter_content()`
5. 审查管理 → `list_reviews()` / `get_review_content()`