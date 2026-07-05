# Novel OS Web Client - Menu Structure

## 3-Level Menu Architecture

```
Section (requiresProject) > Group (collapsible) > Item (navigable)
```

## Current Menu Layout

### Project Section (requiresProject: true on groups)
| Group | Item | Page | Status |
|-------|------|------|--------|
| **管理** | 项目列表 | project-manage | Done |
| | 卷管理 | plot-volumes | Done |
| | 章节管理 | chapters | Done |
| **设定** | 世界规则 | project-world-rules | Done |
| | 角色管理 | project-characters | Done |
| | 势力管理 | project-factions | Done |
| | 世界状态 | project-world-state | Done |
| **创作** | 情节线 | plot-threads | Done |
| | 伏笔管理 | foreshadowing-list | Done |
| | 创作规则 | rules-list | Done |
| **生成** | 流水线 | pipeline | Done |
| | 审核任务 | review-tasks | Done |
| | 上下文预览 | context-preview | Done |
| **分析** | 角色弧光 | arc-characters | Pending |
| | 节奏分析 | pacing-analysis | Pending |

### Knowledge Section (requiresProject: false)
| Group | Item | Page | Status |
|-------|------|------|--------|
| **文档** | 设定文档 | canon-list | Done |
| | 实体管理 | entities-list | Done |
| | 读者期待 | expectations | Pending |
| **知识库** | 项目知识 | kb-pk | Pending |
| | 知识分类 | kb-categories | Pending |
| | 题材策略 | kb-genres | Pending |
| **参考素材** | 素材管理 | materials | Pending |
| **知识搜索** | 自动搜索 | kb-auto-search | Pending |
| | 全文检索 | kb-search | Pending |
| **知识图谱** | 关系图 | kb-graph | Pending |
| | 实体关系 | kb-relations | Pending |
| | 统计 | kb-stats | Pending |
| **知识审核** | 审核列表 | kb-review | Pending |
| | 过期管理 | kb-expiry | Pending |

### System Section (requiresProject: false)
| Group | Item | Page | Status |
|-------|------|------|--------|
| **项目管理** | 工作区管理 | workspace-manage | Pending |
| | 成员管理 | member-manage | Pending |
| **模型配置** | 模型配置 | model-profiles | Done |
| | 路由规则 | model-routes | Pending |
| | 速率限制 | model-rate-limits | Pending |
| **模板管理** | Prompt模板 | template-list | Done |
| **风格控制** | 文风档案 | style-profiles | Pending |
| | 文风分析 | style-analysis | Pending |
| | 文风漂移 | style-drift | Pending |
| **数据管理** | 数据同步 | data-sync | Pending |
| | 同步冲突 | data-conflicts | Pending |
| | 审计日志 | data-audit | Pending |
| | 离线模式 | data-offline | Pending |
| **系统监控** | 缓存管理 | cache-manage | Pending |
| | 备份管理 | backup-manage | Pending |
| **系统信息** | 连接信息 | sys-connection | Pending |
| | 账户管理 | sys-account | Pending |
| | 用户管理 | sys-users | Pending |
| | 调试信息 | sys-debug | Pending |
| **高级功能** | 知识初始化 | kb-init | Pending |
| | 世界观快照 | world-snapshot | Pending |
| | 弧光追踪 | arc-tracking | Pending |

## Menu State Persistence

- Expanded sections: stored in `localStorage` as `menu-expanded-sections`
- Expanded groups: stored in `localStorage` as `menu-expanded-groups`
- Favorites: stored in `localStorage` as `menu-favorites`

## i18n Keys Structure

```json
{
  "menu": {
    "sections": {
      "project": "Project",
      "knowledge": "Knowledge",
      "system": "System"
    },
    "groups": {
      "management": "Management",
      "settings": "Settings",
      "creation": "Creation",
      ...
    },
    "items": {
      "project-list": "Project List",
      "volume-manage": "Volume Management",
      ...
    }
  }
}
```
