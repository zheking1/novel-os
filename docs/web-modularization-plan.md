# Novel OS Web 客户端渐进式模块化实施方案

> 版本：v2.0 | 日期：2026-07-04

---

## 一、核心原则

### 铁律

1. **不改动原有 JS 逻辑** — 只提取，不重写
2. **每步独立可测** — 每一步完成后页面都能正常运行
3. **先提取后修改** — 先模块化稳定，再增删功能
4. **Git 保护** — 每步 commit，出错可回滚

### 最终目录结构

```
novel-os-web/
├── server.py                 # 后端（仅新增静态文件路由）
├── index.html                # 精简后的 HTML 骨架（~20KB）
├── css/
│   └── style.css             # 从 index.html 提取的 CSS
├── js/
│   ├── api.js                # API 调用封装
│   ├── app.js                # 全局状态、路由、UI 工具
│   ├── auth.js               # 认证、登录、工作区加载
│   └── pages/                # 各页面独立的 JS 模块
│       ├── canon.js           # Canon Docs
│       ├── entities.js        # Entities 管理
│       ├── rules.js           # Writing Rules
│       ├── plot.js            # 情节线、伏笔
│       ├── knowledge.js       # 知识库、UK 管理
│       ├── template.js        # 模板管理
│       ├── genre.js           # 【新增】小说类型管理
│       ├── category.js        # 【新增】分类管理
│       ├── binding.js         # 【新增】类型-分类绑定
│       └── system.js          # 系统管理、健康检查
├── Dockerfile
└── index.html.backup         # 原始备份（只读，不动）
```

### 脚本加载顺序

index.html 中 `<script>` 的加载顺序即依赖顺序：

```html
<!-- 基础工具 -->
<script src="js/api.js"></script>
<script src="js/auth.js"></script>

<!-- 全局初始化 -->
<script src="js/app.js"></script>

<!-- 页面模块（按加载顺序，无循环依赖） -->
<script src="js/pages/canon.js"></script>
<script src="js/pages/entities.js"></script>
<script src="js/pages/rules.js"></script>
<script src="js/pages/plot.js"></script>
<script src="js/pages/knowledge.js"></script>
<script src="js/pages/template.js"></script>
<script src="js/pages/system.js"></script>

<!-- 新增页面 -->
<script src="js/pages/genre.js"></script>
<script src="js/pages/category.js"></script>
<script src="js/pages/binding.js"></script>
```

每个页面模块的结构统一为：

```javascript
// ============================================================
// Module: canon.js - Canon Documents
// ============================================================
;(function() {
  'use strict';
  
  // 页面 HTML 容器
  function render() {
    return '<div class="page" id="page-canon-list">...</div>';
  }
  
  // 加载函数
  window.loadCanonList = async function() { ... };
  window.loadCanonCreate = async function() { ... };
  
})();
```

---

## 二、实施步骤

### Step 0：准备工作（5分钟）

```
□ 备份 index.html → index.html.backup（原始，永不修改）
□ 提交当前全部代码到 Git
□ 创建 js/ css/ 目录
```

**执行**：
```bash
cp novel-os-web/index.html novel-os-web/index.html.backup
mkdir -p novel-os-web/js/pages novel-os-web/css
git add -A && git commit -m "备份原始文件，准备模块化"
```

### Step 1：server.py 静态文件路由（10分钟）

**目标**：让 server.py 能 serve `*.js`、`*.css` 文件

**当前 do_GET 结构**（仅做最小改动）：

```python
def do_GET(self) -> None:
    # 【新增】静态文件处理
    if self.path.startswith("/js/") or self.path.startswith("/css/"):
        self.serve_static()
        return
    
    if self.path == "/health":
        # ... 现有逻辑不变
    if self.path == "/api/me":
        # ... 现有逻辑不变
    
    # 默认返回 index.html
    body = INDEX.read_bytes()
    # ... 现有逻辑不变

# 【新增方法】
def serve_static(self):
    path = self.path.lstrip("/")
    filepath = Path(__file__).parent / path
    if filepath.exists() and filepath.is_file():
        body = filepath.read_bytes()
        self.send_response(200)
        if path.endswith(".js"):
            self.send_header("Content-Type", "application/javascript")
        elif path.endswith(".css"):
            self.send_header("Content-Type", "text/css")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    else:
        self.send_json(404, {"error": "not found"})
```

