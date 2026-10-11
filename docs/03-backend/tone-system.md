# 调性系统（Tone System）

> **状态**：已实现（代码与页面均已上线），本文档为补录。
> 调性（tone）= 一部作品的情绪底色（如"热血爽文 / 暗黑压抑 / 轻松搞笑"），用于在项目创建与讨论室环节自动带入对应创作规则。
> 总排期见 [07-planning/roadmap.md](../07-planning/roadmap.md) 的 D-01 / D-03。

---

## 一、概述

### 1.1 解决什么问题

在引入本系统前，基调只是 `project_profile.tone_style` 里的一个自由字符串，带来三个问题：

| 问题 | 后果 |
|---|---|
| 基调不可枚举 | 项目向导只能展示硬编码选项，管理员无法增删 |
| 基调无法驱动规则 | 选了"暗黑压抑"，创建出来的项目规则与选"轻松搞笑"完全一样 |
| 基调不可作为检索维度 | 讨论室、知识检索都无法按情绪底色筛选素材 |

结构化之后：基调成为一张可维护的参考表（`ref_tones`），每条基调挂一组规则模板（`ref_tone_rules`），项目创建时按所选基调批量生成 `canon_rules`。

### 1.2 在系统中的位置

```
            ref_tones / ref_tone_rules          system_style_profiles
                    │  (管理员维护)                      │  (系统预设)
        ┌───────────┼──────────────┐                    │
        ▼           ▼              ▼                    ▼
  novel_wizard  项目 profile   讨论室 tones         style_profiles
  向导选项       tone_style     数据源              （项目级文风）
        │
        ▼
  canon_rules（按基调批量生成的初始规则）
```

- `ref_tones` / `ref_tone_rules` 由 `tone.*` 工具维护（管理员）
- 项目侧只消费，不回写

---

## 二、数据模型

### 2.1 `ref_tones`

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | UUID | PK | |
| `slug` | TEXT | NOT NULL, UNIQUE | 业务键，如 `hot-blooded`；`tone.upsert` 的冲突更新目标 |
| `name` | TEXT | NOT NULL | 展示名，如 `热血爽文`；向导下拉与基调匹配均用此值 |
| `description` | TEXT | NOT NULL, DEFAULT '' | 说明 |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | 停用后不出现在向导选项 |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 0 | 排序 |

### 2.2 `ref_tone_rules`

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | UUID | PK | |
| `tone_slug` | TEXT | NOT NULL | 关联 `ref_tones.slug` |
| `rule_type` | TEXT | NOT NULL | 写入 `canon_rules.rule_type`（UI 提供 `style` / `forbidden` / `global` 三选） |
| `title` | TEXT | NOT NULL | |
| `content` | TEXT | NOT NULL | |
| `severity` | TEXT | NOT NULL, DEFAULT 'warning' | `info` / `warning` / `critical` |
| `sort_order` | INTEGER | NOT NULL, DEFAULT 0 | |

**索引**：`idx_ref_tone_rules_tone_slug`

**不建外键**：`tone.delete` 工具先删 `ref_tone_rules` 再删 `ref_tones`，显式级联。不建 FK 是为了避免迁移在已存在孤儿行的库上失败（见 §8 已知问题）。

### 2.3 建表 SQL

由 `deploy/nas/postgres/migrations/222_runtime_tables.sql` 提供（`CREATE TABLE IF NOT EXISTS`，幂等）。详见 [04-database/knowledge-tables.md](../04-database/knowledge-tables.md)。

---

## 三、MCP 工具

> 定义位置：`novel-os-mcp/src/novel_os_mcp/tools/novel_wizard.py`（`Tone Management Tools` 段）

| 工具 | 参数 | 权限 | 说明 |
|---|---|---|---|
| `tone.list` | — | read | 列出所有基调，每条附带其 `rules` 数组（按 `sort_order` 排序） |
| `tone.upsert` | `slug`, `name`, `description?`, `is_active?`, `sort_order?` | admin | 按 `slug` 冲突更新 |
| `tone.delete` | `slug` | admin | 先删 `ref_tone_rules` 再删 `ref_tones` |
| `tone.rule.upsert` | `tone_slug`, `rule_type`, `title`, `content`, `severity?`, `sort_order?`, `rule_id?` | admin | 传 `rule_id` 走更新，否则新建 |
| `tone.rule.delete` | `rule_id` | admin | 删除单条基调规则 |

