# Novel OS 总开发计划（Roadmap）

> 本文是 `docs/07-planning/` 下各功能规划的**排期总表**：定义优先级、依赖、阶段划分、工时与验收标准。
> 各功能的设计细节见对应子文档，本文不重复设计内容，只回答三件事：**先做什么、为什么这个顺序、做完怎么算完成**。

| 项 | 值 |
|---|---|
| 文档版本 | v1.0 |
| 创建日期 | 2026-10-10 |
| 覆盖范围 | 6 份功能规划 + 4 类技术债（建表 SQL 缺失 / 功能文档缺失 / 文档重复 / 工具目录滞后） |
| 状态图例 | 待开始 / 进行中 / 已完成 / 阻塞 |

---

## 一、背景与现状

### 1.1 近期已完成（排期前提）

近期落地的改动已经改变了几份规划文档的前提条件，排期时必须先扣掉这部分：

| 改动 | 对排期的影响 |
|---|---|
| 调性系统（`ref_tones` / `ref_tone_rules` + `tone.*` 5 个工具 + `tone-management-page.js`） | 已上线，只需补文档（D-03）与建表 SQL（D-01） |
| 讨论室 `tones` 数据源 | 已接入，`discussion_room.py` 的 schema hint 已指向 `ref_tones` |
| 14 步 pipeline（生成+保存+记录合并） | `context.py` / `novel_gen.py` 近期改动频繁，后续改造必须串行 |
| 旧知识工具下线 | `knowledge_service.py`、`tools/knowledge.py`、`js/pages/knowledge.js` **已删除**，JS 中 `knowledge.*` 调用 **0 处** |
| 全局规则 / 进化日志页面 | `global-rules-page.js`、`evolution-logs-page.js` 已存在并调用 `global_rules.*` / `evolution.*` |

### 1.2 待办来源清单

| # | 来源 | 条目 |
|---|---|---|
| 1 | `07-planning/global-rules-plan.md` | 全局规则表 + 管理页 + 项目规则升级流程 |
| 2 | `07-planning/evolution-gatekeeper.md` | gatekeeper 门禁 + `evolution_logs` + 回滚 |
| 3 | `07-planning/dynamic-rules-retrieval.md` | 规则向量检索四层流程 + `rule_summaries` |
| 4 | `07-planning/dynamic-context-budget.md` | 上下文预算动态化（替换硬编码 8000） |
| 5 | `07-planning/category-unification.md` | 两套分类体系统一、删除旧工具与旧表 |
| 6 | `07-planning/knowledge-classification.md` | 基础数据 4 层分类 + CSV 迁移 |
| 7 | `README.md` 路线图 | 缺失建表 SQL、文档去重、i18n |
| 8 | 代码审计（本次） | 4 张表代码已读写但仓库无建表 SQL；工具目录与页面索引的工具名与实际不符 |

---

## 二、待办项总表

| ID | 名称 | 类型 | 优先级 | 依赖 | 预估 | 状态 |
|---|---|---|---|---|---|---|
| **D-01** | 补齐 4 张运行时表建表 SQL（`global_rules`、`evolution_logs`、`ref_tones`、`ref_tone_rules`）+ `canon_rules` 3 个升级列 | 技术债 | **P0** | — | 40 min | SQL 已写，**待生产库核对后执行** |
| **D-02** | `context.py` 解耦 `knowledge_base` 表 | 功能 | **P0** | — | 20 min | 待开始 |
| **D-03** | 调性系统补文档 | 文档 | P1 | — | 30 min | ✅ 已完成 → [03-backend/tone-system.md](../03-backend/tone-system.md) |
| **D-04** | 工具目录与页面索引校正（含补齐 `novel.wizard.*` 6 个工具 + 新增 `tone.*` 章节） | 文档 | P1 | — | 20 min | ✅ 已完成 |
| **D-05** | 文档去重 + 总索引更新（共删除 7 份重复文档：`novel-os-web/docs/` 5 份 + `docs/` 根目录 2 份） | 文档 | P1 | — | 30 min | ✅ 已完成 |
| **D-06** | 动态上下文预算 | 功能 | P1 | — | 35 min | 待开始 |
| **D-07** | 全局规则体系（`global_rules` 表 + 4 工具 + 页面合并） | 功能 | P2 | D-01 | 85 min | 待开始 |
| **D-08** | 动态规则检索（四层匹配 + `rule_summaries`） | 功能 | P2 | D-01, D-06 | 90 min | 待开始 |
| **D-09** | 进化门禁（gatekeeper + `evolution.*` 工具 + 日志页） | 功能 | P2 | D-01, D-07 | 73 min | 待开始 |
| **D-10** | 知识分类体系统一收尾（DROP 5 张旧表 + 文档更新） | 功能 | P1 | D-02 | 25 min | **部分已完成** |
| **D-11** | 基础数据分类体系 + CSV 迁移 | 功能 | 待定 | 需 D-10 落地 | ~4 天 | **阻塞** |

