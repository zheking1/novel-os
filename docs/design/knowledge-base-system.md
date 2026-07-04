# Novel OS 知识库系统设计文档

> 版本: v2.0
> 状态: 确认
> 创建时间: 2026-07-01
> 更新时间: 2026-07-01

---

## 1. 系统概述

### 1.1 设计目标

构建一套双层知识库系统，为小说生成提供精准的上下文数据支持：

- **通用知识库 (Universal Knowledge)**：跨项目、跨用户共享的参考资料，通过 web_search 自动积累
- **项目知识库 (Project Knowledge)**：单本小说专属的世界设定、角色、剧情状态

### 1.2 核心原则

| 原则 | 说明 |
|------|------|
| 按需加载 | 不是一次性灌入所有数据，而是根据章节内容精准检索 |
| 增量补充 | 写到哪补到哪，不提前搜索未使用的内容 |
| 自动积累 | 通用知识库通过 web_search + AI 整理自动入库 |
| 全局共享 | 通用知识库所有用户、所有项目共享复用 |
| 题材感知 | 不同题材使用不同的数据策略 |
| 状态追踪 | 世界状态随章节推进持续更新 |
| 用户自治 | 每个用户自行配置检索模型，不强制通用 |

### 1.3 设计决策记录

| 编号 | 问题 | 决策 |
|------|------|------|
| Q1 | 初始数据来源 | web_search 搜索 → AI 整理 → 统一格式入库 |
| Q2 | 搜索质量保证 | 多来源交叉验证 + 可信度评分 + 保留来源URL |
| Q3 | 更新频率 | 按需补充，写到才补，不提前搜 |
| Q4 | 知识共享 | universal_knowledge 全局共享，所有用户所有项目 |
| Q5 | 关联维护 | 内置模型自动关联（人物↔事件↔势力↔地点） |
| Q6 | 检索性能 | Qdrant语义 + PG精确过滤 + 按genre分collection |
| Q7 | 统一格式 | 人物/事件/设定统一模板 + 关联关系 |
| Q8 | 搜索触发 | 生成前自动检测章纲 → 缺失 → 搜索 |
| Q9 | 知识粒度 | 按章节进程增量补充（写到哪补到哪，逐渐完整） |
| Q10 | 冲突处理 | 取可信度高的版本 |
| Q11 | 成本控制 | 免费小模型，不考虑成本 |
| Q12 | 模型配置 | 每个用户自行配置检索模型（model_profiles），不强制通用 |

### 1.4 与现有系统的关系

```
现有系统:
  knowledge_base (2327条) → 写作方法论/模板（保留）
  canon_rules (94条)      → 写作规则（保留）
  foreshadowing (30条)    → 伏笔追踪（保留）
  state_entities          → 角色状态追踪（保留）
  embedding.py            → EmbeddingService（复用）
  model_profiles          → 模型配置（复用）

新增系统:
  universal_knowledge     → 通用知识库（新增）
  project_knowledge       → 项目知识库（新增）
  world_snapshots         → 世界状态快照（新增）
  genre_strategies        → 题材策略配置（新增）
  ref_categories          → 知识分类（新增）
  knowledge_entities      → 知识实体（新增）
  knowledge_relations     → 实体关联（新增）
  ref_search_jobs         → 搜索任务队列（新增）
  ref_gap_logs            → 知识缺口记录（新增）
```

---

## 2. 通用知识库 (Universal Knowledge)

### 2.1 定义

跨项目、跨用户的参考资料。所有同题材、同时代的小说都能复用。通过 web_search 自动搜索、AI 自动整理入库。

### 2.2 知识分类