### 返回值示例

```json
// tone.list
[
  {
    "id": "...", "slug": "hot-blooded", "name": "热血爽文",
    "description": "快节奏、强爽点", "is_active": true, "sort_order": 1,
    "rules": [
      { "id": "...", "rule_type": "style", "title": "战斗节奏", "content": "...", "severity": "warning", "sort_order": 0 }
    ]
  }
]
```

```json
// tone.upsert / tone.delete / tone.rule.upsert / tone.rule.delete
{ "ok": true, "slug": "hot-blooded" }
```

> 删除类工具返回 dict 而非 bool，遵循 `novel-os-web/docs/api-conventions.md` 的约定（返回 `bool` 会触发 FastMCP 的 `structured_content must be a dict` 错误）。

---

## 四、消费链路

### 4.1 新建项目向导（`novel_wizard`）

**① 选项加载**（`novel.wizard.questions` 附近）

```sql
SELECT name, slug, description FROM ref_tones WHERE is_active = true ORDER BY sort_order
```

查询为空时回落硬编码三项：`["热血爽文", "暗黑压抑", "轻松搞笑"]`，保证向导在空库下仍可用。

**② 写入项目 profile**

用户选择后写入 `project_profile.tone_style`，并用于首卷 metadata（`{"genre": ..., "tone": ..., "estimated_length": ...}`）。

**③ 按基调生成初始规则**（`_generate_rules_by_tone`）

匹配顺序（两轮，命中即停）：

1. `SELECT slug FROM ref_tones WHERE name = $1 AND is_active = true`
2. `SELECT slug FROM ref_tones WHERE slug = $1 AND is_active = true`

无论是否命中，都会先写入一条基础规则：

| rule_type | title | content | severity |
|---|---|---|---|
| `global` | 禁止事项 | 主角不能死亡，世界观设定不能自相矛盾 | `critical` |

命中基调后，把该基调下所有 `ref_tone_rules` 按 `sort_order` 追加到规则列表，最终一并写入项目 `canon_rules`。**未命中时只写基础规则，不报错**。

**④ 文风配置推荐**

`_recommend_system_configs` 用 `tone` 参与 `system_style_profiles` 的排序（`tone = $2` 优先），与基调规则相互独立。

### 4.2 讨论室数据源

`tools/discussion_room.py` 的 `source_hints` 中注册了 `tones` 数据源：

```python
"tones": "本次讨论的数据来源是「基调与文风」。\n"
         "数据表: ref_tones + ref_tone_rules + system_style_profiles\n"
         "结构: NEED: schema table=ref_tones\n"
         "结构: NEED: schema table=ref_tone_rules\n"
         "结构: NEED: schema table=system_style_profiles"
```

前端 `discussion-room-page.js` 的数据源下拉中可选 `tones`。讨论室在此维度下讨论"基调与文风是否一致"类问题。

### 4.3 与 `system_style_profiles` / `style_profiles` 的关系

三者都带 `tone` 语义，职责边界如下，避免误用：

| 表 | 职责 | 粒度 | 维护者 |
|---|---|---|---|
| `ref_tones` / `ref_tone_rules` | **情绪底色**及其创作约束规则 | 项目级，创建时批量写入 `canon_rules` | 管理员（`tone.*`） |
| `system_style_profiles` | **文风参数**预设（POV、时态、目标指标、样例段落） | 系统级预设，项目可 fork | 系统进化流程 |
| `style_profiles` | 项目实际使用的**文风档案** | 项目级 | 项目成员 |

简单说：`ref_tones` 回答"这个故事是什么味道"，`style_profiles` 回答"这句话该怎么写"。

---

## 五、前端页面

| 项 | 值 |
|---|---|
| 文件 | `novel-os-web/js/pages/tone-management-page.js` |
| 路由 ID | `tone-management` |
| 模式 | 自定义（基调卡片 + 二级规则弹窗），非标准 `PAGE_CONFIG` CRUD |
| 菜单入口 | `js/core/menu-manager.js` |
| 权限 | 页面可见即可读，写操作由 MCP 工具的 `admin` 权限兜底 |