**验证**：浏览器访问 `http://${NAS_HOST}:8790/js/app.js` 应返回 404（文件还不存在，但路由通了）

### Step 2：提取 CSS → css/style.css（20分钟）

**目标**：将 index.html 中 `<style>` 标签内的全部 CSS 提取到独立文件

**操作**：
1. 复制 `<style>` 和 `</style>` 之间的全部内容 → `css/style.css`
2. 删除 index.html 中的 `<style>...</style>` 块
3. 在 `<head>` 中添加：`<link rel="stylesheet" href="css/style.css">`

**验证**：刷新页面，样式应完全不变。

**提交**：`git commit -m "Step 2: 提取 CSS 到独立文件"`

### Step 3：提取全局工具 JS → js/app.js（30分钟）

**目标**：提取页面通用的工具函数到 `js/app.js`

**提取内容**：

| 函数 | 用途 |
|------|------|
| `function $(id)` | DOM 查询 |
| `function escapeHtml(str)` | 安全转义 |
| `async function api(path, data)` | API 调用封装 |
| `function showToast(type, msg, detail)` | Toast 提示 |
| `function showModal(html)` | 弹窗 |
| `function closeModal()` | 关闭弹窗 |
| `function setStatus(msg)` | 状态栏 |
| `function t(key)` | 国际化 |
| `var currentPage` | 当前页面状态 |
| `var allProjects` | 项目列表 |
| `var currentWorkspace` | 当前工作区 |

**操作**：
1. 从 index.html 的 `<script>` 中提取上述函数 → `js/app.js`
2. 在 index.html 的 `<script>` 开头插入：`<script src="js/app.js"></script>`
3. 在 index.html 中删除已提取的函数定义

**验证**：刷新页面，所有功能正常工作

**提交**：`git commit -m "Step 3: 提取全局工具 JS"`

### Step 4：提取认证逻辑 → js/auth.js（20分钟）

**目标**：提取登录、工作区、项目相关逻辑

**提取内容**：
- `loadWorkspaces()` 
- `loadProjects()`
- `refreshAuth()`
- 工作区/项目选择器的填充和事件绑定

**验证**：登录、选择工作区、加载项目列表正常工作

**提交**：`git commit -m "Step 4: 提取认证逻辑"`

### Step 5：拆分页面模块（1.5小时）

**目标**：每个现有菜单页面的逻辑提取到独立 JS 文件

**操作方式**（以 canon.js 为例）：

1. 从 index.html `<script>` 中找到 Canon Docs 相关的所有函数
2. 提取到 `js/pages/canon.js`，包裹在 IIFE 中
3. 在 index.html 添加 `<script src="js/pages/canon.js"></script>`
4. 删除 index.html 中已提取的代码
5. 刷新测试 Canon Docs 页面
6. 重复以上步骤处理下一个页面

**提取顺序**：

```
js/pages/canon.js      ← Canon Docs 列表+创建+编辑
js/pages/entities.js   ← Entities 列表+创建  
js/pages/rules.js      ← Writing Rules
js/pages/plot.js       ← 情节线 + 伏笔 + 卷管理
js/pages/knowledge.js  ← 知识库 + UK 管理 + 自动搜索
js/pages/template.js   ← 模板管理
js/pages/system.js     ← 系统管理 + 健康检查
```

**验证**：每提取一个模块，测试该模块对应的页面

**提交**：每提取一个模块单独 commit

### Step 6：精简 index.html（15分钟）

**目标**：index.html 只保留 HTML 结构 + `<script>` 标签引用

