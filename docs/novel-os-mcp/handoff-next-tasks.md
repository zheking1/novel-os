# Novel OS MCP 后续开发任务

更新时间：2026-06-27

## 当前下一步

```text
NEXT: Phase 3.3 实体面板
DOING: Phase 3.2 规则面板（已完成部署）
DONE: Phase 3.1 Canon 文档 + 项目选择器
```

Phase 3.1 已完成并部署，包含：项目选择器下拉菜单、导航面板、Canon 文档 CRUD 面板。

---

## Phase 2.10 模型与成本工具

**状态**：DONE（NAS 冒烟测试通过）

**已实现**：
- 3 张新表：`model_profiles`、`model_route_rules`、`model_usage_records`
- 7 个 MCP 工具：`model.profile.upsert/list`、`model.route`、`model.route_rule.upsert/list`、`cost.record_usage/report`
- 支持模型分层：cheap/standard/premium/local
- 支持路由规则 + fallback 降级
- 成本自动估算（基于 profile 的 cost_config）
- 多维度成本统计：day/task_type/model/profile/provider/tier

### 需求背景

用户明确要求：

- 大纲撰写、正文编写、审查的大模型可以灵活配置。
- 默认可以使用当前 API key。
- 审查默认可只用一个模型直接使用。
- 架构必须支持后续多个模型联合审查。
- 需要 token 成本统计和高端模型限流。

### 建议工具

```text
model.profile.upsert
model.profile.list
model.route
cost.record_usage
cost.report
```

### 建议新增迁移

文件建议：

```text
deploy/nas/postgres/init/150_model_cost.sql
```

建议表：

```text
model_profiles
model_route_rules
model_usage_records
model_daily_costs（可选，先用 view/查询聚合也可以）
```

#### model_profiles

字段建议：

```text
id uuid primary key
project_id uuid not null references projects(id) on delete cascade
profile_key text not null
display_name text not null
provider text not null
model_name text not null
task_types text[] not null default array[]::text[]
tier text not null default 'standard' -- cheap/standard/premium/local
default_params jsonb not null default '{}'
cost_config jsonb not null default '{}'
rate_limit_config jsonb not null default '{}'
is_default boolean not null default false
status text not null default 'active'
metadata jsonb not null default '{}'
created_at timestamptz default now()
updated_at timestamptz default now()
unique(project_id, profile_key)
```

不要保存 API key。API key 由本地 skill 或调用端环境变量管理。

#### model_route_rules

字段建议：

```text
id uuid primary key
project_id uuid not null references projects(id) on delete cascade
task_type text not null
profile_key text not null
priority int not null default 100
conditions jsonb not null default '{}'
fallback_profile_keys text[] not null default array[]::text[]
status text not null default 'active'
metadata jsonb not null default '{}'
created_at timestamptz default now()
updated_at timestamptz default now()
unique(project_id, task_type, profile_key)
```

task_type 建议：

```text
outline
detailed_outline
chapter_draft
chapter_segment
polish
review
compliance_review
summary
embedding
rule_extraction
state_extraction
foreshadowing_extraction
```

#### model_usage_records

字段建议：

```text
id uuid primary key
project_id uuid not null references projects(id) on delete cascade
workspace_id uuid references workspaces(id) on delete set null
user_id uuid references users(id) on delete set null
profile_key text
provider text
model_name text
task_type text not null
source_type text -- context_pack/generation/review/vector/sync/manual
source_id text
input_tokens int default 0
output_tokens int default 0
cached_tokens int default 0
total_tokens int default 0
cost_amount numeric(12, 6) default 0
currency text default 'USD'
latency_ms int
success boolean not null default true
error_code text
metadata jsonb not null default '{}'
created_at timestamptz default now()
```

### Service 建议

在 `services.py` 中新增：

```text
ModelCostService
```

方法建议：

```text
upsert_profile(project_id, ...)
list_profiles(project_id, task_type=None, status='active')
route(project_id, task_type, chapter_no=None, volume_no=None, context=None)
record_usage(project_id, username, ...)
cost_report(project_id, group_by='day', task_types=None, from_date=None, to_date=None)
```

### Tool 行为建议

#### model.profile.upsert

用途：创建或更新项目模型档案。

要求：

- write 权限。
- 不接收 API key。
- 可标记 is_default。
- 如果 `is_default=true`，同 project + task_type 的其他默认项应谨慎处理；初版可以只允许 profile 自身有 `task_types`，route 时按 priority/is_default 选。

#### model.profile.list

用途：列出模型档案。

要求：

- read 权限。
- 支持按 task_type/status 过滤。

#### model.route

用途：根据 task_type 和上下文返回推荐模型 profile。

初版逻辑：

1. active route rule 按 priority 匹配 task_type。
2. 找到 active profile。
3. 返回 primary profile 和 fallback profiles。
4. 如果没有 route rule，返回该 task_type 的 default profile。
5. 如果还没有，返回项目第一个 active standard profile。

