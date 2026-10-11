# Archive & Backup 服务 — 归档与备份

**源码**: 
- `novel-os-mcp/src/novel_os_mcp/services/archive.py` (219 行)
- `novel-os-mcp/src/novel_os_mcp/services/backup.py` (343 行)

## 概述

Archive 和 Backup 是两个独立但互补的服务，负责数据生命周期管理。

- **ArchiveService**: 数据分层归档 (active → recent → archive → deep_archive)
- **BackupService**: 数据备份与恢复 (full / incremental / config / project_export)

---

# 一、ArchiveService — 归档服务

## 数据库表

| 表名 | 说明 |
|------|------|
| `archives` | 归档任务记录 |
| `archive_items` | 归档项目明细 |

## 核心方法

### create_archive

创建归档任务。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|------|------|
| `archive_type` | str | - | 归档类型 |
| `name` | str | - | 归档名称 |
| `description` | str\|None | None | 描述 |
| `retention_days` | int | 365 | 保留天数 |
| `compress` | bool | true | 是否压缩 |

### get_archives

列出项目归档，支持按 `archive_type` 过滤。返回含 `item_count`、`size_bytes`、`last_archived_at`。

### archive_chapters

按条件归档章节:

| 参数 | 说明 |
|------|------|
| `older_than_days` | 创建时间早于 N 天的章节 |
| `status_filter` | 按章节状态过滤 |

**执行流程**:
1. 查询符合条件的章节
2. 逐章: `INSERT INTO archive_items` (存储 `row_to_json(chapters.*)` 作为 `original_data`)
3. 逐章: `UPDATE chapters SET is_deleted = true` (软删除)
4. 更新 `archives.item_count` 和 `last_archived_at`

### restore_from_archive

从归档恢复数据:

1. 从 `archive_items` 读取原始数据
2. 对于 `item_type='chapter'`: `UPDATE chapters SET is_deleted = false`

### get_archive_stats

归档统计: `total_archives`, `total_items`, `total_size_bytes`。

### delete_archive / update_archive_status

CRUD 操作。

---

# 二、BackupService — 备份恢复服务

## 备份类型

| 类型 | 常量 | 说明 |
|------|------|------|
| 全量备份 | `BACKUP_TYPE_FULL = "full"` | 完整数据库备份 |
| 增量备份 | `BACKUP_TYPE_INCREMENTAL = "incremental"` | 增量数据备份 |
| 配置备份 | `BACKUP_TYPE_CONFIG = "config"` | 系统配置备份 |
| 项目导出 | `BACKUP_TYPE_PROJECT_EXPORT = "project_export"` | 单项目数据导出 |

## 备份状态

| 状态 | 说明 |
|------|------|
| `pending` | 等待执行 |
| `in_progress` | 执行中 |
| `completed` | 已完成 |
| `failed` | 失败 |

## 数据库表

| 表名 | 说明 |
|------|------|
| `backup_records` | 备份记录 |
| `backup_schedules` | 备份调度 |
| `restore_records` | 恢复记录 |

## 备份记录管理

### create_backup_record

创建备份记录，初始状态 `pending`。

### update_backup_record

按状态更新备份记录:

- `in_progress` → 设置 `started_at`
- `completed` → 设置 `completed_at`、`file_size_bytes`、`file_count`、`checksum`、`compression_type`
- `failed` → 设置 `completed_at`、`error_message`

### get_backup_records

列表查询，支持 `project_id`、`backup_type`、`status` 过滤。

---

## 备份调度

### upsert_backup_schedule

创建/更新备份计划:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|------|------|
| `schedule_name` | str | - | 计划名称 |
| `backup_type` | str | `"incremental"` | 备份类型 |
| `schedule_type` | str | `"daily"` | 调度类型 (daily/weekly/monthly) |
| `retention_count` | int | 7 | 保留备份份数 |
| `retention_days` | int | 30 | 保留天数 |
| `storage_path` | str\|None | None | 存储路径 |
| `storage_type` | str | `"local"` | 存储类型 |
| `enabled` | bool | true | 是否启用 |

**冲突处理**: `ON CONFLICT DO NOTHING`（duplicate 时查询已有记录返回）。

### get_backup_schedule

列出备份计划，支持按 `project_id` 过滤。

---

## 恢复记录

### create_restore_record

创建恢复记录:

| 参数 | 说明 |
|------|------|
| `backup_record_id` | 关联备份记录 |
| `restore_type` | `"full"` 等 |
| `performed_by` | 执行人 |

### update_restore_record

按状态更新恢复记录:

- `in_progress` → 设置 `started_at`
- `completed` → 设置 `completed_at`、`tables_restored` (JSONB)、`records_restored_count`
- `failed` → 设置 `completed_at`、`error_message`

### get_restore_records

按项目 ID 查询恢复记录列表。

---

## 工作流引导

**归档流程**:
1. `create_archive()` 创建归档任务
2. `archive_chapters()` 按条件归档章节
3. `get_archive_stats()` 查看归档统计
4. 需要恢复 → `restore_from_archive()`

**备份流程**:
1. `upsert_backup_schedule()` 设置备份计划
2. `create_backup_record()` 创建备份任务记录
3. `update_backup_record(status="completed", ...)` 记录完成结果
4. 需要恢复 → `create_restore_record()` + `update_restore_record()`