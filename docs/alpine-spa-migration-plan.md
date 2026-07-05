# Novel OS Web Client — Alpine.js SPA 完整迁移方案

> 版本：v1.0 | 日期：2026-07-04 | 供后续 AI 模型继续开发

---

## 一、当前项目状态

### 1.1 两套前端并存

| 入口 | 路径 | 大小 | 技术 | 状态 |
|------|------|------|------|------|
| 旧版 | `http://IP:8790/` | 384KB | 原生JS | 🟡 功能完整但不维护 |
| 新版 | `http://IP:8790/spa` | 7.6KB | Alpine.js | 🟢 **主力开发** |

### 1.2 文件结构

```
novel-os-web/
├── server.py                 # Python HTTP (含 /spa 路由)
├── Dockerfile                # COPY spa.html + js/ + css/
├── index.html                # 旧版 (384KB, 不再修改)
├── spa.html                  # 🟢 新版SPA入口 (7.6KB)
├── css/style.css             # 31KB 样式
├── js/
│   ├── alpine.min.js         # Alpine.js 3.14 (44KB)
│   ├── app.js                # 工具: $, api, escapeHtml, showToast, setStatus
│   ├── auth.js               # loadWorkspaces, loadProjects
│   ├── spa.js                # 🟢 Alpine store + 路由 + i18n
│   ├── components/
│   │   └── item-level.js     # 🟢 Alpine组件: 物品等级管理
│   └── pages/
│       ├── genre.js, category.js, binding.js  # 🟡 旧JS (可被Alpine替代)
│       ├── canon.js, entities.js, rules.js, plot.js, review.js, init.js
│       ├── system.js, knowledge.js
│       └── ...
```

### 1.3 已完成功能

- ✅ Docker部署（Dockerfile 已包含 spa.html）
- ✅ CSS 外部化
- ✅ 外部 JS 模块化（14个模块）
- ✅ Alpine.js SPA 框架搭建
- ✅ 工作区/项目选择器（Alpine store）
- ✅ 中英双语 i18n（内置在 spa.js）
- ✅ 物品等级管理页面（Alpine组件，完整CRUD）
- ✅ 10页菜单骨架（World组8页 + Management组2页）
- ✅ Toast通知系统
- ✅ 数据库已扩展（genre_category_bindings等）

---

## 二、SPA 架构

### 2.1 核心文件

| 文件 | 作用 | 可修改 |
|------|------|--------|
| `spa.html` | HTML模板 + Alpine绑定 | ✅ |
| `js/spa.js` | Alpine store、路由、i18n | ✅ |
| `js/components/*.js` | 各页面Alpine组件 | ✅ 新建 |
| `js/alpine.min.js` | Alpine框架 | ❌ 不可改 |
| `js/app.js` | 工具函数 | ❌ 不可改 |
| `server.py` | 后端路由 | ⚠️ 谨慎改 |

### 2.2 路由系统

```
spa.js 中的 Alpine.data('app') 管理路由:

currentPage: 'item-level'  ← 当前页面
menu: [{ label, items: [{id, icon, title}] }]  ← 菜单结构

导航: @click="navigate('page-id')"
显示: x-show="currentPage === 'page-id'"
```

### 2.3 i18n 系统

```javascript
// spa.js 中的 i18n 数据
i18n: {
  en: { itemLevel: { title: 'Item Levels', ... } },
  zh: { itemLevel: { title: '物品等级管理', ... } }
}

// 使用方式
t('itemLevel.title')     // 返回当前语言文本
// HTML: <span x-text="t('itemLevel.title')"></span>

// 切换语言
@click="toggleLang()"   // en ↔ zh
```

### 2.4 全局 API

```javascript
// 所有工具可通过 window 访问
window.api('/api/tool', { tool, arguments })  // MCP工具调用
window.$('id')                               // DOM查询
window.escapeHtml(str)                       // 转义
window.showToast(type, title, msg)           // 通知
window.setStatus(text)                       // 状态栏
```

---

## 三、添加新页面 - 标准模板

### 3.1 步骤一：创建 Alpine 组件 `js/components/xxx.js`