```
ref_categories
├── 01 历史资料
│   ├── 历史人物（生平、性格、关系、评价）
│   ├── 历史事件（时间、地点、原因、经过、影响）
│   ├── 历史进程（时间线、阶段划分、转折点）
│   ├── 野史传闻（民间故事、未解之谜、八卦）
│   └── 历史地理（城市、地标、交通、行政区划）
│
├── 02 时代背景
│   ├── 政治体制（政府结构、权力运作、党派）
│   ├── 经济体系（货币、物价、行业、贸易）
│   ├── 社会结构（阶层、帮派、组织、风俗）
│   ├── 文化风俗（礼仪、服饰、饮食、语言、禁忌）
│   └── 科技水平（通讯、交通、武器、医疗、日常）
│
├── 03 题材设定模板
│   ├── 修仙体系（境界划分、丹药、法宝、功法、门派）
│   ├── 玄幻设定（种族、力量体系、世界规则）
│   ├── 科幻设定（科技树、外星、AI、时空理论）
│   ├── 灵异设定（鬼怪分类、规则体系、禁忌）
│   ├── 末日设定（变异类型、生存体系、势力模式）
│   ├── 游戏设定（系统类型、技能树、副本设计）
│   └── 都市设定（现代职业、社会关系、科技应用）
│
├── 04 专业知识
│   ├── 军事（武器参数、战术编制、战争史）
│   ├── 医学（中医理论、西医常识、毒药药理）
│   ├── 建筑（各时代建筑风格、结构特点）
│   ├── 法律（各朝代法律、现代法律常识）
│   ├── 宗教（教义、仪式、禁忌、传说）
│   ├── 工艺（锻造、炼丹、制符、烹饪）
│   └── 自然科学（物理、化学、生物常识）
│
└── 05 写作参考
    ├── 对话风格（各时代说话方式、方言特点）
    ├── 描写素材（环境、人物外貌、动作、心理）
    └── 名称素材（人名库、地名库、招式名库）
```

### 2.3 数据来源

| 来源 | 说明 | 质量 | 可信度 |
|------|------|------|--------|
| web_search | 生成前自动搜索，AI 整理入库 | 中等 | 0.4-0.7 |
| manual | 用户手动录入 | 高 | 0.8-1.0 |
| import | 批量导入（历史资料包） | 高 | 0.7-0.9 |
| ai_generated | AI 生成的设定模板（仙侠/玄幻） | 中等 | 0.5-0.7 |

### 2.4 增量补充策略

```
写到哪补到哪，不提前搜索：

第1章写到1935年:
  → 搜索"1935年 中国 历史事件" → 入库
  → 搜索"1935年 上海 社会状况" → 入库

第20章写到1937年:
  → 检查通用库有没有1937年资料
  → 没有 → 搜索"1937年 卢沟桥事变" → 入库
  → 有 → 直接用

第50章写到朱元璋:
  → 检查有没有朱元璋资料
  → 没有/不完整 → 搜索"朱元璋 登基" → 增量补充
  → 有 → 直接用

随着多个用户写多个小说，知识库自动越来越完整
```

### 2.5 数据质量控制

```
reliability_score（可信度 0-1）:
  1.0 = 权威来源（教科书、官方资料）
  0.8 = 可信来源（百科、学术文章）
  0.6 = 一般来源（网络文章、知乎高赞）
  0.4 = 待验证（AI 生成、用户手动）
  0.2 = 低可信度（来源不明）

冲突处理:
  同一主题多来源 → 取可信度高的版本
  可信度相同时 → 取内容更详细的版本

过期机制:
  历史知识：创建后基本不变
  当代知识：last_verified_at 超过 1 年 → 标记 needs_verify
  生成时遇到 needs_verify → 自动重新搜索校验
```

---

## 3. 项目知识库 (Project Knowledge)

### 3.1 定义

单本小说专属的知识。随创作推进不断变化。不跨项目共享。

### 3.2 知识分类

