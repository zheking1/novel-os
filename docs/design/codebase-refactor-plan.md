# Novel OS 代码库重构方案

> 审计日期：2026-07-02
> 目标：拆分 services.py（8200 行/17 类）和 main.py（6100 行/288 工具）

---

## 一、现状

### 1.1 services.py

| 类 | 行数 | 依赖 |
|---|------|------|
| WorkspaceService | 419 | db |
| CanonService | 520 | db |
| RulesService | 812 | db |
| ComplianceService | 298 | db, RulesService |
| PlotService | 689 | db |
| MemoryService | 925 | db, EmbeddingService, VectorIndex |
| **ContextService** | **1031** | db, MemoryService, RulesService, PlotService |
| ReferenceService | 85 | db |
| ReviewService | 581 | db |
| RuleProposalService | 159 | db |
| ReviewModelMetricsService | 156 | db |
| WorkflowService | 322 | db |
| SyncService | 507 | db, WorkspaceService, CanonService, RulesService, MemoryService, PlotService |
| ModelCostService | 509 | db |
| VectorIndexService | 415 | db, VectorIndex |
| ArchiveService | 390 | db |
| BackupService | 355 | db |

**依赖图：**
```
WorkspaceService ─┐
CanonService ─────┤
RulesService ─────┼──→ ComplianceService
                  │
                  ├──→ ContextService ←── MemoryService + PlotService
                  │
                  └──→ SyncService ←── WorkspaceService + CanonService + MemoryService + PlotService
```

14 个类是叶子节点（无同类依赖），只有 3 个类有跨类依赖。

### 1.2 main.py

| 工具前缀 | 数量 | 使用的服务 |
|---------|------|-----------|
| kb | 33 | kb_service |
| knowledge | 24 | knowledge_service |
| setting | 14 | global_settings_service |
| context | 12 | context_service |
| review | 12 | review_service |
| arc | 11 | character_arc_service |
| pacing | 11 | pacing_service |
| rules | 9 | rules_service |
| archive | 9 | archive_service |
| workflow | 8 | context_service, workflow_service |
| state | 8 | memory_service |
| plot | 8 | plot_service |
| memory | 8 | memory_service |
| causality | 8 | causality_service |
| style | 8 | style_fingerprint_service |
| pipeline | 7 | multipass_service |
| canon | 6 | canon_service |
| sync | 6 | sync_service |
| vector | 6 | vector_index_service |
| novelty | 5 | novelty_service |
| project | 5 | workspace_service |
| model | 5 | model_cost_service |
| cache | 5 | cache_service |
| system | 4 | health_service, degradation_service |
| prompt | 4 | prompt_template_service |
| foreshadowing | 4 | plot_service |
| auth | 4 | workspace_service |
| backup | 4 | backup_service |
| material | 4 | reference_material_service |
| 其余 14 组 | ≤3 | 各自服务 |

**共 288 个 tool，43 个前缀组。**

---

## 二、services.py 拆分方案

### 2.1 文件结构

```
novel_os_mcp/
├── services/
│   ├── __init__.py          # 导出所有类（向后兼容）
│   ├── workspace.py         # WorkspaceService
│   ├── canon.py             # CanonService
│   ├── rules.py             # RulesService
│   ├── compliance.py        # ComplianceService
│   ├── plot.py              # PlotService
│   ├── memory.py            # MemoryService
│   ├── context.py           # ContextService
│   ├── reference.py         # ReferenceService
│   ├── review.py            # ReviewService + RuleProposalService + ReviewModelMetricsService
│   ├── workflow.py          # WorkflowService
│   ├── sync.py              # SyncService
│   ├── model_cost.py        # ModelCostService
│   ├── vector_index.py      # VectorIndexService
│   ├── archive.py           # ArchiveService
│   └── backup.py            # BackupService
```

### 2.2 拆分规则

1. **每个类一个文件**，文件名用 snake_case 类名去掉 `Service` 后缀
2. **ReviewService 族**（ReviewService + RuleProposalService + ReviewModelMetricsService）合并到 `review.py`，因为它们紧密耦合
3. **`__init__.py`** 重新导出所有类，`from .services import ContextService` 仍然有效
4. **无循环依赖**：当前依赖图是 DAG，拆分后仍然是
5. **`ensure_json_value`** 已在 `utils.py`，各模块从 `utils` 导入

### 2.3 `__init__.py` 模板

```python
from .workspace import WorkspaceService
from .canon import CanonService
from .rules import RulesService
from .compliance import ComplianceService
from .plot import PlotService
from .memory import MemoryService
from .context import ContextService
from .reference import ReferenceService
from .review import ReviewService, RuleProposalService, ReviewModelMetricsService
from .workflow import WorkflowService
from .sync import SyncService
from .model_cost import ModelCostService
from .vector_index import VectorIndexService
from .archive import ArchiveService
from .backup import BackupService

__all__ = [
    "WorkspaceService", "CanonService", "RulesService", "ComplianceService",
    "PlotService", "MemoryService", "ContextService", "ReferenceService",
    "ReviewService", "RuleProposalService", "ReviewModelMetricsService",
    "WorkflowService", "SyncService", "ModelCostService", "VectorIndexService",
    "ArchiveService", "BackupService",
]
```

### 2.4 main.py 影响

当前 `main.py` 第 31 行：
```python
from .services import (
    WorkspaceService, CanonService, RulesService, ...
)
```

拆分后改为：
```python
from .services import (
    WorkspaceService, CanonService, RulesService, ...
)
```

**无需修改 main.py 的导入**，因为 `services/__init__.py` 重新导出所有类。

