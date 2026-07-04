# Novel OS 服务层优化方案

> 审计日期：2026-07-02
> 涉及文件：services.py, main.py, kb_service.py, p8_services.py, utils.py, 以及 4 个重复 ensure_json_value 的模块

---

## 一、P0 — 运行时崩溃 / 数据错误（5 项）

### 1.1 kb_service.py `genre_preheat` 使用 `self.db`（应为 `self._db`）

- **位置**：`kb_service.py` 第 752、764、775 行
- **现状**：构造函数存 `self._db = db`，但 `genre_preheat` 方法内三处用 `self.db`
- **影响**：调用 `kb.genre.preheat` 必触发 `AttributeError`，功能完全不可用
- **修复**：三处 `self.db` → `self._db`

### 1.2 `genre_preheat` INSERT 列名与表 schema 不匹配

- **位置**：`kb_service.py` 第 775-784 行
- **现状**：INSERT 使用 `title`、`content`、`source`、`source_id` 列
- **表 schema**（`205_knowledge_base_system.sql` 第 180-194 行）：
  ```sql
  project_knowledge (
    id, project_id, category, key, value JSONB,
    description, chapter_no, related_entry_ids, tags, status, ...
  )
  ```
- **影响**：INSERT 报列名不存在错误；即使加了 `ON CONFLICT`，数据也无法被 `pk_get`/`pk_list` 读取（它们用 `key`/`value`）
- **修复**：改用 `pk_upsert(project_id, category, key, value, description, tags)` 方法，或直接 INSERT 正确列名：`key`（标题）+ `value`（jsonb 内容）

### 1.3 `genre_preheat` 缺少事务保护 + ON CONFLICT

- **位置**：`kb_service.py` 第 763-786 行
- **现状**：SELECT 查重 → 循环判断 → INSERT，无事务无 `ON CONFLICT`
- **影响**：并发调用产生重复数据
- **修复**：用 `ON CONFLICT (project_id, category, key) DO NOTHING` 或包裹在事务中

### 1.4 main.py `state_snapshots` INSERT 缺少 `project_id`

- **位置**：`main.py` 第 6091-6099 行
- **现状**：
  ```sql
  INSERT INTO state_snapshots (entity_id, is_current, state, effective_chapter_no, source_type)
  SELECT id, true, $3::jsonb, $4, 'auto_update'
  FROM state_entities WHERE id = $2
  ```
- **表 schema**：`project_id UUID NOT NULL`（必须有值）
- **影响**：INSERT 必报 `NOT NULL constraint failed` 错误；异常被 `except Exception: pass` 吞掉，静默失败
- **修复**：INSERT 加 `project_id` 列，SQL 加 `WHERE project_id = $1 AND id = $2` 防跨项目污染

### 1.5 p8_services.py 零导入

- **位置**：`p8_services.py` 第 1 行
- **现状**：使用 `Database`、`Any`、`dict`、`list`、`row_to_dict`、`json_dumps`、`ensure_json_value` 均未导入
- **影响**：`from .p8_services import RelationshipGraphService` 触发 `NameError`，图谱相关 3 个 MCP 工具全部不可用
- **修复**：添加导入语句

---

## 二、P1 — 功能缺陷 / 技术债（12 项）

### 2.1 `ensure_json_value` 4 文件重复定义

- **位置**：`services.py:13`、`novelty.py:397`、`style_fingerprint.py:375`、`character_arc.py:332`
- **影响**：改逻辑需改 4 处，极易遗漏导致行为不一致
- **修复**：提取到 `utils.py`，4 个文件改为 `from .utils import ensure_json_value`

### 2.2 24 处 `except Exception` 静默吞错

- **关键位置**：
  - `services.py:4001` — UK 检索失败无日志
  - `services.py:4226` — 压缩上下文加载失败无日志
  - `services.py:4248` — 通用知识检索失败无日志
  - `services.py:4265` — 项目知识检索失败无日志
  - `main.py:6101` — 状态快照更新失败无日志
  - `p8_services.py:342` — 离线同步变更应用失败无日志
- **影响**：生产环境无法排查检索失败原因，功能静默降级
- **修复**：替换为 `logger.warning("...")` 或 `logger.exception("...")`，保留异常信息

### 2.3 `prepare_chapter_context` 349 行，19 个步骤

- **位置**：`services.py` 第 4054-4402 行
- **影响**：不可测试、不可维护、改一处影响全局
- **修复**：拆分为独立方法：
  - `_load_rules_section()`
  - `_load_state_section()`
  - `_load_kb_section()`
  - `_load_foreshadowing_section()`
  - `_load_summaries_section()`
  - `_assemble_and_trim()`
  - `_build_warnings()`

### 2.4 `services.py` 8208 行 17 个类

- **影响**：IDE 卡顿、合并冲突频繁、导航困难
- **修复**：拆分为独立模块文件：
  - `workspace_service.py` → WorkspaceService
  - `canon_service.py` → CanonService
  - `rules_service.py` → RulesService
  - `compliance_service.py` → ComplianceService
  - `plot_service.py` → PlotService
  - `memory_service.py` → MemoryService
  - `context_service.py` → ContextService（保留）
  - `review_service.py` → ReviewService + 子类
  - `workflow_service.py` → WorkflowService
  - `sync_service.py` → SyncService
  - `model_cost_service.py` → ModelCostService
  - `vector_index_service.py` → VectorIndexService
  - `archive_service.py` → ArchiveService
  - `backup_service.py` → BackupService
  - `services.py` 仅保留导入和工厂函数