```
project_knowledge
├── world_rules（世界规则）
│   ├── 力量体系定义（修仙境界、科技等级）
│   ├── 世界物理规则（灵气浓度、时间流速）
│   ├── 社会规则（门派制度、法律体系）
│   └── 经济规则（货币体系、资源分布）
│
├── characters（角色档案）
│   ├── 主要角色（身份、背景、性格、目标、秘密）
│   ├── 次要角色（身份、动机、与主角关系）
│   └── 历史角色在小说中的设定
│
├── factions（势力档案）
│   ├── 组织（名称、目标、成员、资源、弱点）
│   └── 国家/朝代（政治格局、军事力量、经济状况）
│
├── plot（剧情设定）
│   ├── 大纲（总纲、卷纲、章纲）
│   ├── 伏笔（已埋伏笔、兑现计划）
│   └── 因果链（事件因果关系）
│
├── world_state（世界状态）
│   ├── 当前局势（政治、经济、军事、社会）
│   ├── 势力关系（联盟、敌对、中立）
│   └── 资源分布（灵脉、矿产、领地）
│
└── timeline（项目时间线）
    ├── 故事时间线（章节对应的故事时间）
    └── 重要节点（转折点、高潮点）
```

### 3.3 项目知识的生命周期

```
创建阶段（项目初始化）:
  用户定义 → 世界规则、主角设定、初始势力
  系统预置 → 从通用知识库加载相关模板

创作阶段（逐章推进）:
  每章生成后 → 自动更新世界状态
  每章生成后 → 自动更新角色状态
  每章生成后 → 自动记录新伏笔

维护阶段:
  定期校验 → 角色一致性、设定一致性
  冲突检测 → 发现矛盾时提醒用户
```

---

## 4. 知识实体与关联 (Entities & Relations)

### 4.1 设计理念

知识条目不是孤立的，而是网状关联的。人物、事件、势力、地点之间存在复杂关系。

```
朱元璋 ──── 参与 ──── 鄱阳湖之战
  │                      │
  ├── 身份: 皇帝          ├── 时间: 1363年
  ├── 性格: 果断多疑      ├── 地点: 鄱阳湖
  └── 关联人物:           └── 参与人物:
       ├── 马皇后(皇后)        ├── 朱元璋(战胜)
       ├── 刘伯温(军师)        ├── 陈友谅(战败)
       └── 徐达(大将)          └── 俞通海(战死)

检索"鄱阳湖之战" → 同时返回参战人物的简要状态
检索"朱元璋" → 同时返回他参与的重要事件
```

### 4.2 实体类型

| 实体类型 | 说明 | structured_data 示例 |
|---------|------|---------------------|
| person | 历史/虚构人物 | `{"birth":"1889","death":"1936","personality":["果断"],"role":"军阀"}` |
| event | 历史/虚构事件 | `{"date":"1937-07-07","location":"卢沟桥","consequence":"全面抗战"}` |
| place | 地点 | `{"type":"城市","era":"民国","features":["租界","港口"]}` |
| faction | 势力/组织 | `{"type":"军阀","territory":"东北","strength":"强"}` |
| concept | 概念/设定 | `{"type":"修炼体系","levels":["练气","筑基","金丹"]}` |

### 4.3 关联类型

| 关联类型 | 说明 | 示例 |
|---------|------|------|
| participated_in | 参与事件 | 朱元璋 → participated_in → 鄱阳湖之战 |
| located_at | 位于地点 | 鄱阳湖之战 → located_at → 鄱阳湖 |
| belongs_to | 属于势力 | 朱元璋 → belongs_to → 红巾军 |
| related_to | 人物关系 | 朱元璋 → related_to → 马皇后(夫妻) |
| caused_by | 因果关系 | 明朝建立 → caused_by → 北伐成功 |
| same_as | 同一实体 | 朱元璋 → same_as → 明太祖 |
| influenced_by | 受影响 | 朱元璋性格 → influenced_by → 乞丐经历 |

### 4.4 自动关联机制

```
AI 整理知识条目时自动提取关联：

输入: "朱元璋，1328年出生，1368年建立明朝，1398年去世。"
AI 提取:
  实体: {name: "朱元璋", type: "person", birth: 1328, death: 1398}
  实体: {name: "明朝", type: "faction", founded: 1368}
  关联: 朱元璋 → same_as → 明太祖
  关联: 朱元璋 → founded → 明朝

输入: "1363年鄱阳湖之战，朱元璋击败陈友谅。"
AI 提取:
  实体: {name: "鄱阳湖之战", type: "event", date: 1363}
  关联: 朱元璋 → participated_in → 鄱阳湖之战
  关联: 陈友谅 → participated_in → 鄱阳湖之战
  关联: 鄱阳湖之战 → located_at → 鄱阳湖
```

