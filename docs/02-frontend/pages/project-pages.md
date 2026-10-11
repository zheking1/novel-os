# 项目管理页面

## project-manage-page.js (377行)

项目 CRUD 页面，工作区下所有项目的管理入口。

### 功能

- 项目列表展示（名称、slug、描述）
- 新建/编辑项目（slug 验证: `/^[a-z0-9-]+$/`）
- 删除项目（修改 slug 时禁用编辑）
- 搜索过滤（按名称/slug/描述）
- 选择项目 → 自动刷新菜单和项目选择器
- "当前" 徽章标记激活项目

### 关键逻辑

```javascript
// Slug 验证
if (!/^[a-z0-9-]+$/.test(slug)) {
  alert('项目标识只能包含小写字母、数字和横线');
  return;
}

// 选择项目
async selectProject(slug) {
  window.AppState.currentProject = slug;
  localStorage.setItem('novel-project', slug);
  // 更新 header 中的 project-select
  document.getElementById('project-select').value = slug;
  // 重新渲染菜单 → 刷新列表
  await this.loadData();
}

// 删除当前项目时清理
if (window.AppState.currentProject === slug) {
  window.AppState.currentProject = null;
  localStorage.removeItem('novel-project');
}
```

### 使用的 MCP 工具

- `project.list` — 列出工作区项目
- `project.create` — 创建项目
- `project.update` — 更新项目
- `project.delete` — 删除项目

---

## workspace-manage-page.js (426行)

工作区 CRUD + 成员管理子功能。

### 功能

- 工作区列表（slug, name, member_count）
- 创建工作区
- 编辑/删除工作区
- **成员管理子模态框**: 在工作区卡片上点击成员图标
  - 添加成员: `workspace.add_member`
  - 移除成员: `workspace.remove_member`

### 关键逻辑

```javascript
// 成员管理子模态框
<button onclick="WorkspaceManagePage.showMembersModal('workspace-slug')">

// 添加成员
await ApiClient.callTool('workspace.add_member', {
  workspace: slug,
  username: username,
  role: 'editor'
});

// 移除成员
await ApiClient.callTool('workspace.remove_member', {
  workspace: slug,
  username: username
});
```

### 使用的 MCP 工具

- `workspace.list` — 列出所有工作区
- `workspace.create` — 创建工作区
- `workspace.update` — 更新工作区
- `workspace.delete` — 删除工作区
- `workspace.add_member` — 添加成员
- `workspace.remove_member` — 移除成员

---

## member-manage-page.js

成员列表展示和角色管理。

### 功能

- 列出工作区所有成员
- 显示角色信息
- 可能支持批量操作

---

## home-page.js (305行)

首页仪表盘，两个 Tab: "工作台" 和 "使用教程"。

### 工作台内容

#### 模型状态网格

6 个任务类型的模型统计卡片:
- 审核 (review)
- 润色 (polish)
- 向量 (embedding)
- 分析 (analysis)
- 上下文 (context)
- 重排序 (rerank)

每个卡片显示该类型的激活模型数，绿色表示有激活模型，红色表示无。

#### 配置缺失提醒

如果任何关键类型缺少模型，显示黄色警告框引导用户去配置。

#### 项目进度条

遍历前 3 个工作区，每个工作区取前 5 个项目:
- 显示章节总数和完成数
- 进度条 (完成比例)
- 待审核任务数
- 最近活动

#### 最近动态

获取最近 5 条审核任务记录，显示项目名、章节号、状态、时间。

### 使用教程内容

4 步引导:
1. 系统配置 (配置模型 / API Key / AGENTS.md / MCP 连接)
2. AI 工具对话创建小说
3. AI 工具生成章节
4. 完成提示

包含一键复制 `AGENTS.md` 和 MCP 配置 JSON 的功能。

### 使用的 MCP 工具

- `workspace.list` — 列出工作区
- `model.profile.list` — 列出模型配置
- `project.list` — 列出项目
- `local.chapter.list` — 列出章节
- `volume.list` — 列出卷
- `review.list_revision_tasks` — 审核任务列表