**工时合计（不含 D-11）**：约 448 min ≈ 7.5 h

### D-10 已完成 / 剩余范围

原规划 65 min 中，风险最高的部分**已经做完**：

| 原计划步骤 | 状态 | 证据 |
|---|---|---|
| 删除 `knowledge_service.py` | ✅ 已完成 | 文件不存在 |
| 删除 `tools/knowledge.py` 的 21 个旧工具 | ✅ 已完成 | 文件不存在，代码 0 处引用 |
| 删除 `js/pages/knowledge.js` + `index.html` 引用 | ✅ 已完成 | 文件不存在，`index.html` 无引用 |
| 前端 `knowledge-stats` / `knowledge-review` 页面改工具名 | ✅ 已完成 | `js/pages/` 下 `knowledge.*` 调用 0 处 |
| `tools/vector.py` 改查 `universal_knowledge` | ✅ 已完成 | 代码 0 处引用旧表 |
| **`context.py` 解耦 `knowledge_base`** | ❌ **待做（D-02）** | `services/context.py` 仍有 16 处引用 |
| **DROP 5 张旧表** | ❌ **待做** | `categories` 在 Python 代码 0 处引用，仅老迁移 SQL 出现 |
| **数据库文档清理** | ❌ **待做** | `04-database/` 仍按旧体系描述 |

---

## 三、优先级与依赖分析

### 3.1 排序原则

1. **数据完整性优先** — 代码已在读写但仓库无建表 SQL（D-01），任何一次环境重建都会直接崩，必须先补
2. **改同一文件的串行化** — `services/context.py` 被 D-02 / D-06 / D-07 / D-08 同时改动，必须排成串行，禁止并行开发
3. **先解耦后删除** — D-02 先把 `context.py` 从 `knowledge_base` 摘出来，D-10 才能安全 DROP 表
4. **收益/风险比** — D-06（35 min，直接改善生成质量）排在 D-08（90 min，依赖向量链路）之前
5. **已开工的收尾优先** — D-10 剩余工作量小（25 min）且能解除 D-11 的阻塞，紧随阶段 0 之后做掉

### 3.2 依赖图

```
阶段 0
  D-01 建表 SQL ──┬──────────────┬──────────────┐
                  ▼              ▼              ▼
阶段 1        阶段 2         阶段 3          阶段 4
  D-02         D-06           D-07 ──> D-09    (D-08 依赖 D-07)
  D-10        动态上下文预算   全局规则      进化门禁
  分类收尾         │             │
                  └──────> D-08 动态规则检索（与 D-06/D-07 串行，同改 context.py）

阶段 5：D-03 / D-04 / D-05 文档收尾（不阻塞开发，当前进行中）

D-11 基础数据分类体系  ✗ 阻塞：需先完成 D-10，再换映射目标
```

### 3.3 冲突与阻塞项

**D-11（`knowledge-classification.md`）** 整套 4 层分类与 CSV 迁移方案建立在 `categories` + `knowledge_base` 之上，而 `universal_knowledge` 才是活跃表（9 个 Python 文件在用），`knowledge_base` 在 D-02 之后将变成孤儿表。

处理方式：**挂起，不重写**。等 D-10 落地后只需做「换映射目标」级别的改造：

- §4.1 字段映射表：`knowledge_base` → `universal_knowledge`，`category_slug` → `ref_categories.slug`
- §3 四层分类树：挂到现有 `ref_categories` 二级分类下，而非新建 `categories`
- §5 前端设计、§8 兼容性、§9 风险**均无需改动**

保留理由是：它是整个计划里唯一「往库里填真数据」的任务（450+ 条创作方法论 CSV），长期价值最高。

---

## 四、阶段划分

### 阶段 0：数据完整性收口（P0，~60 min）

**目标**：让仓库 SQL 与代码实际依赖对齐，任何环境重建后可一次拉起。

**包含项**：D-01

| 步骤 | 内容 |
|---|---|
| 0.1 | 新增 `deploy/nas/postgres/migrations/222_runtime_tables.sql`（幂等） |
| 0.2 | 新增 `deploy/nas/postgres/migrations/223_rule_summaries.sql` |
| 0.3 | 更新 `docs/04-database/migrations.md` 与表说明文档 |
| 0.4 | 生产库核对与执行 |

