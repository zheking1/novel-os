# Novel OS 知识系统工作流程说明

## 你的问题：为什么没有自动创建知识包？

### 核心答案

**当前的 Novel OS 实现中，知识包的创建和知识检索都是手动的，不是自动的。**

这是**设计上的缺陷或未完成的功能**，不是你的操作问题。

---

## 理想的工作流程（设计预期）

```
创建项目 "西域铁骑：反攻大清"
    ↓
[缺失] 系统应该自动识别小说类型：穿越历史
    ↓
[缺失] 自动创建知识包 (kb.pack.create)
    ↓
[缺失] 自动分析项目需求：
       - 康熙初年的历史背景
       - 伊犁、哈萨克草原地理
       - 清廷官制、军事制度
       - 主角穿越前的现代知识领域
    ↓
[缺失] 自动触发知识搜索 (kb.auto.search)
       - "康熙初年历史"
       - "哈萨克草原地理"
       - "清朝军事制度"
       - "中亚历史"
    ↓
[缺失] 将搜索结果存入 Universal Knowledge (kb.auto.store)
    ↓
[缺失] 关联到项目知识包 (kb.pack.update)
    ↓
生成大纲时自动引用相关知识
    ↓
生成章节时自动引用相关知识
```

---

## 实际的工作流程（当前实现）

```
创建项目 "西域铁骑：反攻大清"
    ↓
✅ 项目创建成功（只保存基本信息）
    ↓
❌ 没有自动创建知识包！
    ↓
❌ 没有自动搜索相关知识！
    ↓
❌ 知识库是空的！
    ↓
用户需要手动：
    1. 创建知识包 (kb.pack.create)
    2. 手动搜索知识 (kb.auto.search)
    3. 手动存储结果 (kb.auto.store)
    4. 手动配置分类 (kb.pack.update)
```

---

## 涉及的关键 MCP 工具

### 1. 知识缺口检测 (应该在生成大纲前调用)

```python
novel-os.kb.gap.detect
  - project_id: "你的项目ID"
  - chapter_no: 1
  - chapter_plan: "第一章大纲内容..."
```

**作用**：分析大纲，识别需要但缺失的知识点

### 2. 自动搜索 (应该在检测到缺口后调用)

```python
novel-os.kb.auto.search
  - query: "康熙初年伊犁历史"
  - category_slug: "history" 
  - chapter_no: 1
  - project_id: "你的项目ID"
```

**作用**：创建搜索任务，返回 job_id

### 3. 存储搜索结果 (应该在搜索完成后调用)

```python
novel-os.kb.auto.store
  - job_id: "搜索任务ID"
  - search_results: [
      {"title": "...", "url": "...", "snippet": "..."}
    ]
```

**作用**：将 web_search 结果存入 Universal Knowledge

### 4. 知识包管理 (手动配置)

```python
# 创建知识包
novel-os.kb.pack.create
  - project_id: "你的项目ID"
  - genre: "穿越历史"

# 更新知识包配置
novel-os.kb.pack.update
  - project_id: "你的项目ID"
  - active_categories: ["历史", "地理", "军事"]
```

---

## 什么时候应该调用知识检索？

### 设计上的预期时机：

| 时机 | 应该调用的工具 | 当前实现状态 |
|------|---------------|-------------|
| **项目创建时** | kb.pack.create, kb.auto.search | ❌ 未实现 |
| **生成大纲前** | kb.gap.detect → kb.auto.search | ❌ 未实现 |
| **生成章节前** | kb.gap.detect → kb.auto.search | ❌ 未实现 |
| **发现知识缺口时** | kb.gap.create | ✅ 已实现 |

### 实际需要的调用流程：

**方案 A：项目创建时自动初始化（推荐）**
```python
# 1. 创建项目
novel-os.project.create(...)

# 2. 【缺失】应该自动执行：
#    - kb.pack.create(genre="穿越历史")
#    - kb.auto.search("康熙初年历史")
#    - kb.auto.search("哈萨克草原地理")
#    - kb.auto.search("清朝军事制度")
#    - kb.auto.store(...)
```

**方案 B：生成大纲前检查（当前 workaround）**
```python
# 1. 手动创建知识包
novel-os.kb.pack.create(...)

# 2. 手动搜索相关知识
novel-os.kb.auto.search("康熙初年历史")
# ... 执行 web_search ...
novel-os.kb.auto.store(job_id, results)

# 3. 生成大纲时引用知识
novel-os.workflow.prepare_chapter_context(...)
```

---

## 为什么知识包和本地项目菜单没有数据？

### 知识包为空的原因：

1. **创建项目时没有自动创建知识包**
   - 系统只创建了项目基本信息
   - 没有调用 `kb.pack.create`

2. **没有自动搜索和导入知识**
   - 没有调用 `kb.auto.search`
   - 没有将历史/地理知识存入知识库

3. **知识包是空的配置容器**
   - 就像创建了一个空文件夹
   - 需要手动填充内容

### 本地项目为空的原因：

1. **本地项目是可选功能**
   - 用于绑定本地文件系统
   - 不是项目的必需组件

2. **需要手动注册**
   - 调用 `local.project.register`
   - 指定本地目录路径

---

## 解决方案建议

### 短期解决方案（手动操作）

你可以立即执行以下操作来填充知识：

```python
# 1. 为你的项目创建知识包
novel-os.kb.pack.create
  - project_id: "68048e44-737f-4746-a669-eefc9e13545d"
  - genre: "穿越历史"

# 2. 搜索康熙初年历史
novel-os.kb.auto.search
  - query: "康熙初年历史 清朝早期政治制度"
  - project_id: "68048e44-737f-4746-a669-eefc9e13545d"

# 3. 搜索哈萨克草原地理
novel-os.kb.auto.search
  - query: "哈萨克草原地理 中亚历史 伊犁"
  - project_id: "68048e44-737f-4746-a669-eefc9e13545d"

# 4. 搜索清朝军事
novel-os.kb.auto.search
  - query: "清朝军事制度 八旗制度 清军装备"
  - project_id: "68048e44-737f-4746-a669-eefc9e13545d"
```

### 长期解决方案（系统改进）

应该在以下环节添加自动知识初始化：

1. **项目创建向导** (`novel.wizard`)
   - 在创建项目时询问小说类型
   - 自动创建知识包
   - 自动触发相关知识的搜索

2. **大纲生成前**
   - 自动调用 `kb.gap.detect`
   - 根据缺口自动搜索知识
   - 将搜索结果存入知识包

3. **章节生成前**
   - 检测当前章节需要的知识
   - 自动补充缺失的知识

---

## 总结

| 问题 | 答案 |
|------|------|
| 为什么没有自动创建知识包？ | 系统未实现自动创建功能 |
| 为什么没有自动搜索知识？ | 系统未实现自动生成时的知识检索 |
| 知识包应该什么时候填充？ | 项目创建时或生成大纲前 |
| 当前需要怎么操作？ | 手动创建知识包并搜索相关知识 |
| 这是 bug 还是设计？ | 是未完成的功能，不是 bug |

**建议**：如果你需要完整的历史知识支撑，我可以帮你手动创建知识包并触发相关搜索。或者我们可以建议开发者在项目创建向导中添加自动知识初始化功能。