```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="css/style.css">
</head>
<body>
  <!-- 侧边栏菜单结构 -->
  <!-- 页面容器 div -->
  
  <script src="js/api.js"></script>
  <script src="js/app.js"></script>
  <script src="js/auth.js"></script>
  <script src="js/pages/canon.js"></script>
  <!-- ... -->
  
  <!-- 路由初始化 -->
  <script>
    // 页面路由注册
    var pageLoader = {
      'canon-list': loadCanonList,
      'canon-create': loadCanonCreate,
      'entities-list': loadEntitiesList,
      // ...
    };
    
    function goToPage(pageName) {
      currentPage = pageName;
      document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
      var target = document.getElementById('page-' + pageName);
      if (target) { target.classList.remove('hidden'); }
      var loader = pageLoader[pageName];
      if (loader) { loader().catch(console.error); }
    }
    
    async function init() {
      await refreshAuth();
      goToPage('canon-list');
    }
    document.addEventListener('DOMContentLoaded', init);
  </script>
</body>
</html>
```

### Step 7：删除冗余菜单 + 添加新功能（1小时）

**Step 7a：删除冗余**

在 index.html 的 HTML 结构中删除：
- `data-page="project-world-rules"` 的 menu-item
- `data-page="project-characters"` 的 menu-item
- `data-page="project-factions"` 的 menu-item
- 整个 `data-section="local-project"` 的 menu-section

**Step 7b：新增菜单项**

在 Knowledge section 中添加：
```html
<div class="menu-item" data-page="genre-manage">📖 小说类型管理</div>
<div class="menu-item" data-page="category-manage">📂 分类管理</div>
<div class="menu-item" data-page="genre-category-bind">🔗 类型与分类绑定</div>
<div class="menu-item" data-page="knowledge-pack">📦 知识包</div>
```

**Step 7c：新增页面容器**

在 index.html 中添加：
```html
<div id="page-genre-manage" class="page hidden">...</div>
<div id="page-category-manage" class="page hidden">...</div>
<div id="page-genre-category-bind" class="page hidden">...</div>
```

**Step 7d：新增页面 JS**

- `js/pages/genre.js` — 小说类型管理
- `js/pages/category.js` — 分类管理
- `js/pages/binding.js` — 类型绑定矩阵

**Step 7e：注册路由**

在路由表中添加：
```javascript
'genre-manage': loadGenreManage,
'category-manage': loadCategoryManage,
'genre-category-bind': loadBindingPage,
```

### Step 8：部署 + Git 推送（10分钟）

```bash
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web
```

---

## 三、GoToPage 路由改造

这是最关键的改造点。当前 `goToPage` 使用 `data-page` 属性 + 事件委托：

```javascript
// 原有模式（保留）
function goToPage(pageName) {
  currentPage = pageName;
  document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
  var target = document.getElementById('page-' + pageName);
  if (target) {
    target.classList.remove('hidden');
    // 调用对应加载函数
    if (pageLoader[pageName]) pageLoader[pageName]();
  }
}
```

**不覆盖原函数**，在模块化过程中将原逻辑提取为路由表：

```javascript
// js/app.js 中的路由表
window.pageLoader = {
  // 已有页面
  'canon-list': loadCanonList,
  'canon-create': loadCanonCreate,
  'entities-list': loadEntitiesList,
  'entities-create': loadEntitiesCreate,
  'template-list': loadTemplateList,
  'template-create': loadTemplateCreate,
  // 【新增】管理页面
  'genre-manage': loadGenreManage,
  'category-manage': loadCategoryManage,
  'genre-category-bind': loadBindingPage,
};
```

---

## 四、新增页面的标准模板