**验收标准**

```sql
-- 1. 四张表可查（不应报 relation does not exist）
SELECT count(*) FROM global_rules;
SELECT count(*) FROM evolution_logs;
SELECT count(*) FROM ref_tones;
SELECT count(*) FROM ref_tone_rules;

-- 2. canon_rules 升级列存在
SELECT promotion_status, promoted_to_global_id, discussion_id FROM canon_rules LIMIT 1;
```

```
# 3. 工具可调用且返回 ok
ApiClient.callTool('global_rules.list', {})
ApiClient.callTool('evolution.stats', {})
ApiClient.callTool('tone.list', {})
```

- 新建空库执行全部 init + migration 后，上述检查全部通过

**执行方式**

在 NAS 的 `/opt/novel-os/deploy/nas/` 目录内执行（脚本会自动做执行前结构核对 + 交互确认 + 执行后验证）：

```bash
sh scripts/apply-migration.sh 222_runtime_tables.sql global_rules evolution_logs ref_tones ref_tone_rules
sh scripts/apply-migration.sh 223_rule_summaries.sql rule_summaries
```

> 通过 ssh / plink 远程调用时，**必须**加 `APPLY_MIGRATION_YES=1`，否则脚本读不到交互输入会直接取消：
>
> ```bash
> APPLY_MIGRATION_YES=1 sh scripts/apply-migration.sh 222_runtime_tables.sql global_rules evolution_logs ref_tones ref_tone_rules
> ```

**执行前必须做的核对（重点风险）**

这 4 张表多半是之前在 NAS 上手工建的，仓库里没有。脚本会先打印 `\d` 结果，执行前先比对生产库现有结构与代码期望结构。

差异用 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 补齐，**不要 `DROP`**。已知需要关注的差异点：

- `global_rules.rule_type` 代码支持 `creative` / `compliance` / `polish` 三值，规划文档里只写了前两个
- `evolution_logs.risk_level` 代码会写入 `info`（回滚日志），规划文档只定义了 `low/medium/high`

**回滚方案**：迁移全部 `CREATE TABLE IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`，幂等可重复执行；回滚即删除新增迁移文件，已建表保留不影响运行。

---

### 阶段 1：知识体系统一收尾（~45 min）

**目标**：`ref_categories` 成为唯一分类树，`context.py` 不再依赖旧表。

**包含项**：D-02（20 min）+ D-10 剩余（25 min）

| 步骤 | 内容 |
|---|---|
| 1.1 | `context.py::_retrieve_knowledge_base` 改为查 `state_entities` + `project_knowledge`（见 `category-unification.md` §2.3） |
| 1.2 | 上传 + 重建 MCP 容器，验证 `workflow.prepare_chapter_context` 不报错 |
| 1.3 | 备份后执行 `deploy/nas/postgres/migrations/224_drop_legacy_kb_tables.sql`（DROP 5 张表） |
| 1.4 | 更新 `04-database/` 中旧体系描述（已完成：System 1 已标废弃，migrations.md 已补 224） |

> 224 已处理一个 DROP 障碍：`knowledge_base.category_id` 有指向 `categories(id)` 的外键，
> 迁移里先用 DO 块动态查名并解除该约束，再 DROP，否则会被拒绝。

**验收标准**

- `grep -rn "knowledge_base" novel-os-mcp/src/` 只剩注释与 section id，无 SQL 查询
- `kb.genre.list`、`kb.category.tree`、`kb.uk.search` 正常返回
- 5 张旧表 DROP 后，全站冒烟无报错

**回滚方案**

- 1.1 为只读链路替换，回退即恢复原查询；旧表在 1.3 之前不删，因此 1.1 失败不影响任何数据
- 1.3 执行前先 `pg_dump` 单表备份，DROP 后如需恢复可直接导入

**✅ 已核实：`knowledge_tags` 同名表冲突**

同名表在两处迁移中都被创建，**且都用了 `CREATE TABLE IF NOT EXISTS`**：

| 迁移 | 结构 | 归属 |
|---|---|---|
| `190_extensible_categories.sql` | 联合表：`knowledge_id` FK→`knowledge_base(id)`、`tag_id` FK→`tags(id)`、复合主键 | 旧体系 |
| `210_restructure_categories.sql` | 独立表：`id` PK、`item_id`、`tag`、`tag_type` | 新体系 |

按文件名顺序执行时，**190 先建表，210 因 `IF NOT EXISTS` 静默失效** —— 库里实际存在的是旧体系联合表，新体系的独立表从未被创建。

结论：