### 2.5 `main.py` 6116 行 157 个 tool 平铺

- **影响**：同 2.4，且 Agent 选工具时上下文浪费
- **修复**：拆分为 domain 模块：
  - `tools_auth.py` — auth/workspace/user 相关
  - `tools_canon.py` — canon/rules/compliance
  - `tools_plot.py` — plot/foreshadowing/volume
  - `tools_memory.py` — memory/state/reference
  - `tools_context.py` — workflow/context
  - `tools_review.py` — review/council
  - `tools_kb.py` — knowledge base/UK/PK
  - `tools_graph.py` — graph/relationship
  - `tools_system.py` — admin/system/cache/backup
  - `main.py` 只负责组装和启动

### 2.6 `_retrieve_knowledge_base` UK 搜索逐词循环

- **位置**：`services.py` 第 3975-4002 行
- **现状**：最多 5 个 focus term，每个触发 1 次 `uk_search`，共 5 次独立 SQL
- **影响**：每次 `prepare_chapter_context` 多 5 次 DB 查询
- **修复**：合并为 1 次批量查询（`WHERE topic ILIKE ANY($1)` 或全文检索）

### 2.7 `_load_delta_state` 空 ID 集合处理不当

- **位置**：`services.py` 第 3850 行
- **现状**：`list(known_entity_ids) if known_entity_ids else [""]`
- **影响**：传入空字符串 `""` 到 SQL `NOT IN` 子句，语义不正确
- **修复**：空集合时直接走全量查询分支，不经过 delta 逻辑

### 2.8 `_compute_section_budgets` pacing 调整硬编码

- **位置**：`services.py` 第 3762-3830 行
- **影响**：用户无法自定义节奏分配比例
- **修复**：从 `budget` 字典读取用户自定义比例，硬编码值作为 fallback defaults

### 2.9 增量上下文不完整

- **位置**：`services.py` `prepare_chapter_context` 中 state 和 summaries 有 delta，rules/foreshadowing 无
- **影响**：增量效果打折扣
- **修复**：为 rules 和 foreshadowing 增加 `previous_context` delta 逻辑

### 2.10 p8_services.py `_apply_upsert`/`_apply_delete` 空实现

- **位置**：`p8_services.py` 第 359-366 行
- **影响**：离线同步功能是空壳
- **修复**：根据 `entity_type` 分发到对应 Service（state/foreshadowing/canon）

### 2.11 services.py 两处 TODO 未实现

- **位置**：`services.py:7446`（向量生成）、`services.py:7831`（归档逻辑）
- **影响**：向量索引和归档功能不完整
- **修复**：7446 接入 `embedding_service`，7831 实现实际归档逻辑或标记为 stub

### 2.12 审查团无并行执行引擎

- **位置**：`review.council.dispatch` 返回模型列表，但无机制并行调用 LLM
- **影响**：调度工具存在但无法真正并行提交报告
- **修复**：在 `ReviewService` 中增加 `dispatch_parallel` 方法，使用 `asyncio.gather` 并行调用

---

## 三、P2 — 架构 / 性能 / 体验（6 项）

### 3.1 无自动化测试

- **影响**：重构必破，回归无法验证
- **修复**：为核心方法（prepare_chapter_context、uk_search、genre_preheat）编写 pytest 测试

### 3.2 tool 描述过于简单

- **影响**：Agent 难以判断何时用哪个 tool
- **修复**：为每个 tool 补充 2-3 句描述，包含使用场景和参数说明

### 3.3 `model.route` 无实际路由逻辑

- **影响**：模型选择功能是空壳
- **修复**：实现基于 cost/quality/speed 的路由策略

### 3.4 前端无可视化页面

- **影响**：图谱/因果链/人物弧线后端就绪但无法展示
- **修复**：新增前端页面（依赖 P2 拆分后的前端工作）

### 3.5 压缩策略仍是截断

- **影响**：长文本压缩质量差
- **修复**：用 LLM 做结构化提取（key entities + relationships + timeline）

### 3.6 无请求限流/熔断

- **影响**：恶意调用或级联故障无保护
- **修复**：在 MCP server 入口加 rate limiter

---

## 四、执行计划

| 阶段 | 任务 | 预计改动文件 |
|------|------|------------|
| Phase 1 | P0 修复（1.1-1.5） | kb_service.py, main.py, p8_services.py |
| Phase 2 | P1 公共函数提取（2.1） | utils.py, novelty.py, style_fingerprint.py, character_arc.py |
| Phase 3 | P1 错误处理（2.2） | services.py, main.py, p8_services.py, 等 |
| Phase 4 | P1 services.py 拆分（2.4 + 2.3） | services.py → 多个 *_service.py |
| Phase 5 | P1 main.py 拆分（2.5） | main.py → tools_*.py |
| Phase 6 | P1 功能补全（2.6-2.12） | services.py, kb_service.py, p8_services.py |
| Phase 7 | 同步部署 | sync_mcp.py → NAS |

每个 Phase 完成后同步部署验证。