---

## 三、main.py 拆分方案

### 3.1 文件结构

```
novel_os_mcp/
├── main.py                    # 入口：启动 MCP server，注册所有 tool 模块
├── tools/
│   ├── __init__.py
│   ├── admin.py               # admin.*
│   ├── auth.py                # auth.*, workspace.*, user.*, project.*
│   ├── canon.py               # canon.*, rules.*, compliance.*
│   ├── plot.py                # plot.*, foreshadowing.*, volume.*
│   ├── memory.py              # memory.*, state.*
│   ├── context.py             # context.*, workflow.*
│   ├── review.py              # review.*
│   ├── kb.py                  # kb.*, knowledge.*
│   ├── graph.py               # graph.*
│   ├── setting.py             # setting.*
│   ├── model.py               # model.*, cost.*
│   ├── vector.py              # vector.*, embedding.*, rag.*
│   ├── system.py              # system.*, cache.*, backup.*, restore.*
│   ├── prompt.py              # prompt.*, context.weight.*, material.*, expectation.*, annotation.*, noun.*, search.*
│   ├── novel_gen.py           # arc.*, pacing.*, causality.*, style.*, novelty.*, pipeline.*
│   ├── archive.py             # archive.*
│   ├── sync.py                # sync.*
│   └── reference.py           # reference.*
```

### 3.2 合并策略

43 个前缀组合并为 18 个文件，按功能域聚合：

| 新文件 | 合并的前缀 | 工具数 |
|--------|-----------|--------|
| auth.py | auth + workspace + user + project | 14 |
| canon.py | canon + rules + compliance | 18 |
| plot.py | plot + foreshadowing + volume | 14 |
| memory.py | memory + state | 16 |
| context.py | context + workflow | ~20 |
| kb.py | kb + knowledge | 57 |
| setting.py | setting | 14 |
| novel_gen.py | arc + pacing + causality + style + novelty + pipeline | 50 |
| system.py | system + cache + backup + restore | ~14 |
| prompt.py | prompt + material + expectation + annotation + noun + search + context.weight | ~20 |
| 其余 | 各自独立 | ≤9 each |

### 3.3 每个 tools/*.py 的结构

```python
# tools/canon.py
from .. import mcp, db, auth
from ..services import CanonService, RulesService, ComplianceService

@mcp.tool(name="canon.doc.upsert")
async def canon_doc_upsert(workspace: str, project: str, ...):
    ...

@mcp.tool(name="canon.doc.list")
async def canon_doc_list(workspace: str, project: str, ...):
    ...
```

### 3.4 main.py 精简后

```python
# main.py — 只负责启动和注册
import logging
from .db import Database
from .mcp import mcp

logger = logging.getLogger("novel_os_mcp")

db = Database(...)

# Import all tool modules to register them
from .tools import admin, auth, canon, plot, memory, context
from .tools import review, kb, graph, setting, model, vector
from .tools import system, prompt, novel_gen, archive, sync, reference

if __name__ == "__main__":
    mcp.run()
```

### 3.5 服务实例化

服务实例在 `main.py` 顶层创建（保持现状），通过模块级变量传递。各 `tools/*.py` 从 `main` 导入：

```python
# tools/canon.py
from ..main import canon_service, rules_service, compliance_service
```

或者更好的方式：用一个 `deps.py` 集中管理依赖注入。

```python
# deps.py
class Services:
    db: Database
    canon: CanonService
    rules: RulesService
    ...

services = Services()
```

---

## 四、执行计划

### Phase 1：services.py 拆分（低风险）

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1.1 | 创建 `services/` 目录 | ls 确认 |
| 1.2 | 按类逐个提取到独立文件 | 每个文件 Python 语法检查 |
| 1.3 | 创建 `services/__init__.py` 重新导出 | `python -c "from services import *"` |
| 1.4 | 删除旧 `services.py` | 确认无残留引用 |
| 1.5 | 同步部署验证 | docker build + 启动 |

**预计改动：** 1 个文件拆为 16 个文件，main.py 导入路径不变。

### Phase 2：main.py 拆分（中风险）

| 步骤 | 操作 | 验证 |
|------|------|------|
| 2.1 | 创建 `tools/` 目录 | ls 确认 |
| 2.2 | 创建 `deps.py` 依赖注入 | 服务实例集中管理 |
| 2.3 | 按前缀组逐个提取到 tools/*.py | 每个文件语法检查 |
| 2.4 | 精简 main.py 为入口 | MCP server 启动正常 |
| 2.5 | 同步部署验证 | 所有工具可调用 |

**预计改动：** 1 个文件拆为 19 个文件，需改导入路径。

### Phase 3：tool 描述优化（无风险）

为每个 tool 补充 2-3 句描述。不改逻辑，只改 docstring。

---

## 五、风险评估

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 循环导入 | 低 | 高 | 依赖图是 DAG，无环 |
| MCP tool 注册遗漏 | 中 | 中 | 逐模块提取，每步验证 tool 数量 |
| 服务实例化顺序 | 低 | 高 | deps.py 集中管理，显式初始化 |
| 导入路径错误 | 中 | 中 | __init__.py 重新导出保持兼容 |
| Docker 缓存命中不更新 | 低 | 低 | sync_mcp.py 已强制 COPY src |

---

## 六、不做的事

- **不改 tool 名称**：288 个 tool 名保持不变，避免 breaking change
- **不改服务接口**：所有 Service 类的方法签名不变
- **不改数据库 schema**：纯代码重构
- **不加新功能**：本次只做结构优化
