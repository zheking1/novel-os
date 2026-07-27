# 正文本地化 + agent 错误修复计划

## 一、删除正文字段

### 1.1 pipeline.generate 参数改造
**文件**: `novel-os-mcp/src/novel_os_mcp/tools/novel_gen.py`
- `content: str | None = None` → `summary: str | None = None`
- 内部逻辑：`if content:` → `if summary:`，不再接收全文
- 删除 `word_count = len(text)`，改为接口验证 `len(summary) <= 200`

### 1.2 generation_passes 列删除
**DB 操作**: `ALTER TABLE generation_passes DROP COLUMN content;`
不再存储任何正文内容。

---

## 二、kb.uk.create year_range 类型修复

**文件**: `novel-os-mcp/src/novel_os_mcp/kb_service.py`
- `year_range` 参数从 `list[int]` 改为 PostgreSQL 兼容格式
- INSERT 时加 `$7::int[]` 显式类型转换

---

## 三、UUID 序列化修复

**文件**: `novel-os-mcp/src/novel_os_mcp/tools/discussion_room.py`
- `apply_results` 函数中排查所有 UUID 字段
- 在返回给 FastMCP 前确保 `.id` 等字段已转 `str()`

---

## 四、build_world phase 4 确认机制

**文件**: `novel-os-mcp/src/novel_os_mcp/tools/novel_wizard.py`
- `_build_world_steps` phase 4 最后一步 `next: wait_user_confirm` → `next: next_step`
- 无需用户确认，系统自动进入 Phase 5

---

## 五、Web UI 同步

**文件**: `novel-os-web/js/pages/*`
- 章节管理 → 提示 "正文已保存在本地"
- 审核管理 → 加 session_id 输入验证提示

---

## 执行顺序

1. year_range 修复
2. UUID 序列化修复
3. phase 4 确认修复
4. pipeline.generate summary 改造
5. generation_passes 列删除
6. Web UI 更新