---

## 5. 题材策略 (Genre Strategy)

### 5.1 策略类型

| 策略类型 | 时间线 | 通用知识来源 | 项目知识重点 |
|---------|--------|-------------|-------------|
| real_historical | 真实历史年份 | 按年份搜索历史资料 | 虚构角色嵌入历史 |
| real_modern | 当代时间 | 搜索当代社会资料 | 现代背景故事 |
| progression | 自创进度 | 加载题材模板 | 修炼/升级体系 |
| hybrid | 混合 | 历史资料 + 自创规则 | 真实背景 + 虚构设定 |
| pure_fiction | 自创时间 | 加载题材模板 | 完全虚构世界 |

### 5.2 题材策略配置

```json
{
  "genre": "historical_republic",
  "display_name": "民国历史",
  "strategy": "real_historical",
  "timeline_type": "real_year",
  "data_sources": {
    "history": "web_search_by_year",
    "culture": "universal_knowledge",
    "geography": "universal_knowledge"
  },
  "knowledge_scope": {
    "preload": ["era_background", "geography"],
    "on_demand": ["historical_events", "historical_figures"],
    "skip": ["cultivation_system", "fantasy_setting"]
  },
  "search_keywords_template": [
    "{year}年 中国",
    "{year}年 {city}",
    "{event_name} 历史"
  ],
  "incremental_fetch": true
}
```

### 5.3 已支持题材

| 题材ID | 名称 | 策略类型 | 通用知识来源 |
|--------|------|---------|-------------|
| historical_republic | 民国历史 | real_historical | 按年份搜索 1912-1949 |
| historical_ancient | 古代历史 | real_historical | 按朝代搜索 |
| xianxia | 仙侠 | progression | 修仙体系模板 |
| xuanhuan | 玄幻 | progression | 力量体系模板 |
| sci-fi | 科幻 | hybrid | 科学概念 + 虚构技术 |
| urban | 都市 | real_modern | 当代社会资料 |
| post_apocalyptic | 末日 | pure_fiction | 末日设定模板 |
| horror | 灵异 | pure_fiction | 鬼怪规则模板 |
| game | 游戏 | pure_fiction | 游戏设定模板 |
| time_travel | 穿越 | hybrid | 历史资料 + 金手指设定 |
| isekai | 异世界 | pure_fiction | 完全虚构 |

---

## 6. 世界状态追踪 (World Snapshots)

### 6.1 设计理念

不管什么题材，世界状态都用统一的结构追踪。每章生成后自动更新。

### 6.2 统一结构

```json
{
  "chapter_no": 30,
  "story_time": "1937年7月",
  "story_year": 1937,
  "world_state": {
    "politics": "国民党统治，日本侵略加剧",
    "military": "抗日战争即将全面爆发",
    "economy": "法币贬值，物价上涨",
    "society": "抗日情绪高涨，学生运动",
    "technology": "电报、电话、火车、轮船"
  },
  "character_states": [
    {"name": "张三", "status": "律师，已发现日本商人阴谋"},
    {"name": "李四", "status": "地下党，正在策划行动"}
  ],
  "active_threads": ["日本商人阴谋", "张三身份秘密"],
  "relevant_knowledge_ids": ["uuid1", "uuid2"]
}
```

### 6.3 不同题材的状态差异

```
历史小说:
  world_state = {politics, military, economy, society, technology}
  story_year = 1937
  story_time = "1937年7月"

仙侠小说:
  world_state = {灵气浓度, 最强势力, 世界威胁, 修炼体系状态}
  story_progress = 0.3 (主角修炼进度 30%)
  story_era = "灵气复苏初期"

科幻小说:
  world_state = {tech_level, ai_status, space_colonies, main_conflict}
  story_year = 2150
  story_time = "火星殖民第10年"

末日小说:
  world_state = {days_since_disaster, safe_zones, zombie_level, resources}
  story_progress = 0.2
  story_era = "灾难后第3年"
```

