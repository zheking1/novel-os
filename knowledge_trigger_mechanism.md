# Novel OS 知识系统自动触发机制设计

## 问题核心

**谁来判断何时触发知识检索？**
**触发时机是什么？**

---

## 方案一：项目创建时自动触发（推荐）

### 触发时机
**项目创建完成时**

### 判断者
**系统（项目创建向导 / novel.wizard）**

### 工作流程

```
用户填写项目信息
    ↓
系统分析小说类型（用户选择或AI推断）
    ↓
【触发点】自动调用知识初始化流程
    ↓
1. kb.pack.create(genre=分析结果)
2. 根据genre确定知识主题
3. 创建多个kb.auto.search任务
4. 执行web_search
5. kb.auto.store存储结果
6. kb.pack.update启用相关分类
    ↓
项目创建完成，知识包已填充
```

### 实现代码示例

```python
# novel.wizard.commit 或 project.create 内部
async def auto_init_knowledge_pack(project_id: str, genre: str, description: str):
    """项目创建时自动初始化知识包"""
    
    # 1. 创建知识包
    await kb_pack_create(project_id=project_id, genre=genre)
    
    # 2. 根据类型确定搜索主题
    search_topics = generate_search_topics(genre, description)
    # 例如：
    # 穿越历史 → ["清朝历史", "康熙年间", "官职制度", ...]
    # 仙侠 → ["修仙体系", "丹药等级", "法宝分类", ...]
    
    # 3. 创建搜索任务
    for topic in search_topics:
        job = await kb_auto_search(
            query=topic,
            project_id=project_id,
            category_slug=infer_category(topic)
        )
        
        # 4. 立即执行搜索并存储（或放入队列异步处理）
        results = await web_search(topic)
        await kb_auto_store(job_id=job.id, search_results=results)
    
    # 5. 启用相关分类
    categories = infer_categories_from_genre(genre)
    await kb_pack_update(
        project_id=project_id,
        active_categories=categories
    )
```

### 优点
- ✅ 用户无感知，一键完成
- ✅ 项目创建时数据完整
- ✅ 后续生成可直接使用

### 缺点
- ⚠️ 项目创建时间增加（需要等待搜索完成）
- ⚠️ 可能创建不必要的知识（如果用户不生成某些类型内容）

---

## 方案二：大纲生成前触发

### 触发时机
**生成大纲前（workflow.prepare_chapter_context 之前）**

### 判断者
**大纲生成服务 / workflow 模块**

### 工作流程

```
用户请求生成大纲
    ↓
系统检查当前项目知识包
    ↓
【判断逻辑】
IF 知识包为空:
    → 触发知识初始化
ELIF 大纲涉及未知领域:
    → 触发增量知识搜索
ELSE:
    → 使用现有知识
    ↓
执行 workflow.prepare_chapter_context
```

### 判断逻辑

```python
async def should_init_knowledge(project_id: str, chapter_plan: str) -> bool:
    """判断是否需要初始化知识"""
    
    # 1. 检查知识包是否存在
    pack = await kb_pack_get(project_id=project_id)
    if not pack:
        return True  # 需要创建
    
    # 2. 检查知识包是否为空
    if not pack.active_categories:
        return True  # 需要填充
    
    # 3. 检测知识缺口（可选）
    gaps = await kb_gap_detect(
        project_id=project_id,
        chapter_plan=chapter_plan
    )
    if gaps:
        return True  # 需要补充知识
    
    return False
```

### 实现代码示例

```python
# workflow.prepare_chapter_context 内部
async def prepare_chapter_context(project_id: str, chapter_no: int, ...):
    
    # 【触发点】检查并初始化知识
    if await should_init_knowledge(project_id, chapter_plan):
        await auto_init_knowledge_pack(project_id, ...)
    
    # 继续正常流程...
    context = await assemble_context(project_id, chapter_no)
    return context
```

### 优点
- ✅ 延迟加载，按需获取
- ✅ 可以根据具体大纲调整搜索方向
- ✅ 项目创建更快

### 缺点
- ⚠️ 第一次生成大纲有延迟（需要等待搜索）
- ⚠️ 用户可能感到困惑（为什么第一次慢）

---

## 方案三：知识缺口检测触发

### 触发时机
**生成内容时检测到知识缺口**

### 判断者
**知识缺口检测服务 / kb.gap.detect**

### 工作流程

```
生成大纲/章节
    ↓
解析内容提取实体和概念
    ↓
检查知识库是否包含这些信息
    ↓
【判断逻辑】
IF 发现知识缺口:
    → 创建缺口记录 kb.gap.create
    → 触发自动搜索 kb.auto.search
    → 用户确认或自动存储
ELSE:
    → 继续生成
```

### 判断逻辑