1. **DROP 是安全的** —— Python 代码中 `knowledge_tags` / `knowledge_vectors` / `genre_category_bindings` / `setting_category_relations` / `categories` 的引用数**均为 0**
2. **后遗症需记账** —— 若将来新体系要用 `knowledge_tags`（`item_id`/`tag`/`tag_type` 结构），它当前并不存在，且重跑 210 也不会创建（表已存在）。届时必须先 DROP 再重跑 210

---

### 阶段 2：上下文质量提升（~35 min）

**目标**：消除 `context.py` 中硬编码的 8000 token 预算。

**包含项**：D-06

| 步骤 | 内容 |
|---|---|
| 2.1 | 新增 `_detect_context_window()`，从 `model_profiles.metadata.max_tokens` + 已知容量表推断 |
| 2.2 | `_compute_section_budgets` 替换为两级动态分配算法 |
| 2.3 | 加配置开关，保留旧实现以便回退 |
| 2.4 | 部署 + 按 `dynamic-context-budget.md` §2.4 三档模型实测对比 |

**验收标准**

- 配置 128K 模型后，P0/P1 section 预算随之放大（规则 19K + 状态 25K 量级）
- 未配置模型时回落为原行为（8000），与改造前输出一致
- 4K 老模型下 P3 section 全部跳过，不报错

**回滚方案**：开关切回旧 `_compute_section_budgets`；开关默认保持旧行为，验证通过后再切新。

---

### 阶段 3：规则体系（~175 min）

**目标**：全局规则可管理、规则检索从"全量加载"升级为"按需匹配"。

**包含项**：D-07（85 min）→ D-08（90 min），**串行执行**

| 步骤 | 内容 |
|---|---|
| 3.1 | `global_rules` 工具验证（表由阶段 0 创建）；`context.py` 加载规则时 UNION 全局规则 |
| 3.2 | `rules-list-page.js` 合并 `compliance-page.js`，Tab 切换 creative / compliance |
| 3.3 | `rules.py` 新增 `index_to_qdrant` / `search_by_embedding` / `search_by_keyword` |
| 3.4 | `context.py::_load_rules_section` 改四层流程 + `_infer_scene_type` + `_summarize_rules_by_group` |
| 3.5 | `canon.py::rules.upsert` 保存后自动索引；创建 `rule_summaries`（阶段 0 已建） |
| 3.6 | `rules-list-page.js` 表单增加 genre / scene_type / rule_group |

**验收标准**

- 全局规则创建后，在任意项目的 `context.preview` 中出现
- 项目规则「升级为全局」后，`canon_rules.promotion_status = 'promoted'`
- 规则 >30 条时自动归纳为 `rule_summaries` 摘要
- 停掉 Qdrant 后，规则检索降级到 tsvector 不报错（降级链路必须实测）

**回滚方案**：3.1/3.2 可独立回退；3.3-3.5 通过保留原 `_load_rules_section` 并用开关切换。

---

### 阶段 4：进化门禁（~75 min）

**目标**：讨论室 / Agent 产出经风险评估后写入，全程可追溯可回滚。

**包含项**：D-09（73 min）

| 步骤 | 内容 |
|---|---|
| 4.1 | `services/gatekeeper.py` 已就绪，验证 `evolution_logs` 写入链路（表由阶段 0 创建） |
| 4.2 | `discussion_room.apply_results` 全局级写入改走 gatekeeper |
| 4.3 | 全局规则页改造为普通用户只读 |
| 4.4 | 端到端验证：低风险自动写入 / 中高风险待审批 / 管理员回滚 |

**验收标准**

- 写入项目级表 → `risk_level=low`、`auto_applied=true`
- 写入全局表且来源为单 Agent → `risk_level=medium`，不自动写入
- 管理员回滚后，目标表记录恢复到 `old_value`，并新增一条 `action=ROLLBACK` 日志
- 进化日志页按来源 / 风险 / 目标表筛选可用

**回滚方案**：gatekeeper 为旁路组件，出问题可直接让 `apply_results` 跳过门禁走原直接写表路径。

---

### 阶段 5：文档收尾（~80 min，当前进行中）

**包含项**：D-03（30 min）、D-04（20 min）、D-05（30 min）

| 步骤 | 内容 |
|---|---|
| 5.1 | 新增 `docs/03-backend/tone-system.md`（数据模型 / 5 个工具 / 页面 / 消费链路） |
| 5.2 | 校正 `docs/03-backend/tools/tool-catalog.md` 与 `docs/02-frontend/pages/README.md` 中与实际不符的工具名 |
| 5.3 | 删除 `novel-os-web/docs/` 下 5 份重复规划文档，统一指向 `docs/07-planning/` |
| 5.4 | 更新 `docs/00-index/README.md` 与 `README.md` 路线图 |