### 6.4 状态更新时机

```
每章生成后:
  1. 解析生成内容 → 提取世界状态变化
  2. 更新 world_snapshots
  3. 更新 state_entities（角色状态）
  4. 更新 foreshadowing（伏笔状态）
  5. 记录 chapter_summaries（章节摘要）
```

---

## 7. 生成流程集成

### 7.1 完整流程

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: 题材策略识别                                         │
│   project.genre → 加载 genre_strategy                       │
│   确定时间线类型、数据来源、检索策略                           │
├─────────────────────────────────────────────────────────────┤
│ Step 2: 加载项目知识（必加载）                                │
│   world_snapshots（最近状态）                                │
│   state_entities（出场角色）                                 │
│   foreshadowing（相关伏笔）                                  │
│   chapter_plans（本章大纲）                                  │
│   chapter_summaries（最近摘要）                              │
├─────────────────────────────────────────────────────────────┤
│ Step 3: 加载通用知识（条件加载）                              │
│   if real_historical:                                       │
│     检查通用库有无该年份资料                                  │
│     有 → 直接用                                             │
│     没有 → web_search 按年份搜索 → AI 整理 → 入库 → 使用    │
│   if progression:                                           │
│     按主角境界 → 加载对应模板                                │
│   if hybrid:                                                │
│     两者都做                                                │
│   if pure_fiction:                                          │
│     加载题材模板（如有）                                     │
├─────────────────────────────────────────────────────────────┤
│ Step 4: 知识缺口检测                                        │
│   解析章纲 → 提取关键实体（人物/地点/事件/概念）              │
│   查 universal_knowledge → 是否有相关条目                   │
│   查 project_knowledge → 是否有相关设定                     │
│   缺失 → 触发 web_search 补充到通用库                       │
├─────────────────────────────────────────────────────────────┤
│ Step 5: 精准检索                                            │
│   用章纲主题 + 出场角色 → 语义搜索                           │
│   universal_knowledge（通用知识）                            │
│   project_knowledge（项目知识）                              │
│   knowledge_entities（实体详情）                             │
│   knowledge_relations（关联实体）                            │
│   → Top N 最相关条目                                        │
├─────────────────────────────────────────────────────────────┤
│ Step 6: 组装 Context Pack                                   │
│   sections:                                                │
│     - active_rules（写作规则）                               │
│     - current_state（角色状态）                              │
│     - world_state（世界状态）                                │
│     - universal_knowledge（通用知识）                        │
│     - project_knowledge（项目知识）                          │
│     - chapter_plan（章节大纲）                               │
│     - foreshadowing（相关伏笔）                              │
│     - recent_summaries（近期摘要）                           │
│     - output_constraint（输出约束）                          │
├─────────────────────────────────────────────────────────────┤
│ Step 7: 生成 + 后处理                                       │
│   Agent 生成内容                                            │
│   → 合规校验（validate_content）                             │
│   → 更新 world_snapshots                                    │
│   → 更新 state_entities                                     │
│   → 更新 chapter_summaries                                  │
│   → 更新 foreshadowing                                      │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 检索优先级

```
1. project_knowledge（最高优先）
   → 本小说的世界规则、角色设定，不可替代

2. universal_knowledge（按需加载）
   → 同题材通用知识，按章节内容精准检索

3. knowledge_base（写作参考）
   → 写作方法论、模板，教 Agent 怎么写

4. canon_rules（硬性约束）
   → 不可违反的规则，必须遵守
```

### 7.3 Token 预算分配