```javascript
document.addEventListener('alpine:init', () => {
  Alpine.data('xxxManager', () => ({
    items: [],           // 数据列表
    editing: null,       // 编辑状态 (null=列表, idx=编辑)
    form: {},            // 表单数据
    status: '',          // 状态提示

    async init() { await this.load(); },

    async load() {
      this.status = 'Loading...';
      try {
        const ws = document.querySelector('[x-data]').__x.getUnobservedData().workspace || 'default';
        // 1. 如果需要UUID，先解析slug
        const cat = await window.api('/api/tool', {
          tool: 'setting.category.get',
          arguments: { workspace: ws, slug: 'your-category-slug' }
        });
        const catId = cat?.id || cat?.result?.id;
        
        // 2. 加载数据
        const r = await window.api('/api/tool', {
          tool: 'setting.item.list',
          arguments: { workspace: ws, category_id: catId }
        });
        this.items = (r.ok && r.result) ? r.result : [];
        this.status = '';
      } catch (e) { this.status = 'Error: ' + e.message; }
    },

    add() { this.editing = -1; this.form = {}; },
    edit(idx) { this.editing = idx; this.form = { ...this.items[idx] }; },
    cancel() { this.editing = null; },

    async save() {/* API调用 */},
    async remove(idx) {/* API调用 */}
  }));
});
```

### 3.2 步骤二：在 spa.html 中添加页面容器

```html
<div x-show="currentPage === 'xxx'" x-data="xxxManager" x-init="$nextTick(() => $data.init())">
  <div class="flex justify-between items-center mb-4">
    <h2 class="text-xl font-bold" x-text="t('xxx.title')"></h2>
    <button class="bg-blue-500 text-white px-4 py-1.5 rounded text-sm" @click="add()">
      + New
    </button>
  </div>
  
  <div class="space-y-2">
    <template x-for="(item, idx) in items" :key="item.id">
      <div class="bg-white border rounded p-3 flex justify-between items-center shadow-sm">
        <div>
          <span class="font-medium" x-text="item.core_summary"></span>
        </div>
        <div class="flex gap-2">
          <button class="text-blue-500 text-sm" @click="edit(idx)">Edit</button>
          <button class="text-red-500 text-sm" @click="remove(idx)">Delete</button>
        </div>
      </div>
    </template>
  </div>

  <!-- Modal (参考 item-level.js 的弹窗模式) -->
  <div x-show="editing !== null" class="fixed inset-0 bg-black/30 z-50 flex items-start justify-center pt-20" @click.self="cancel()">
    <div class="bg-white max-w-md w-full mx-4 p-6 rounded-lg shadow-xl">
      <!-- 表单 -->
      <div class="flex gap-2 mt-4">
        <button class="bg-blue-500 text-white px-4 py-1.5 rounded text-sm" @click="save()">Save</button>
        <button class="border px-4 py-1.5 rounded text-sm" @click="cancel()">Cancel</button>
      </div>
    </div>
  </div>
</div>
```

### 3.3 步骤三：在 spa.html `<head>` 添加组件引用

```html
<script src="js/components/xxx.js"></script>
```

### 3.4 步骤四：在 spa.js 添加菜单项和 i18n

**spa.js menu:**
```javascript
{ id: 'xxx', icon: '🆕', title: 'New Page' }
```

**spa.js i18n:**
```javascript
xx: { title: 'New Page' }
```

### 3.5 步骤五：Dockerfile 不需要改

```
COPY js/ /app/js/   ← 已包含所有 js/components/ 子目录
```

### 3.6 步骤六：部署测试

```bash
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web
curl http://127.0.0.1:8790/spa  # 验证200
```

---

## 四、MCP API 参考

### 4.1 setting.category 系列

| 工具 | 参数 | 用途 |
|------|------|------|
| `setting.category.list` | `workspace`, `is_active` | 列出分类 |
| `setting.category.get` | `workspace`, `slug` | 按slug查UUID |
| `setting.category.upsert` | `workspace`, `slug`, `name`, `metadata` | 创建/更新分类 |

### 4.2 setting.item 系列

| 工具 | 参数 | 用途 |
|------|------|------|
| `setting.item.list` | `workspace`, `category_id` (UUID!) | 列出条目 |
| `setting.item.upsert` | `workspace`, `category_id`, `core_summary`, `detailed_expansion`, `sort_order`, `data`(JSONB) | 创建/更新条目 |
| `setting.item.delete` | `workspace`, `item_id` | 删除条目 |