```javascript
// js/pages/genre.js — 示例
;(function() {
  'use strict';

  // ===== 状态 =====
  var genres = [];

  // ===== 页面渲染 =====
  function render() {
    if (!genres.length) return '<p class="empty-state">暂无类型</p>';
    return genres.map(function(g) {
      return '<div class="list-item">' +
        '<span>' + escapeHtml(g.name) + '</span>' +
        '<span class="badge">' + escapeHtml(g.slug || '') + '</span>' +
        '<div class="actions">' +
          '<button onclick="window.editGenre(\'' + escapeHtml(g.slug) + '\')">编辑</button>' +
          '<button onclick="window.deleteGenre(\'' + escapeHtml(g.slug) + '\')">删除</button>' +
        '</div>' +
      '</div>';
    }).join('');
  }

  // ===== 加载 =====
  window.loadGenreManage = async function() {
    setStatus('加载中...');
    try {
      var result = await api('/api/tool', {
        tool: 'setting.genre.list',
        arguments: {}
      });
      if (result.ok) {
        genres = result.result || [];
        document.getElementById('genreList').innerHTML = render();
        setStatus('');
      }
    } catch (e) {
      setStatus('加载失败: ' + e.message);
    }
  };

  // ===== CRUD =====
  window.showGenreForm = function(slug) {
    var g = slug ? genres.find(function(x) { return x.slug === slug; }) : {};
    var html = 
      '<h3>' + (slug ? '编辑' : '新建') + '类型</h3>' +
      '<div class="form-group">' +
        '<label>标识 (slug)</label>' +
        '<input id="genreSlug" value="' + escapeHtml(g.slug || '') + '" ' + (slug ? 'readonly' : '') + '>' +
      '</div>' +
      '<div class="form-group">' +
        '<label>名称</label>' +
        '<input id="genreName" value="' + escapeHtml(g.name || '') + '">' +
      '</div>' +
      '<div class="form-group">' +
        '<label>描述</label>' +
        '<textarea id="genreDesc">' + escapeHtml(g.description || '') + '</textarea>' +
      '</div>' +
      '<div class="form-actions">' +
        '<button onclick="window.saveGenre()">保存</button>' +
        '<button onclick="closeModal()">取消</button>' +
      '</div>';
    showModal(html);
  };

  window.saveGenre = async function() {
    var slug = document.getElementById('genreSlug').value.trim();
    var name = document.getElementById('genreName').value.trim();
    if (!slug || !name) { showToast('warning', '请填写标识和名称'); return; }
    
    setStatus('保存中...');
    var result = await api('/api/tool', {
      tool: 'setting.genre.upsert',
      arguments: {
        slug: slug,
        name: name,
        description: document.getElementById('genreDesc').value.trim()
      }
    });
    if (result.ok) {
      showToast('success', '保存成功');
      closeModal();
      loadGenreManage();
    }
  };

  window.deleteGenre = async function(slug) {
    if (!confirm('确定删除 ' + slug + ' ?')) return;
    var result = await api('/api/tool', {
      tool: 'setting.genre.delete',
      arguments: { slug: slug }
    });
    if (result.ok) {
      showToast('success', '已删除');
      loadGenreManage();
    }
  };

})();
```

---

## 五、防错措施

### 5.1 Git 保护

```
每一步单独 commit，出问题可以精确回滚：
  git reset --hard HEAD~1    # 回退到上一步
  git log --oneline           # 查看所有步骤
```

### 5.2 测试矩阵

| 测试项 | 检查点 |
|--------|--------|
| 页面加载 | 无 JS 报错 |
| 登录 | 正常登录，Session 保持 |
| 工作区选择 | 加载工作区列表，选择后加载项目 |
| 每个菜单页面 | 从 Canon Docs 开始，逐个检查 |
| 新增页面 | 小说类型管理、分类管理、绑定管理 |
| Toast/Modal | 弹窗正常显示和关闭 |

### 5.3 回滚机制

如果某步出错：
1. `git stash` 保存当前修改
2. `git checkout index.html` 恢复 html
3. 修复问题后 `git stash pop`

---

## 六、时间估算

| Step | 内容 | 时间 |
|------|------|------|
| 0 | 准备+备份 | 5min |
| 1 | server.py 静态路由 | 10min |
| 2 | 提取 CSS | 20min |
| 3 | 提取全局 JS | 30min |
| 4 | 提取认证 | 20min |
| 5 | 拆分页面（7个） | 1.5h |
| 6 | 精简 index.html | 15min |
| 7 | 删除冗余+新增功能 | 1h |
| 8 | 部署+推送 | 10min |
| **合计** | | **~4.5h** |

---

## 七、与原始方案的对比

| 维度 | 原始方案（重写 SPA） | 本方案（渐进模块化） |
|------|-------------------|-------------------|
| 风险 | 中（新框架学习成本） | 低（保持现有技术栈） |
| 时间 | 10天 | 4.5小时 |
| 兼容性 | 需重新对接所有 API | 100% 兼容现有逻辑 |
| 可回滚 | 困难（全新代码） | 极易（每步可回滚） |
| 后续扩展 | 容易 | 容易（模块化后等价） |

---

*文档版本：v2.0*  
*创建日期：2026-07-04*