**验收标准**

- 每份文档都能从 `00-index/README.md` 到达，无孤儿文档
- 页面索引中的工具名与 `tools/` 下 `@mcp.tool(name=...)` 实际注册名一致
- 已删除文档无残留引用

---

## 五、风险与缓解

| 风险 | 影响 | 缓解措施 |
|---|---|---|
| 生产库已手工建表，结构与代码期望不一致 | 迁移执行失败或字段缺失 | 执行前 `\d` 比对，差异用 `ALTER ADD COLUMN IF NOT EXISTS` 补齐，不 `DROP` |
| `context.py` 被多任务并行改动 | 代码冲突、生成链路中断 | 阶段 1/2/3 强制串行，一个阶段合并部署后再开下一个 |
| `knowledge_tags` 归属不明 | 误删新体系在用表 | 阶段 1 执行前先确认创建来源，必要时暂缓 DROP 该表 |
| D-10 DROP 表后仍有隐式引用 | 运行时报错 | DROP 前跑"工具调用来源扫描"，DROP 后跑端到端冒烟 |
| 每次 MCP 改动都要重建容器（3-5 min） | 排期被部署时间放大 | 同阶段内改动合并为一次构建 |
| D-11 体系冲突，做完即作废 | 浪费 4 天 | 明确挂起，等 D-10 落地后做映射目标替换 |

---

## 六、进度记录

| 日期 | 阶段 | 完成项 | 备注 |
|---|---|---|---|
| 2026-10-10 | — | 建立 roadmap v0.1 提纲 + 代码审计 | 发现 4 张表缺建表 SQL、D-10 已完成大半 |
| 2026-10-10 | 阶段 0 | D-01 迁移脚本 222 / 223 编写完成，`04-database` 已同步 | 待生产库 `\d` 核对后执行 |
| 2026-10-10 | 阶段 1 | D-02 / D-10 剩余范围核定 | 旧工具与前端已清理，只剩 `context.py` 解耦 + DROP 表 |
| 2026-10-10 | 阶段 2 | D-06 开发计划章节补齐 | `dynamic-context-budget.md` 新增第三章 |
| 2026-10-10 | 阶段 3 | D-08 开发计划章节补齐 | `dynamic-rules-retrieval.md` 新增第六章，原总结顺延为第七章 |
| 2026-10-10 | 阶段 5 | D-03 / D-04 / D-05 文档收尾完成 | 新增 tone-system.md、校正工具目录与页面索引、删除 5 份重复文档 |
| 2026-10-10 | 阶段 0 | 新增 `deploy/nas/scripts/apply-migration.sh` | 迁移无法由 Agent 直接执行（缺 `~/.novel-os.env`），改为一键脚本 |
| 2026-10-10 | 阶段 1 | `knowledge_tags` 同名表冲突已核实 | 190 的联合表生效、210 的独立表静默失效；5 张待删表代码引用均为 0 |
| 2026-10-10 | D-11 | `knowledge-classification.md` 加冻结横幅 | 写明冻结原因、解锁条件与解冻后的改造范围 |
| 2026-10-10 | 前端 | 修复 `tone-management-page.js` 两个 bug | 描述字段存成空串（`tone-desc`）、删除规则后列表未刷新 |
| 2026-10-10 | 阶段 5 | 补查重复文档，再删 `docs/` 根目录 2 份 | `FIX_PLAN_BODY_LOCAL.md`、`MCP_TOOL_FIX_PLAN.md` 与 `08-fix-plans/` 下两份哈希完全一致 |
| 2026-10-10 | 阶段 5 | 补齐工具目录 §51 | `novel.wizard.*` 实际 6 个工具全部收录（原只列 2 个），并标注 6+5=11 的总数口径 |

---

## 七、相关文档

| 文档 | 关系 |
|---|---|
| `07-planning/dynamic-context-budget.md` | D-06 设计（含开发计划） |
| `07-planning/dynamic-rules-retrieval.md` | D-08 设计（含开发计划） |
| `07-planning/global-rules-plan.md` | D-07 设计 |
| `07-planning/evolution-gatekeeper.md` | D-09 设计 |
| `07-planning/category-unification.md` | D-02 / D-10 设计 |
| `07-planning/knowledge-classification.md` | D-11（阻塞中） |
| `03-backend/tone-system.md` | D-03 产出 |
| `04-database/migrations.md` | D-01 / D-10 需同步更新 |
| `00-index/README.md` | D-05 需同步更新 |