```
total_budget = 100%
├── output_constraint:   3%  （输出格式约束）
├── active_rules:       15%  （写作规则）
├── project_knowledge:  22%  （项目知识：角色+世界+剧情）
├── universal_knowledge: 18%  （通用知识：按需检索）
├── current_state:      15%  （角色状态快照）
├── world_state:         8%  （世界状态）
├── chapter_plan:        7%  （本章大纲）
├── foreshadowing:       8%  （相关伏笔）
└── recent_summaries:    4%  （近期摘要）
```

### 7.4 检索模型配置

```
每个用户自行配置检索模型（model_profiles 表）:

User A:
  embedding: BAAI/bge-m3
  rerank: BAAI/bge-reranker-v2-m3

User B:
  embedding: Qwen/Qwen3-Embedding-0.6B
  rerank: Qwen/Qwen3-Reranker-0.6B

User C:
  不配置 → 降级到 PostgreSQL 关键词搜索

配置位置: model_profiles 表，task_types = ['embedding'] / ['rerank']
检索时: EmbeddingService._get_config(project_id) → 获取用户配置
```

---

## 8. 数据库设计

### 8.1 知识分类表

```sql
CREATE TABLE ref_categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  parent_id UUID REFERENCES ref_categories(id),
  slug VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  genre_tags TEXT[] DEFAULT '{}',
  search_keywords TEXT[] DEFAULT '{}',
  sort_order INT DEFAULT 0,
  is_system BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### 8.2 知识实体表

```sql
CREATE TABLE knowledge_entities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  -- 实体信息
  entity_type VARCHAR(50) NOT NULL,
  -- person: 历史/虚构人物
  -- event: 历史/虚构事件
  -- place: 地点
  -- faction: 势力/组织
  -- concept: 概念/设定
  
  name VARCHAR(200) NOT NULL,
  aliases TEXT[] DEFAULT '{}',
  summary TEXT,
  content TEXT NOT NULL,
  
  -- 结构化数据
  structured_data JSONB DEFAULT '{}',
  
  -- 来源
  source VARCHAR(50) DEFAULT 'manual',
  source_url TEXT,
  reliability FLOAT DEFAULT 0.5,
  
  -- 适用范围
  genre_tags TEXT[] DEFAULT '{}',
  era VARCHAR(100),
  
  -- 检索
  embedding_id TEXT,
  search_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('simple', COALESCE(name,'') || ' ' || COALESCE(content,''))
  ) STORED,
  
  -- 状态
  status VARCHAR(20) DEFAULT 'active',
  use_count INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_ke_type ON knowledge_entities(entity_type);
CREATE INDEX idx_ke_genre ON knowledge_entities USING GIN(genre_tags);
CREATE INDEX idx_ke_search ON knowledge_entities USING GIN(search_vector);
CREATE INDEX idx_ke_embedding ON knowledge_entities(embedding_id);
```

### 8.3 实体关联表

```sql
CREATE TABLE knowledge_relations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  from_entity_id UUID REFERENCES knowledge_entities(id) ON DELETE CASCADE,
  to_entity_id UUID REFERENCES knowledge_entities(id) ON DELETE CASCADE,
  
  relation_type VARCHAR(50) NOT NULL,
  -- participated_in: 参与事件
  -- located_at: 位于地点
  -- belongs_to: 属于势力
  -- related_to: 人物关系
  -- caused_by: 因果关系
  -- same_as: 同一实体
  -- influenced_by: 受影响
  
  relation_detail VARCHAR(200),
  -- 例: "夫妻"、"师徒"、"敌对"、"战胜"
  
  strength FLOAT DEFAULT 1.0,
  metadata JSONB DEFAULT '{}',
  
  created_at TIMESTAMPTZ DEFAULT now(),
  
  UNIQUE(from_entity_id, to_entity_id, relation_type)
);

