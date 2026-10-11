# ApiClient — API 客户端

> 文件: `novel-os-web/js/core/api-client.js` (424行)

## 基础配置

```javascript
ApiClient.config = {
  baseUrl: '/api',          // 所有端点自动加上此前缀
  timeout: 30000,           // 30 秒
  retries: 3,
  retryDelay: 1000
}
```

## 核心方法

### `request(method, endpoint, data, options)`

**关键**: 第一个参数是 `method`，不是 `endpoint`。**禁止** 调用 `request(endpoint, options)`。

```javascript
// 正确 ✅
ApiClient.request('POST', '/tool', { tool: 'x', arguments: {} }, { showLoading: false })

// 错误 ❌
ApiClient.request('/tool', options)
```

参数:
| 参数 | 类型 | 说明 |
|---|---|---|
| `method` | string | `'GET'` / `'POST'` / `'PUT'` / `'DELETE'` |
| `endpoint` | string | 相对路径（不含 `/api` 前缀，会自动加上） |
| `data` | object | POST/PUT body（自动 JSON.stringify） |
| `options` | object | 见下 |

options 参数:
| 键 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `showLoading` | boolean | `true` | 是否显示全局 loading |
| `showError` | boolean | `true` | 是否弹 toast 错误 |
| `cache` | boolean | `false` | 是否缓存（基本不用，CacheManager 接管了） |
| `cacheKey` | string | `null` | 缓存键 |
| `cacheDuration` | number | `300000` | 缓存有效期 ms |
| `retry` | boolean | `true` | 是否自动重试 |

### `callTool(toolName, args, options)`

**所有业务功能的主入口。** 没有 REST API，全部通过 MCP 工具调用。

```javascript
// 示例
const workspaces = await ApiClient.callTool('workspace.list', {})
const result = await ApiClient.callTool('kb.uk.create', { workspace, topic: '...' })
const data = await ApiClient.callTool('prompt.template.list', { workspace, project })
```

内部流程:
1. 检查 `options.skipCache` 或 `args._skip_cache`
2. 只读操作（含 `list|get|search|whoami|health|stats|tree`）自动走 CacheManager
3. 写操作（含 `create|update|delete|upsert|record|fulfill`）自动按前缀失效缓存
4. `POST /api/tool` → `{ tool, arguments }` → 服务器代理到 MCP

## 自动项目注入

部分命名空间方法会自动注入当前项目：

```javascript
promptTemplate: {
  async list(workspace, filters, options) {
    const project = window.AppState?.currentProject;  // ← 自动
    return ApiClient.callTool('prompt.template.list', { workspace, project, ...filters }, options);
  }
}
```

这意味着页面无需手动传递 project 参数。

## 401 处理

```javascript
if (response.status === 401) {
  localStorage.removeItem('novel-workspace');
  localStorage.removeItem('novel-project');
  window.location.reload();  // 整页刷新回到登录
}
```

## 完整命名空间方法

### `ApiClient.workspace`
| 方法 | MCP 工具 | 参数 |
|---|---|---|
| `list(options)` | `workspace.list` | — |

### `ApiClient.project`
| 方法 | MCP 工具 | 参数 |
|---|---|---|
| `list(workspace, options)` | `project.list` | `{workspace}` |

### `ApiClient.setting`
| 方法 | MCP 工具 | 参数 |
|---|---|---|
| `list(workspace, options)` | `setting.category.list` | `{workspace}` |
| `get(workspace, slug, options)` | `setting.category.get` | `{workspace, slug}` |
| `upsert(workspace, data, options)` | `setting.category.upsert` | `{workspace, ...data}` |
| `delete(workspace, categoryId, options)` | `setting.category.delete` | `{workspace, category_id}` |

### `ApiClient.item`
| 方法 | MCP 工具 | 参数 |
|---|---|---|
| `list(workspace, categoryId, options)` | `setting.item.list` | `{workspace, category_id}` |
| `upsert(workspace, data, options)` | `setting.item.upsert` | `{workspace, ...data}` |
| `delete(workspace, itemId, options)` | `setting.item.delete` | `{workspace, item_id}` |

### `ApiClient.genre`
| 方法 | MCP 工具 | 参数 |
|---|---|---|
| `list(options)` | `setting.genre.list` | — |
| `upsert(data, options)` | `setting.genre.upsert` | `data` |
| `delete(slug, options)` | `setting.genre.delete` | `{slug}` |

### `ApiClient.promptTemplate`
| 方法 | MCP 工具 | 自动注入 |
|---|---|---|
| `list(workspace, filters, options)` | `prompt.template.list` | `project` |
| `get(workspace, templateKey, options)` | `prompt.template.get` | `project` |
| `create(workspace, data, options)` | `prompt.template.upsert` | `project` |
| `update(workspace, templateKey, data, options)` | `prompt.template.upsert` | `project` |
| `delete(workspace, templateKey, options)` | `prompt.template.delete` | `project` |

### `ApiClient.modelProfile`
| 方法 | MCP 工具 | 说明 |
|---|---|---|
| `list(workspace, options)` | `model.profile.list` | 不传 workspace 到 tool |
| `get(workspace, profileKey, options)` | `model.profile.list` | 带 `profile_key` 过滤 |
| `create(workspace, data, options)` | `model.profile.upsert` | — |
| `update(workspace, profileKey, data, options)` | `model.profile.upsert` | 带 `profile_key` |
| `delete(workspace, profileKey, options)` | `model.profile.upsert` | 设 `status: 'inactive'` |

### `ApiClient.localChapter`
| 方法 | MCP 工具 | 自动注入 |
|---|---|---|
| `list(project, options)` | `local.chapter.list` | `workspace` |
| `get(project, chapterNo, options)` | `local.chapter.get` | `workspace` |
| `read(project, chapterNo, options)` | `local.chapter.get` + `read` | `workspace` |
| `write(project, chapterNo, content, options)` | `local.chapter.write` | `workspace` |

## 缓存失效规则

```javascript
// callTool 内部自动处理
const WRITE_OPS = ['create', 'update', 'delete', 'upsert', 'record', 'fulfill'];
const READ_ONLY = ['list', 'get', 'search', 'whoami', 'health', 'stats', 'tree'];
```

当工具名匹配写操作关键字时，自动调用 `CacheManager.invalidatePrefix(prefix)` 清除该前缀的所有缓存。例如 `prompt.template.create` 会清除所有 `prompt.*` 缓存。