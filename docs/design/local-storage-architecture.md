# 本地存储 + 索引架构设计

> 目标：2000万字小说生成，上下文不溢出、逻辑不崩、剧情不崩、人设不崩
> 日期：2026-07-02

---

## 一、核心原则

**精准检索数据进 DB，长文本内容留本地。**

| 数据类型 | 存储位置 | DB 存什么 | 原因 |
|---------|---------|----------|------|
| 章节正文 | 本地 .md | 路径+字数+状态+摘要 | 3000-10000字/章，纯内容无需DB |
| 章纲 | 本地 .md | 路径+章节号+关键情节点 | 500-2000字，需检索关键情节 |
| 审查报告 | 本地 .md | 路径+模型名+评分+问题列表 | 500-2000字，需检索问题 |
| 总体审查意见 | 本地 .md | 路径+综合评分+通过状态 | 需检索结论 |
| 人物设定卡 | 本地 .json | 完整结构化数据 | 需精确查询属性 |
| 世界规则长文本 | 本地 .md | 路径+摘要+关键词 | 需语义检索 |
| 势力关系 | 本地 .json | 完整关系图 | 需图查询 |
| 伏笔记录 | 本地 .json | 完整结构化数据 | 需状态追踪 |

---

## 二、本地目录结构

```
用户本地/
  novels/
    小说名/
      .novel-index.json          ← 索引元数据（自动维护）
      
      小说设定/
        人物设定/
          张三.json              ← 角色卡（结构化）
          李四.json
        世界规则/
          魔法体系.md            ← 长文本设定
          地理.md
        势力关系.json            ← 结构化
        
      第01章/
        ch01_outline.md          ← 章纲
        ch01_draft.md            ← 初稿
        ch01_revision_1.md       ← 修订稿
        ch01_final.md            ← 定稿
        审查报告/
          model_A_report.md      ← 模型A审查
          model_B_report.md      ← 模型B审查
          summary.md             ← 总体意见
          
      第02章/
        ...
```

---

## 三、DB 索引 Schema

### 3.1 chapter_index（章节索引）

```sql
CREATE TABLE chapter_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    chapter_no INT NOT NULL,
    title VARCHAR(200),
    status VARCHAR(20) DEFAULT 'planned',  -- planned/draft/revised/final
    word_count INT DEFAULT 0,
    summary TEXT,                          -- 200-500字摘要
    local_path VARCHAR(500),               -- 本地相对路径
    outline_path VARCHAR(500),             -- 章纲路径
    review_passed BOOLEAN DEFAULT FALSE,
    review_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, chapter_no)
);
```

**不存：** 章节正文、修订历史全文

### 3.2 review_index（审查索引）

```sql
CREATE TABLE review_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID REFERENCES chapter_index(id),
    model_name VARCHAR(100),
    score FLOAT,                           -- 综合评分 0-100
    issues JSONB,                          -- [{type, severity, description, line}]
    passed BOOLEAN DEFAULT FALSE,
    local_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**不存：** 审查报告全文

### 3.3 setting_index（设定索引）

```sql
CREATE TABLE setting_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    category VARCHAR(50),                  -- character/world/faction/rule
    name VARCHAR(200) NOT NULL,
    keywords TEXT[],                       -- 关键词
    summary TEXT,                          -- 摘要
    local_path VARCHAR(500),
    structured_data JSONB,                 -- .json 文件存完整数据
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 3.4 向量索引（复用 Qdrant）

只存摘要和关键词的嵌入向量，不存全文。

```
Collection: chapter_summaries
  Payload: { project_id, chapter_no, title, status, local_path }
  Vector: embedding(summary + keywords)

Collection: setting_summaries
  Payload: { project_id, category, name, local_path }
  Vector: embedding(summary + keywords)
```

---

## 四、文件监听 + 索引同步

### 4.1 监听机制

```
本地文件变化 → 文件系统监听 (chokidar) → 更新 .novel-index.json
                                            ↓
                                    提取摘要 + 关键词
                                            ↓
                                    生成向量嵌入（可选）
                                            ↓
                                    写入 chapter_index / setting_index
```

### 4.2 .novel-index.json 格式

```json
{
  "version": "1.0",
  "project_name": "小说名",
  "last_sync": "2026-07-02T12:00:00Z",
  "chapters": {
    "1": {
      "title": "第一章",
      "status": "final",
      "word_count": 4523,
      "files": {
        "outline": "第01章/ch01_outline.md",
        "draft": "第01章/ch01_draft.md",
        "final": "第01章/ch01_final.md",
        "reviews": ["第01章/审查报告/model_A_report.md"]
      },
      "summary": "...",
      "updated_at": "2026-07-02T12:00:00Z"
    }
  },
  "settings": {
    "characters": ["小说设定/人物设定/张三.json"],
    "world_rules": ["小说设定/世界规则/魔法体系.md"],
    "factions": ["小说设定/势力关系.json"]
  }
}
```