CREATE INDEX idx_kr_from ON knowledge_relations(from_entity_id);
CREATE INDEX idx_kr_to ON knowledge_relations(to_entity_id);
CREATE INDEX idx_kr_type ON knowledge_relations(relation_type);
```

### 8.4 通用知识库（兼容旧结构）

```sql
CREATE TABLE universal_knowledge (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  
  category_id UUID REFERENCES ref_categories(id),
  
  topic VARCHAR(200) NOT NULL,
  summary TEXT,
  content TEXT NOT NULL,
  structured_data JSONB DEFAULT '{}',
  
  -- 适用范围
  era VARCHAR(100),
  year_range INT[],
  genre_tags TEXT[] DEFAULT '{}',
  
  -- 来源和质量
  source VARCHAR(50) DEFAULT 'manual',
  source_url TEXT,
  reliability FLOAT DEFAULT 0.5,
  last_verified_at TIMESTAMPTZ,
  
  -- 检索
  embedding_id TEXT,
  search_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('simple', COALESCE(topic,'') || ' ' || COALESCE(content,''))
  ) STORED,
  tags TEXT[] DEFAULT '{}',
  
  -- 状态
  status VARCHAR(20) DEFAULT 'active',
  use_count INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_uk_genre ON universal_knowledge USING GIN(genre_tags);
CREATE INDEX idx_uk_year ON universal_knowledge(year_range);
CREATE INDEX idx_uk_search ON universal_knowledge USING GIN(search_vector);
CREATE INDEX idx_uk_embedding ON universal_knowledge(embedding_id);
```

### 8.5 项目知识库

```sql
CREATE TABLE project_knowledge (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL,
  
  category VARCHAR(50) NOT NULL,
  -- world_rule: 世界规则
  -- character: 角色档案
  -- faction: 势力档案
  -- plot: 剧情设定
  -- world_state: 世界状态
  -- timeline: 时间线
  
  key VARCHAR(200) NOT NULL,
  value JSONB NOT NULL,
  description TEXT,
  
  chapter_no INT,
  related_entry_ids UUID[] DEFAULT '{}',
  tags TEXT[] DEFAULT '{}',
  
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  UNIQUE(project_id, category, key)
);

CREATE INDEX idx_pk_project ON project_knowledge(project_id);
CREATE INDEX idx_pk_category ON project_knowledge(project_id, category);
```

### 8.6 世界状态快照

```sql
CREATE TABLE world_snapshots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL,
  
  chapter_no INT NOT NULL,
  story_time VARCHAR(100),
  story_year INT,
  story_era VARCHAR(100),
  story_progress FLOAT,
  
  world_state JSONB NOT NULL,
  
  character_count INT DEFAULT 0,
  active_threads TEXT[] DEFAULT '{}',
  relevant_knowledge_ids UUID[] DEFAULT '{}',
  
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_ws_project ON world_snapshots(project_id, chapter_no);
```

### 8.7 搜索任务队列

```sql
CREATE TABLE ref_search_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID,
  
  query_text TEXT NOT NULL,
  search_context TEXT,
  category_id UUID REFERENCES ref_categories(id),
  
  status VARCHAR(20) DEFAULT 'pending',
  results_count INT DEFAULT 0,
  entries_created INT DEFAULT 0,
  error_message TEXT,
  
  triggered_by VARCHAR(50),
  chapter_no INT,
  
  created_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);
```

### 8.8 知识缺口记录

```sql
CREATE TABLE ref_gap_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID,
  
  gap_type VARCHAR(50) NOT NULL,
  description TEXT NOT NULL,
  context TEXT,
  
  entity_name VARCHAR(200),
  entity_type VARCHAR(50),
  
  resolved BOOLEAN DEFAULT false,
  resolved_by_entry_id UUID,
  resolved_at TIMESTAMPTZ,
  
  created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 9. API 工具设计

### 9.1 知识实体工具

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `entity.create` | 创建知识实体 | type, name, content, structured_data, genre_tags, ... |
| `entity.update` | 更新知识实体 | entity_id, ... |
| `entity.get` | 获取知识实体 | entity_id / name / type |
| `entity.search` | 语义搜索实体 | query, type, genre, era, limit |
| `entity.list_relations` | 列出实体关联 | entity_id, relation_type |
| `entity.create_relation` | 创建实体关联 | from_id, to_id, type, detail |
| `entity.batch_create` | 批量创建实体 | entries[] |

