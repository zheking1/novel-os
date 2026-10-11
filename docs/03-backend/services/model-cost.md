# Model Cost 服务 — 模型成本管理

**源码**: `novel-os-mcp/src/novel_os_mcp/services/model_cost.py` (551 行)

## 概述

Model Cost 服务管理 AI 模型调用成本的完整生命周期：使用记录、成本核算、预算告警、成本预测、模型配置管理和路由规则。

## 数据库表

| 表名 | 说明 |
|------|------|
| `model_usage_records` | 模型使用记录 |
| `model_profiles` | 模型配置档案 |
| `model_route_rules` | 模型路由规则 |
| `budget_alerts` | 预算告警设置 |

---

## 一、使用记录 (Usage Recording)

### record_usage

记录每次 API 调用:

| 字段 | 说明 |
|------|------|
| `model_name` | 模型名称 |
| `task_type` | 操作类型 |
| `input_tokens` | 输入 token 数 |
| `output_tokens` | 输出 token 数 |
| `cost_amount` | 费用 (USD, 可选) |
| `source_id` | 关联章节 ID |
| `metadata` | JSONB 扩展元数据 |

---

## 二、使用统计

### get_usage_summary

聚合统计 (最近 N 天):

**返回值**:
- `total_requests`: 总请求数
- `total_input_tokens` / `total_output_tokens`: token 总量
- `total_cost_usd`: 总费用
- `avg_cost_per_request`: 平均单次费用
- `avg_input_tokens` / `avg_output_tokens`: 平均 token 数

### get_usage_by_model

按模型分组统计: `model_name → {requests, input_tokens, output_tokens, total_cost_usd, avg_cost}`

### get_daily_usage

按天分组统计: `DATE(created_at) → {requests, input_tokens, output_tokens, total_cost_usd}`

---

## 三、预算告警 (Budget Alerts)

### set_budget_alert

设置预算告警:

| 参数 | 说明 |
|------|------|
| `alert_type` | 告警类型 |
| `threshold_usd` | 费用阈值 |
| `notification_method` | 通知方式 (`"log"` 等) |

`ON CONFLICT (project_id, alert_type)` 覆盖更新。

### check_budget_alerts

检查是否触发告警:

1. `get_usage_summary(days=30)` 获取近 30 天总费用
2. 对比各告警 `threshold_usd`
3. 返回触发的告警列表，含 `current_cost`

---

## 四、成本预测 (Cost Forecasting)

### get_cost_forecast

基于历史数据预测未来 N 天成本:

1. `get_daily_usage(days=30)` 获取近 30 天数据
2. 计算日均费用: `total_cost / days_with_data`
3. 预测: `daily_avg * forecast_days`

**返回值**: `{forecast_cost, daily_average, forecast_days, based_on_days}`

---

## 五、成本报告 (Cost Reporting)

### cost_report

生成聚合成本报告:

**分组维度** (`group_by`):
- `"day"` → `DATE(created_at)`
- `"week"` → `DATE_TRUNC('week', created_at)`
- `"month"` → `DATE_TRUNC('month', created_at)`

**过滤条件**: `from_date`/`to_date`, `task_types`, `profile_keys`

**返回值**: `{total_cost_usd, total_requests, total_input_tokens, total_output_tokens, groups: [...], stats: {...}}`

---

## 六、模型配置管理 (Model Profiles)

### 模型配置属性

| 字段 | 类型 | 说明 |
|------|------|------|
| `profile_key` | str | 配置键 |
| `display_name` | str | 显示名称 |
| `provider` | str | 提供方 (e.g., `baidubce`) |
| `model_name` | str | 模型名 (e.g., `deepseek-v4-flash`) |
| `task_types` | list[str] | 支持的任务类型: `review`, `generation`, `analysis`, `planning`, `polishing` 等 |
| `tier` | str | 价格等级: `standard`, `premium`, `budget` |
| `default_params` | dict | JSONB 默认参数 (api_url, api_key, model_name, temperature, max_tokens 等) |
| `cost_config` | dict | JSONB 成本配置 (input_per_1k, output_per_1k) |
| `rate_limit_config` | dict | JSONB 限流配置 (rpm, tpm, max_concurrent) |
| `is_default` | bool | 是否为默认配置 |
| `status` | str | `active` / `inactive` |
| `is_contributed` | bool | 是否为社区贡献配置 |

### upsert_profile

创建/更新模型配置（`ON CONFLICT (user_id, profile_key)`）。

**新建要求**: `display_name`, `provider`, `model_name` 必填。

**更新策略**: 传入 `None` 的字段保留旧值（merge 策略）。

### list_profiles / list_profiles_by_user

- `list_profiles`: 项目级模型配置列表
- `list_profiles_by_user`: 用户级 (跨项目) 模型配置列表

支持按 `task_type`、`tier`、`status` 过滤。排序: `is_default DESC, tier, display_name`。

---

## 七、模型路由 (Model Routing)

### route_model

根据 `task_type` 路由到最佳模型配置:

**优先级**:
1. 查找 `model_route_rules` (按 `priority DESC`)
2. 回退到默认 profile (匹配 `task_type`, 按 `is_default DESC, tier`)
3. 无匹配 → 返回 error

### upsert_route_rule

创建/更新路由规则:

| 字段 | 说明 |
|------|------|
| `task_type` | 任务类型 |
| `profile_key` | 目标模型配置 |
| `priority` | 优先级 (数字越大越高) |
| `conditions` | JSONB 条件 (e.g., `{"volume_no": > 10}`) |
| `fallback_profile_keys` | 回退配置键列表 |
| `status` | `active` / `inactive` |

`ON CONFLICT (project_id, task_type, profile_key)` 覆盖更新。

### list_route_rules

列出路由规则，JOIN `model_profiles` 获取配置详情。

---

## 工作流引导

1. 配置模型 → `model.profile.upsert(profile_key, provider, model_name, task_types, cost_config)`
2. 设置路由 → `model.route.upsert(task_type, profile_key, priority)`
3. 每次调用 → `record_usage()` 记录
4. 成本监控 → `get_usage_summary()` / `cost_report()` / `get_cost_forecast()`
5. 预算告警 → `set_budget_alert()` + `check_budget_alerts()`
6. 模型选择 → `route_model(task_type)` 自动路由