### 4.3 同步策略

| 事件 | 触发 | 动作 |
|------|------|------|
| 新章节文件创建 | 文件监听 | 提取摘要 → 写入 chapter_index → 生成向量 |
| 章节文件修改 | 文件监听 | 更新 word_count → 重新提取摘要 → 更新向量 |
| 审查报告生成 | 文件监听 | 解析评分 → 写入 review_index |
| 设定文件修改 | 文件监听 | 更新 setting_index → 更新向量 |
| 手动同步 | 用户触发 | 全量扫描 → 对比 .novel-index.json → 增量更新 |

---

## 五、本地管理 Skill 设计

### 5.1 Skill 名称：`novel-local`

### 5.2 功能

| 功能 | 描述 |
|------|------|
| `local.scan` | 扫描本地目录，构建/更新 .novel-index.json |
| `local.sync` | 同步 .novel-index.json 到 DB 索引 |
| `local.watch` | 启动文件监听，实时同步 |
| `local.read` | 读取本地文件内容（按需加载） |
| `local.write` | 写入本地文件（生成结果） |
| `local.search` | 基于 DB 索引搜索，返回本地文件路径 |
| `local.stats` | 统计本地项目信息（字数、章节数等） |

### 5.3 与 MCP 工具集成

```
MCP 工具调用 → novel-local skill → 本地文件系统 → 返回结果
```

新增 MCP 工具：
- `local.project.scan` — 扫描项目目录
- `local.chapter.read` — 读取章节内容
- `local.chapter.write` — 写入章节内容
- `local.chapter.list` — 列出章节（基于索引）
- `local.review.read` — 读取审查报告
- `local.setting.read` — 读取设定文件
- `local.search` — 语义搜索（基于向量索引）

---

## 六、Pipeline 工作流

### 6.1 生成流程

```
1. 用户选择本地项目目录
2. 扫描目录 → 构建索引 → 同步到 DB
3. 用户选择生成章节（如第15章）
4. MCP 生成章纲 → 写入本地 ch15_outline.md
5. MCP 生成初稿 → 写入本地 ch15_draft.md
6. MCP 调用多个模型审查 → 写入本地 审查报告/
7. 生成总体意见 → 写入本地 summary.md
8. 提取摘要 → 更新 chapter_index → 更新向量
9. 用户查看结果（Web UI 显示摘要，按需加载全文）
```

### 6.2 上下文控制

```
生成第 N 章时：
1. 从 DB 索引加载：
   - 前3章摘要（非全文）
   - 相关实体设定（结构化数据）
   - 当前伏笔状态
   - 写作规则
2. 从本地加载：
   - 第 N 章章纲（按需读取）
3. 生成结果写入本地，不占 DB 空间
```

---

## 七、2000万字不崩策略

### 7.1 上下文不溢出

- **DB 只存摘要和结构化数据**，不存全文
- 生成时只加载相关摘要，不加载全文
- 向量检索返回 Top-K 摘要，不返回全文

### 7.2 逻辑不崩

- 伏笔状态追踪（DB）
- 因果关系链（DB）
- 规则冲突检测（DB）

### 7.3 剧情不崩

- 章节摘要向量检索，确保剧情连贯
- 章纲强制生成，控制剧情走向
- 多模型审查，检测剧情漏洞

### 7.4 人设不崩

- 人物设定结构化存储（DB）
- 人物状态快照（DB）
- 审查时检查人设一致性

---

## 八、Web UI 改造

### 8.1 新增页面

| 页面 | 功能 |
|------|------|
| Pipeline | 选择项目目录 → 扫描 → 生成章节 → 查看结果 |
| 章节管理 | 浏览本地章节列表 → 查看摘要 → 按需加载全文 |
| 系统监控 | Health / Cache / Backup |

### 8.2 改造页面

| 页面 | 改造 |
|------|------|
| 章节列表 | 从 DB 索引加载，显示摘要而非全文 |
| 审查报告 | 从本地文件加载，显示评分和问题列表 |
| 设定管理 | 混合加载：结构化数据从 DB，长文本从本地 |

---

## 九、实施计划

### Phase 1：本地目录结构 + 索引 Schema
- 创建 .novel-index.json 规范
- 创建 DB migration（chapter_index, review_index, setting_index）
- 创建本地管理 Skill 骨架

### Phase 2：文件监听 + 同步
- 实现 chokidar 监听
- 实现 .novel-index.json 更新逻辑
- 实现 DB 同步逻辑

### Phase 3：MCP 工具集成
- 新增 local.* 工具
- 集成到现有 pipeline

### Phase 4：Web UI 改造
- 新增 Pipeline 页面
- 新增章节管理页面
- 改造现有页面使用本地数据