### 9.2 通用知识库工具

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `uk.category_list` | 列出知识分类 | parent_slug, genre |
| `uk.search` | 语义搜索通用知识 | query, genre, era, year, limit |
| `uk.entry_create` | 创建知识条目 | category_id, topic, content, ... |
| `uk.entry_update` | 更新知识条目 | entry_id, ... |
| `uk.auto_search` | 触发自动搜索 | query, genre, chapter_no |
| `uk.batch_import` | 批量导入 | entries[] |
| `uk.stats` | 统计各分类知识量 | genre |

### 9.3 项目知识库工具

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `pk.upsert` | 创建/更新项目知识 | project, category, key, value |
| `pk.get` | 获取项目知识 | project, category, key |
| `pk.list` | 列出项目知识 | project, category |
| `pk.delete` | 删除项目知识 | project, category, key |

### 9.4 世界状态工具

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `world.get_state` | 获取当前世界状态 | project, chapter_no |
| `world.update_state` | 更新世界状态 | project, chapter_no, world_state |
| `world.get_snapshot` | 获取历史快照 | project, chapter_no |
| `world.diff` | 对比两个快照差异 | project, chapter_a, chapter_b |

### 9.5 题材策略工具

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `genre.list` | 列出支持的题材 | |
| `genre.get_strategy` | 获取题材策略 | genre_id |
| `genre.create` | 创建自定义题材 | ... |

### 9.6 知识缺口工具

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `gap.detect` | 检测知识缺口 | project, chapter_no |
| `gap.list` | 列出未解决缺口 | project |
| `gap.resolve` | 标记缺口已解决 | gap_id, entry_id |

---

## 10. 数据流总览

```
                        ┌─────────────┐
                        │  Web Search │
                        └──────┬──────┘
                               │
                               ▼
┌──────────────┐    ┌──────────────────┐
│ ref_search   │───→│ knowledge_       │
│ _jobs        │    │ entities         │
│ (搜索队列)    │    │ (知识实体库)      │
└──────────────┘    └────────┬─────────┘
                             │
                             ├── knowledge_relations (关联)
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
     ┌──────────────────┐         ┌──────────────────┐
     │ universal_       │         │ project_         │
     │ knowledge        │         │ knowledge        │
     │ (通用知识)        │         │ (项目知识)        │
     └────────┬─────────┘         └────────┬─────────┘
              │                             │
              └─────────────┬───────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ context_pack │
                     │ (上下文组装)  │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Agent 生成    │
                     └──────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
       ┌──────────┐  ┌──────────┐  ┌──────────┐
       │ world_   │  │ state_   │  │ chapter_ │
       │ snapshots│  │ entities │  │ summaries│
       └──────────┘  └──────────┘  └──────────┘
```

---

## 11. 实现阶段

| 阶段 | 内容 | 优先级 | 依赖 |
|------|------|--------|------|
| Phase 1 | 表结构创建（ref_categories, knowledge_entities, knowledge_relations） | P0 | - |
| Phase 2 | 表结构创建（universal_knowledge, project_knowledge, world_snapshots） | P0 | - |
| Phase 3 | 基础 CRUD API（entity.*, uk.*, pk.*） | P0 | Phase 1-2 |
| Phase 4 | 题材策略配置（genre_strategies） | P0 | Phase 1-2 |
| Phase 5 | web_search 自动补充 + AI 整理入库 | P1 | Phase 3 |
| Phase 6 | 知识缺口检测（gap.*） | P1 | Phase 3 |
| Phase 7 | 集成到 prepare_chapter_context | P0 | Phase 3-4 |
| Phase 8 | 世界状态追踪（world.*） | P1 | Phase 3 |
| Phase 9 | 生成后自动更新状态 | P1 | Phase 7-8 |
| Phase 10 | 预置题材知识包（民国/仙侠等） | P2 | Phase 3 |
| Phase 11 | 知识图谱可视化（实体关联图） | P3 | Phase 3 |