```python
async def detect_and_fill_gaps(project_id: str, content: str):
    """检测并填充知识缺口"""
    
    # 1. 检测缺口
    gaps = await kb_gap_detect(
        project_id=project_id,
        content=content
    )
    
    for gap in gaps:
        # 2. 创建缺口记录
        await kb_gap_create(
            entity_name=gap.entity,
            entity_type=gap.type,
            description=f"缺失{gap.entity}的相关知识"
        )
        
        # 3. 触发搜索
        job = await kb_auto_search(
            query=f"{gap.entity} {gap.context}",
            project_id=project_id
        )
        
        # 4. 存储结果
        results = await web_search(gap.entity)
        await kb_auto_store(job_id=job.id, search_results=results)
```

### 优点
- ✅ 精准获取所需知识
- ✅ 不浪费资源搜索无用信息
- ✅ 可以持续学习积累

### 缺点
- ⚠️ 实现复杂度高
- ⚠️ 需要准确的缺口检测算法
- ⚠️ 可能中断生成流程

---

## 方案四：混合触发策略（最终推荐）

结合以上三种方案的优点：

### 第一层：项目创建时（基础框架）

```python
# 项目创建时
async def on_project_create(project_id, genre, description):
    # 仅创建知识包框架，不执行搜索
    await kb_pack_create(project_id=project_id, genre=genre)
    
    # 根据类型预设启用的分类
    categories = infer_categories_from_genre(genre)
    await kb_pack_update(project_id=project_id, active_categories=categories)
```

### 第二层：大纲生成前（按需填充）

```python
# 生成大纲前
async def before_outline_generation(project_id, chapter_plan):
    # 检查知识包是否需要填充
    pack = await kb_pack_get(project_id=project_id)
    
    if pack.is_empty or pack.last_updated < 7_days_ago:
        # 执行基础搜索
        await search_basic_knowledge(project_id, pack.genre)
    
    # 检测特定缺口
    gaps = await kb_gap_detect(project_id=project_id, content=chapter_plan)
    for gap in gaps:
        await search_and_store(gap.entity)
```

### 第三层：运行时动态补充

```python
# 生成过程中
async def during_generation(project_id, current_content):
    # 实时检测新出现的缺口
    gaps = await kb_gap_detect(project_id=project_id, content=current_content)
    
    for gap in gaps:
        if gap.priority == "high":
            # 立即搜索（阻塞）
            await search_and_store(gap.entity)
        else:
            # 放入队列异步处理
            await queue_background_search(gap.entity)
```

---

## 触发判断矩阵

| 触发时机 | 判断者 | 触发条件 | 搜索范围 | 优先级 |
|---------|--------|---------|---------|--------|
| 项目创建 | 创建向导 | 新项目创建 | 类型相关基础框架 | 高 |
| 大纲生成前 | 生成服务 | 知识包为空/过时 | 大纲相关内容 | 高 |
| 缺口检测 | 检测服务 | 发现未知实体 | 特定实体 | 中 |
| 运行时 | 生成服务 | 出现新概念 | 实时补充 | 低 |

---

## 当前系统缺失的功能

### 已实现
- ✅ `kb.pack.create` - 创建知识包
- ✅ `kb.auto.search` - 创建搜索任务
- ✅ `kb.auto.store` - 存储搜索结果
- ✅ `kb.gap.detect` - 检测知识缺口
- ✅ `kb.gap.create` - 创建缺口记录

### 缺失（需要实现）
- ❌ **自动触发逻辑** - 上述判断逻辑
- ❌ **类型推断** - 从项目描述推断搜索主题
- ❌ **搜索队列** - 异步执行搜索任务
- ❌ **结果去重** - 避免重复搜索相似内容
- ❌ **知识关联** - 将知识与章节内容关联

---

## 建议实现优先级

### P0（立即实现）
1. 项目创建时自动创建知识包
2. 大纲生成前检查并填充知识

### P1（近期实现）
3. 知识缺口检测触发
4. 异步搜索队列

### P2（长期优化）
5. 智能类型推断
6. 知识关联分析
7. 知识质量评估

---

## 你现在可以使用的方式

### 手动触发（当前）
```python
# 1. 创建知识包
novel-os.kb.pack.create(project_id="...", genre="穿越历史")

# 2. 搜索知识
novel-os.kb.auto.search(query="康熙初年历史", project_id="...")
# ... 执行 web_search ...
novel-os.kb.auto.store(job_id="...", search_results=[...])

# 3. 更新配置
novel-os.kb.pack.update(project_id="...", active_categories=["历史", "地理"])
```

### 自动触发（待实现）
```python
# 系统自动执行
novel-os.project.create(...)
# → 自动触发知识初始化
# → 无需手动操作
```