注意：MCP 只返回配置，不调用模型。

#### cost.record_usage

用途：本地 skill 或 Web 在模型调用后提交 token 与成本记录。

要求：

- write 权限。
- total_tokens 可由 input/output/cached 自动计算。
- cost 可由调用方传，也可以按 profile cost_config 估算。

#### cost.report

用途：统计项目模型成本。

要求：

- read 权限。
- 支持 group_by：day/task_type/model/profile/provider。
- 返回 usage_count、tokens、cost、success/error。

### 冒烟脚本建议

新增：

```text
deploy/nas/scripts/verify-phase2-model-cost-tools.sh
```

验证：

1. 创建 workspace/project。
2. upsert 三个 profile：cheap、standard、premium。
3. list 按 task_type 返回。
4. route outline 返回指定 profile。
5. record_usage 两条记录。
6. cost.report 按 task_type 聚合正确。
7. 清理 workspace。

通过后加入 Phase 2 组合冒烟。

### 文档更新

必须更新：

- `docs/novel-os-mcp/development-plan.md`
- `docs/novel-os-mcp/tool-schema.md`
- `novel-os-mcp/docs/TOOLS.md`
- `docs/novel-os-mcp/handoff-current-state.md`
- `docs/novel-os-mcp/handoff-next-tasks.md`

## Phase 1 剩余：上下文 Profile

状态：TODO/未完全实现。

需求：

- 每个项目/分卷/任务类型可配置 context budget。
- 配置 Canon、状态、伏笔、摘要、规则、审查经验等占比。
- 支持 profile 版本和生效范围。

建议后续表：

```text
context_profiles
```

是否先做：可以在 Phase 2.10 后补，也可以等 Phase 3 Web 需要可视化权重编辑器时再做。

## Phase 3 Web 数据维护台

状态：TODO。

不要一次性重写全部 Web。建议顺序：

1. 项目选择器和当前项目状态。
2. Canon 文档 CRUD 页面。
3. 规则库页面，包含 compliance 规则。
4. 实体/状态维护页面。
5. 伏笔看板。
6. 剧情线/卷/章节计划页面。
7. 审查中心：review jobs、reports、revision tasks、rule proposals。
8. 上下文包预览和 preflight。
9. 同步冲突页面。
10. 模型配置和成本看板。

Web 要求：

- 中英文切换。
- 不以手写 JSON 为主流程。
- 保留调试工具。
- 不负责小说初始化。

## Phase 4 本地 Skill 对接

状态：TODO。

建议顺序：

1. 接入 `sync.import_initial_project_pack`。
2. 接入 `sync.import_local_manifest` 和 `sync.submit_file_hashes`。
3. 接入 `workflow.prepare_chapter_context` 输出本地 context 文件。
4. 接入 `workflow.submit_chapter_commit`。
5. 接入 `review.start_job`、`review.submit_model_report`、`workflow.learn_from_review`。
6. 接入 Phase 2.10 model route 和 cost record。
7. 初始化小说时参考 `lingfengQAQ/webnovel-writer` 的沟通式设定流程，但最终只把结构化设定导入 MCP。

## Phase 5 审查闭环增强

当前已有基础，后续增强：

- 多模型 council 配置 UI。
- 模型权重基于人工复核准确率动态调整。
- 规则提案审批页面。
- 状态/伏笔建议采纳页面。
- Critical 阻断进入下一章的工作流级校验。
- 审查报告本地文件和 MCP 结构化报告双向绑定。

## Phase 6 性能、容灾与运维

建议任务：

- Redis context pack cache。
- 高频实体状态缓存。
- 向量检索结果缓存。
- active/recent/archive/deep_archive 数据生命周期。
- 定时归档完结卷。
- 定时清理过期 vector jobs、废弃草稿 commit、驳回提案。
- 依赖降级：Qdrant 不可用时走 PostgreSQL 文本检索。
- 发布前自动备份和 5 分钟回滚手册。

## Phase 7/P1 创作效率

后续功能：

- Prompt 模板托管。
- 工程包导入导出。
- 批量维护工具。
- 批量预生成细纲。
- 商业节奏看板。
- 读者期待库。
- 专有名词锁定。
- 多版本正文差异对比。
- 协作批注。

## Phase 8/P2 远期

后续功能：

- 增强离线创作模式。
- 分布式 MCP。
- 人物/势力关系图谱。
- 题材模板市场。

## 新窗口开始 Phase 2.10 前的检查清单

- 读取 [HANDOFF.md](./HANDOFF.md)。
- 确认本地 `python -m compileall novel-os-mcp/src` 通过。
- 确认 NAS 最近 Phase 2 冒烟通过。
- 不保存 API key。
- 不改 `/opt/novel-os` 外目录。
- 设计 schema 时考虑多项目隔离。