### 交互结构

```
基调卡片列表（tone.list）
  ├─ 新增基调 ──> ModalDialog: slug / 名称 / 描述 / 启用 / 排序 ──> tone.upsert
  ├─ 编辑   ──> 同上（slug 只读）                              ──> tone.upsert
  ├─ 删除   ──> confirm                                        ──> tone.delete
  └─ 管理规则 ──> ModalDialog(lg) 规则列表
                    ├─ 新增/编辑规则 ──> ModalDialog(md) ──> tone.rule.upsert
                    │     新建不传 rule_id，编辑传 r.id
                    └─ 删除规则 ─────────────────────────> tone.rule.delete
```

- `init()` 返回 `true`，符合页面范式要求
- `ModalDialog.show()` 不返回布尔值，保存逻辑写在 `onConfirm` 回调里，回调内调 `ModalDialog.close()`

---

## 六、权限与校验

| 操作 | 权限 |
|---|---|
| `tone.list` | `read` |
| `tone.upsert` / `tone.delete` / `tone.rule.upsert` / `tone.rule.delete` | `admin` |
| 向导选择基调、按基调生成规则 | 项目创建者（走 `novel.wizard.*`） |

注意：`get_principal("admin")` 校验在工具层，前端页面不单独做权限判断——非管理员点击保存会被 MCP 拒绝。

---

## 七、运维

### 种子数据

**当前没有种子数据**。`ref_tones` 为空时，向导回落硬编码三项，功能不受影响；如需正式使用，请通过 `tone-management` 页面或 `tone.upsert` 工具录入。

建议的初始基调（与回落项一致，便于过渡）：

| slug | name | 说明 |
|---|---|---|
| `hot-blooded` | 热血爽文 | 快节奏、强爽点 |
| `dark-oppressive` | 暗黑压抑 | 低亮度、高代价 |
| `light-comedy` | 轻松搞笑 | 轻冲突、高趣味 |

### 新增一个基调

```json
{
  "tool": "tone.upsert",
  "args": { "slug": "hot-blooded", "name": "热血爽文", "description": "快节奏、强爽点", "is_active": true, "sort_order": 1 }
}
```

随后用 `tone.rule.upsert` 逐条挂规则（`tone_slug` 指向上面的 slug）。

### 备份与容器重建

- 数据存在 PostgreSQL，容器重建不丢失
- 但**建表 SQL 此前缺失**（已在 `222_runtime_tables.sql` 补齐）：重建空库而未执行该迁移时，`tone.*` 工具会全部报 `relation does not exist`

---

## 八、已知问题

| # | 问题 | 影响 | 建议 |
|---|---|---|---|
| 1 | `tone-management-page.js` 中描述输入框 id 为 `tone-desc`，但保存时读取的是 `tone-description` | **编辑基调时描述被存成空字符串** | ✅ 已修复（2026-10-10，统一读取 `tone-desc`） |
| 2 | `deleteRule()` 删除规则后只重渲染弹窗，未刷新 `this.tones` | 被删规则在重新加载页面前仍显示在列表里 | ✅ 已修复（2026-10-10，先记录 slug → `tone.rule.delete` → `loadTones()` → 重开弹窗） |
| 3 | `ref_tone_rules.tone_slug` 无外键约束 | 直接删 `ref_tones` 行会留下孤儿规则 | 一律走 `tone.delete` 工具；定期清理孤儿行 |
| 4 | 建表 SQL 缺失（历史问题） | 空库重建后工具不可用 | 已由 `222_runtime_tables.sql` 修复 |
| 5 | 文档未收录 | 索引中找不到本系统 | 已补本文，并同步 `tool-catalog.md` / `pages/README.md` |

---

## 九、相关文档

| 文档 | 关系 |
|---|---|
| `docs/07-planning/roadmap.md` | D-01（建表）、D-03（本文档） |
| `docs/04-database/knowledge-tables.md` | `ref_tones` / `ref_tone_rules` 表结构 |
| `docs/03-backend/tools/tool-catalog.md` | `tone.*` 工具登记 |
| `docs/02-frontend/pages/README.md` | `tone-management` 页面索引 |