### 4.3 注意：category_id 必须是 UUID

```javascript
// ❌ 错误 - 传 slug
{ category_id: 'item-level' }

// ✅ 正确 - 先查UUID再用
const cat = await api('/api/tool', { tool: 'setting.category.get', arguments: { workspace: ws, slug: 'item-level' } });
const catId = cat?.id || cat?.result?.id;
```

### 4.4 genre/setting 系列 (Phase 3 新增的)

| 工具 | 用途 |
|------|------|
| `setting.genre.upsert/delete/list` | 小说类型管理 |
| `genre.binding.bulk_upsert/matrix` | 类型-分类绑定矩阵 |

---

## 五、Alpine组件间通信

### 5.1 获取全局app store

```javascript
// 在任何Alpine组件中获取app级别数据
const app = document.querySelector('[x-data]').__x.getUnobservedData();
console.log(app.workspace);  // 当前工作区
console.log(app.project);    // 当前项目
console.log(app.t('key'));   // 国际化
```

### 5.2 跨组件通知

```javascript
window.showToast('success', 'Saved');  // Toast通知
window.setStatus('Ready');             // 状态栏更新
```

---

## 六、计划添加的页面清单

| 优先级 | 页面 | slug | 数据库分类 | 组件文件 |
|--------|------|------|-----------|----------|
| **P0** | Genre Manager | genre-manage | genre_canonical | genre.js (已有,待Alpine化) |
| **P0** | Category Manager | category-manage | setting_categories | 新建 |
| **P0** | Genre-Category Binding | binding | genre_category_bindings | 新建 |
| **P1** | Character Levels | character-level | character-level | 新建 |
| **P1** | Skill Levels | skill-level | skill-level | 新建 |
| **P1** | Tech Levels | tech-level | tech-level | 新建 |
| **P1** | Item Catalog | item-catalog | item-catalog | 新建 |
| **P1** | Skill Catalog | skill-catalog | skill-catalog | 新建 |
| **P2** | Locations | location-map | location-map | 新建 |
| **P2** | Bestiary | creature-bestiary | creature-bestiary | 新建 |

### 已预设的数据库分类（slug）

- `item-level` - 物品等级
- `character-level` - 人物等级
- `skill-level` - 技能等级
- `tech-level` - 科技等级
- `building-level` - 建筑等级
- `power-system` - 力量体系
- `item-catalog` - 物品图鉴
- `skill-catalog` - 技能图鉴
- `location-map` - 地图地点
- `creature-bestiary` - 生物图鉴

---

## 七、部署命令速查

```bash
# NAS连接
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST}

# 同步本地文件到NAS
pscp -pw "${NAS_SSH_PASSWORD}" local_file root@${NAS_HOST}:/opt/novel-os/novel-os-web/

# 重建容器
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web

# 验证
curl http://127.0.0.1:8790/health    # 检查服务
curl http://127.0.0.1:8790/spa       # 检查SPA

# 查看日志
docker logs novel-os-web --tail 20

# 查看容器内文件
docker exec novel-os-web ls /app/js/components/

# Git (本地执行)
git add -A ':!temp-webnovel/'
git commit -m "描述"
git push origin main
```

---

## 八、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| SPA 404 | Dockerfile未COPY spa.html | 已修复 |
| API报UUID错误 | category_id传了slug | 先用 `setting.category.get` 查UUID |
| 容器反复重启 | server.py语法错误 | `docker logs` 查看错误行 |
| `$不是函数` | app.js的`$`在IIFE内 | 用 `window.$` 或确保 app.js 先加载 |
| i18n不生效 | `window.i18nData`为空 | 直接用spa.js内置i18n |

---

## 九、下一步建议

1. **P0优先**：完成 Genre/Category/Binding 三个管理页的 Alpine 版本
2. **P1**：四个等级管理页（复用item-level组件模式）
3. **P2**：物品/技能图鉴、地图
4. **最后**：当SPA功能完整后，把 `spa.html` 设为默认入口

---

*文档版本：v1.0 | 供后续AI模型继续开发*