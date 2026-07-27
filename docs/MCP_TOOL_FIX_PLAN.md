# MCP 工具数据维护修复方案

## 1. pipeline.generate → 更新 chapters.word_count

**问题**: `save_pass=true` 时创建了 generation_pass，但 chapters 表 word_count=0

**文件**: `novel-os-mcp/src/novel_os_mcp/tools/novel_gen.py` 第 1518 行之后

**方案**: 保存 generation_pass 后，同步更新 chapters 表

```python
# 在 create_generation_pass 后添加
ch_row = await db.fetchrow(
    "SELECT id FROM chapters WHERE project_id = $1 AND chapter_no = $2",
    project_id, chapter_no,
)
if ch_row:
    await db.execute(
        "UPDATE chapters SET word_count = $1, updated_at = NOW() WHERE id = $2",
        word_count, ch_row["id"],
    )
```

---

## 2. submit_chapter_commit → 自动填充 chapters.volume_no

**问题**: 创建 chapter 时 volume_no=NULL，未根据章节号匹配卷范围

**文件**: `novel-os-mcp/src/novel_os_mcp/services/workflow.py` 第 421-431 行

**方案**: 创建 chapter 前，根据 chapter_no 查找所属卷

```python
# line 421 附近，vol_row 查询已存在但 volume_no 未使用
vol_row = await self._db.fetchrow(
    "SELECT volume_no FROM volumes WHERE project_id = $1 AND start_chapter_no <= $2 AND (end_chapter_no IS NULL OR end_chapter_no >= $2) LIMIT 1",
    project_id, chapter_no,
)
volume_no = vol_row["volume_no"] if vol_row else 1
# INSERT 时把 volume_no 传给 chapters
```

---

## 3. submit_chapter_commit → 回填 volumes.end_chapter_no

**问题**: 章节提交后 volumes 表的 end_chapter_no 一直为 NULL

**文件**: `novel-os-mcp/src/novel_os_mcp/services/workflow.py` 第 465 行之后

**方案**: 提交成功后刷新卷范围

```python
await conn.execute(
    "UPDATE volumes SET end_chapter_no = (SELECT MAX(chapter_no) FROM chapters WHERE project_id=$1 AND volume_no=volumes.volume_no), updated_at=NOW() WHERE project_id=$1",
    project_id,
)
```

---

## 4. pipeline.generate → 写入 chapter_summaries

**问题**: `chapter_summaries` 表全空，Web UI 章节列表摘要列为空

**文件**: `novel-os-mcp/src/novel_os_mcp/tools/novel_gen.py` 第 1518 行之后

**方案**: save_pass=true 且 pass_type='drafting' 时，同步写入摘要

```python
if pass_type == "drafting":
    ch_row = await db.fetchrow(
        "SELECT id FROM chapters WHERE project_id = $1 AND chapter_no = $2",
        project_id, chapter_no,
    )
    if ch_row:
        await db.execute(
            """INSERT INTO chapter_summaries (project_id, chapter_id, summary_type, content)
               VALUES ($1, $2, 'chapter', $3)
               ON CONFLICT (chapter_id, summary_type) DO UPDATE SET content = EXCLUDED.content, updated_at = NOW()""",
            project_id, ch_row["id"], summary,
        )
```

---

## 5. discussion_room 完成 → 写入 review_reports

**问题**: 讨论室审核完成但 review_reports 表无数据，审核报告页显示空

**文件**: `novel-os-mcp/src/novel_os_mcp/tools/discussion_room.py` 第 593-598 行 `_update_phase`

**方案**: 讨论室完成且有共识时，从 responses 提取 reviewer 反馈写入 review_reports

```python
if phase == "completed" and kwargs.get("status") == "completed":
    # 已有: auto-aggregate review_jobs
    # 新增: 提取 review 反馈写入 review_reports
    session = await db.fetchrow("SELECT responses, project_id, topic FROM discussion_sessions WHERE id=$1", session_id)
    if session:
        responses = json.loads(session["responses"]) if isinstance(session["responses"], str) else session["responses"]
        for r in responses:
            if r.get("role") == "reviewer" and r.get("phase", "").startswith("review"):
                # 解析 chapter_no (从 topic 中提取)
                import re
                match = re.search(r'第(\d+)章', session["topic"] or "")
                chapter_no = int(match.group(1)) if match else None
                if chapter_no:
                    ch = await db.fetchrow("SELECT id FROM chapters WHERE project_id=$1 AND chapter_no=$2", session.get("project_id"), chapter_no)
                    if ch:
                        await db.execute(
                            "INSERT INTO review_reports (project_id, chapter_id, reviewer_model, dimensions, score, summary, raw_content) VALUES ($1,$2,$3,$4,$5,$6,$7)",
                            session["project_id"], ch["id"], r["model"], "{}", 85, r.get("content", "")[:500], r.get("content", ""),
                        )
```

---

## 6. state.entity.upsert → 标注批量创建时的完整字段

**问题**: agent 只传 name + entity_type，aliases/description/tags/profile/importance 等全空

**文件**: `novel-os-mcp/src/novel_os_mcp/tools/novel_gen.py` (agent 生成的 build_world workflow_guide 中的 batch 步骤不需要改)

**方案**: 工具 docstring 强化字段说明，agent 创建实体时按模板填全

```python
@mcp.tool(name="state.entity.upsert")
async def state_entity_upsert(
    workspace: str,
    project: str,
    entity_type: str,     # character/location/faction/item
    name: str,
    summary: str = "",    # ⚠️ 必填：角色/地点的简要描述(50-200字)
    description: str = "",# ⚠️ 建议填：详细描述
    profile: dict = {},   # ⚠️ 建议填：角色档案{age,appearance,personality,background}
    aliases: list[str] = [],
    tags: list[str] = [],
    importance: str = "medium",  # low/medium/high
    ...
```

在 build_world 的 workflow_guide.steps 中，为 entity.upsert batch 步骤添加 note 提示必填字段。

---

## 7. plot.thread.upsert → 默认值

**问题**: 创建 plot_thread 时 thread_type/current_chapter_no 为空

**文件**: `novel-os-mcp/src/novel_os_mcp/services/plot.py`

**方案**: INSERT 时设置默认值

```python
INSERT INTO plot_threads (project_id, key, title, thread_type, status, current_chapter_no, ...)
VALUES ($1, $2, $3, COALESCE($4, 'side'), COALESCE($5, 'active'), COALESCE($6, 0), ...)
```

---

## 已修复（不在此文档范围内）

- discussion_room: consensus 改用 control model 判定
- discussion_room: 429 指数退避 + 3s delay
- discussion_room: max_rounds→3 + partial status + 循环审核
- discussion_room: 完成时 auto-aggregate review_job
- workflow.submit_chapter_commit: 删除 accept 参数
- pipeline.generate: 删除阻塞的 _extract_knowledge_from_content
- Web UI: arc/pacing 页面 project_id 缺失修复
- Web UI: volumes.goals Array.isArray 防御
- proper_nouns 表已创建
- universal_knowledge category_id 已补充
