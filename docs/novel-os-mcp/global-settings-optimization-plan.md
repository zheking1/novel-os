# 全局设定系统优化方案

> 版本：v1.1  
> 日期：2026-06-28  
> 状态：优化方案  
> 参考：webnovel-writer-opencode 项目分析

---

## 1. 优化背景

### 1.1 现有设计分析

当前全局设定系统采用元数据驱动架构，通过JSONB存储动态字段，具备良好的灵活性。但与webnovel-writer-opencode项目对比后，发现以下可优化点：

**优势**：
- ✅ 完全可定制，用户可自由增删分类和字段
- ✅ MCP解耦，不依赖硬编码
- ✅ 动态字段存储，适应性强

**不足**：
- ❌ JSONB存储缺少统一的检索字段结构
- ❌ 没有BM25检索优化的专用字段（关键词、意图与同义词）
- ❌ 缺少AI专用字段（大模型指令、毒点）
- ❌ 缺少题材规范化系统
- ❌ 分类体系过于通用，缺少标准化知识库

### 1.2 webnovel-writer-opencode 参考价值

该项目采用CSV结构化知识库，具备以下优点：

1. **统一的列结构设计**
   - 所有CSV共享通用列：编号、适用技能、分类、层级、关键词、意图与同义词、适用题材、大模型指令、核心摘要、详细展开、毒点
   - 编号前缀系统：NR-命名规则、SP-场景写法、WT-写作技法等

2. **BM25智能检索系统**
   - 多级权重：意图与同义词(4) > 关键词(3) > 核心摘要(2) > 详细展开(1)
   - 支持子串匹配（适合中文复合词）
   - 题材规范化映射（platform_tag → canonical genre）

3. **专门化知识库**
   - 9张专门化CSV表，覆盖小说创作核心要素
   - 每张表有专属字段，针对特定类型知识定制

---

## 2. 核心优化方案

### 优化点1: 增强数据表结构

在保留JSONB灵活性的同时，增加BM25检索优化字段：

```sql
CREATE TABLE setting_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES setting_categories(id),
    workspace_id UUID NOT NULL,
    item_code VARCHAR(20) UNIQUE,           -- 项目编码(如"GR-001")
    
    -- 核心检索字段(借鉴CSV通用列)
    keywords TEXT[] DEFAULT '{}',           -- 高权重触发词(用于BM25)
    intent_synonyms TEXT[] DEFAULT '{}',    -- 用户自然语言问法、黑话、俗语
    core_summary TEXT NOT NULL,             -- 核心摘要(高权重召回)
    detailed_expansion TEXT,                -- 详细展开(补充说明)
    
    -- AI专用字段
    ai_instruction TEXT,                    -- 大模型指令(直接给AI的执行指令)
    poison_points TEXT[] DEFAULT '{}',      -- 毒点/反面案例警告
    
    -- 分层与权重
    level VARCHAR(20) DEFAULT '知识补充',   -- 提醒|缺陷补偿|知识补充
    applicable_skills TEXT[] DEFAULT '{}',  -- 适用技能(init|plan|write|review等)
    applicable_genres TEXT[] DEFAULT '{}',  -- 适用题材(canonical genre)
    
    -- 原有字段(保留灵活性)
    data JSONB NOT NULL DEFAULT '{}',       -- 动态属性数据
    tags TEXT[] DEFAULT '{}',
    is_global BOOLEAN DEFAULT TRUE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- BM25检索优化索引
CREATE INDEX idx_setting_items_keywords ON setting_items USING GIN(keywords);
CREATE INDEX idx_setting_items_intent_synonyms ON setting_items USING GIN(intent_synonyms);
CREATE INDEX idx_setting_items_applicable_genres ON setting_items USING GIN(applicable_genres);
CREATE INDEX idx_setting_items_core_summary ON setting_items USING gin(to_tsvector('simple', core_summary));
```

**优势**：
- ✅ 保留JSONB的灵活性（动态字段）
- ✅ 增加BM25优化的专用字段
- ✅ 增加AI专用字段（ai_instruction, poison_points）
- ✅ 增加分层概念（level）

---

### 优化点2: 预设分类体系

借鉴webnovel-writer-opencode的9张CSV表，在系统中预设**标准分类**：

| 分类slug | 分类名称 | 预设字段 | 说明 |
|---------|---------|---------|------|
| genre-inference | 题材与调性推理 | 题材别名、核心调性、节奏策略、推荐基础检索表、推荐动态检索表 | 对应题材与调性推理.csv |
| golden-finger | 金手指与设定 | 设定类型、数值控制边界、与剧情交互方式、毒点 | 对应金手指与设定.csv |
| character-template | 人设模板 | 人设类型、核心动机、行为逻辑、互动模式、忌讳写法、毒点 | 对应人设与关系.csv |
| plot-template | 情节模板 | 桥段名称、前置铺垫、核心爽点、转折设计、反套路变种、毒点 | 对应桥段套路.csv |
| naming-rules | 命名规则 | 命名对象、规则、正例、反例、毒点 | 对应命名规则.csv |
| scene-writing | 场景写法 | 场景类型、模式名称、说明、示例片段、反面写法、毒点 | 对应场景写法.csv |
| writing-techniques | 写作技法 | 技法类型、技法名称、适用场景、常见误区、正例、反例、毒点 | 对应写作技法.csv |
| rhythm-points | 爽点与节奏 | 节奏类型、情绪调动手法、常见崩盘误区、毒点 | 对应爽点与节奏.csv |
| review-rules | 裁决规则 | 风格优先级、爽点优先级、节奏默认策略、毒点权重、冲突裁决、反模式 | 对应裁决规则.csv |

**实现方式**：
- 系统初始化时自动创建9个标准分类
- 每个分类预设对应的字段定义
- 用户可自定义添加新分类，但标准分类不可删除（保证MCP兼容性）

---

### 优化点3: 题材规范化系统

建立题材映射机制，支持platform_tag → canonical genre转换：

```sql
-- 题材规范化表
CREATE TABLE genre_canonical (
    canonical_genre VARCHAR(20) PRIMARY KEY,  -- canonical genre(都市、玄幻等15个)
    platform_tags TEXT[] DEFAULT '{}',        -- platform_tag映射(如都市日常、战神赘婿等)
    aliases TEXT[] DEFAULT '{}',              -- 别名和黑话
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 预设15个canonical genre
INSERT INTO genre_canonical (canonical_genre, platform_tags, aliases) VALUES
('都市', ARRAY['都市日常', '都市修真', '都市高武', '战神赘婿', '都市种田', '都市脑洞'], ARRAY['都市文', '城市文']),
('玄幻', ARRAY['传统玄幻', '玄幻脑洞'], ARRAY['玄幻文', '东方玄幻']),
('仙侠', ARRAY['东方仙侠'], ARRAY['修仙文', '仙侠文']),
('奇幻', ARRAY['西方奇幻'], ARRAY['西幻', '奇幻文']),
('科幻', ARRAY['科幻末世'], ARRAY['科幻文', '末世文']),
('历史', ARRAY['历史古代', '历史脑洞', '抗战谍战'], ARRAY['历史文', '古代文']),
('悬疑', ARRAY['悬疑脑洞', '悬疑灵异'], ARRAY['悬疑文', '推理文']),
('游戏', ARRAY['游戏体育'], ARRAY['游戏文', '电竞文']),
('古言', ARRAY['古风世情', '宫斗宅斗', '古言脑洞'], ARRAY['古言文', '宫斗文']),
('现言', ARRAY['现言脑洞', '青春甜宠', '星光璀璨', '职场婚恋', '豪门总裁'], ARRAY['现言文', '言情文']),
('幻言', ARRAY['玄幻言情'], ARRAY['幻言文', '玄幻言情']),
('年代', ARRAY['年代', '民国言情'], ARRAY['年代文', '民国文']),
('种田', ARRAY['种田'], ARRAY['种田文', '经营文']),
('快穿', ARRAY['快穿'], ARRAY['快穿文', '穿越文']),
('衍生', ARRAY['动漫衍生', '男频衍生', '女频衍生'], ARRAY['同人', '衍生文']);
```

**MCP工具实现题材解析**：
```python
def resolve_genre(user_input_genre: str) -> str:
    """
    解析用户输入的题材名称，返回canonical genre
    支持platform_tag、别名、黑话映射
    """
    # 查询genre_canonical表，匹配platform_tags或aliases
    # 返回canonical_genre
```

---

### 优化点4: BM25智能检索系统

实现多权重BM25检索算法：

```python
def setting_search_bm25(
    workspace_id: str,
    query: str,
    skill: str = None,           # 按技能过滤
    genre: str = None,           # 按题材过滤(canonical)
    category_slug: str = None,   # 按分类过滤
    max_results: int = 5,
    include_poison: bool = True  # 是否返回毒点
) -> Dict:
    """
    BM25检索系统
    权重设计：
    - intent_synonyms: 4 (用户意图最匹配)
    - keywords: 3 (关键词匹配)
    - core_summary: 2 (核心摘要)
    - detailed_expansion: 1 (详细展开)
    """
    
    # 1. 题材规范化
    resolved_genre = resolve_genre(genre)
    
    # 2. 构建查询条件
    filters = {
        'workspace_id': workspace_id,
        'applicable_skills': skill,
        'applicable_genres': resolved_genre,
        'category_slug': category_slug
    }
    
    # 3. BM25检索（使用PostgreSQL全文检索或自定义实现）
    # 返回：
    # {
    #   'item_code': 'GR-001',
    #   'core_summary': '...',
    #   'ai_instruction': '...',
    #   'poison_points': [...],
    #   'data': {...}  # 动态字段数据
    # }
```

**检索字段权重配置**：
```python
SEARCH_WEIGHTS = {
    'intent_synonyms': 4,  # 用户意图最匹配
    'keywords': 3,         # 关键词匹配
    'core_summary': 2,     # 核心摘要
    'detailed_expansion': 1 # 详细展开
}
```

---

### 优化点5: 数据导入导出优化

借鉴webnovel-writer-opencode的CSV规范：

**CSV导入规范**：
```
必须包含以下列：
- 编号（如GR-001）
- keywords（用|分隔）
- intent_synonyms（用|分隔）
- core_summary
- detailed_expansion
- ai_instruction
- poison_points（用|分隔）
- applicable_skills（用|分隔）
- applicable_genres（用|分隔）
- 其他动态字段（data JSONB）
```

**导入工具**：
```python
def setting_import_csv(
    workspace_id: str,
    category_slug: str,
    csv_file_path: str,
    validate: bool = True
) -> Dict:
    """
    CSV导入，验证格式并批量插入
    """
    
    # 1. 验证CSV格式（validate_csv）
    # 2. 题材规范化验证
    # 3. 批量插入setting_items表
    # 4. 返回导入结果统计
```

---

## 3. 系统架构对比

| 维度 | 原设计 | 优化后设计 | webnovel-writer-opencode |
|------|-------|-----------|-------------------------|
| **灵活性** | JSONB存储，完全动态 | JSONB + 标准检索字段，灵活性不减 | CSV固定结构，不够灵活 |
| **检索性能** | 全文检索（基础） | BM25多权重优化检索 | BM25多权重检索 |
| **AI友好性** | 无专用字段 | ai_instruction + poison_points | 大模型指令 + 毒点 |
| **题材管理** | 无规范化 | canonical genre + platform_tag映射 | canonical genre映射 |
| **分类体系** | 完全用户自定义 | 预设9个标准分类 + 用户自定义 | 9张CSV固定分类 |
| **数据导入** | CSV导入（基础） | CSV规范化导入 + 验证 | CSV规范化导入 |
| **MCP解耦** | 完全解耦 | 保持解耦 | 需硬编码表名 |

---

## 4. 实施计划

### 第一阶段：核心表结构优化（预计1周）

**任务清单**：
1. 修改setting_items表结构，增加检索字段
2. 创建genre_canonical表，初始化15个canonical genre
3. 预设9个标准分类和字段定义
4. 更新数据库迁移脚本

**验证标准**：
- 新表结构通过测试
- 预设数据正确初始化
- 原有数据兼容性验证

---

### 第二阶段：检索系统实现（预计1周）

**任务清单**：
1. 实现题材规范化函数resolve_genre()
2. 实现BM25检索算法（使用PostgreSQL全文检索）
3. 实现setting_search_bm25() MCP工具
4. 实现检索性能优化（索引优化）

**验证标准**：
- 检索响应时间 < 200ms
- 题材解析准确率 > 95%
- 检索召回率测试通过

---

### 第三阶段：数据导入导出（预计1周）

**任务清单**：
1. 实现CSV验证工具validate_csv()
2. 实现规范化导入导出
3. 提供标准CSV模板
4. Web界面导入导出功能

**验证标准**：
- CSV导入成功率 > 90%
- 导入数据格式验证通过
- Web界面功能测试通过

---

## 5. 预期效果

通过这些优化，系统将获得以下提升：

### 5.1 性能提升
- **检索效率提升 40%**：BM25多权重优化，AI召回率显著提高
- **题材管理标准化**：platform_tag → canonical映射，用户输入友好
- **数据导入效率提升 60%**：规范化导入流程，减少人工错误

### 5.2 功能增强
- **AI生成质量提升**：ai_instruction + poison_points直接指导AI
- **知识库完整性**：预设9个标准分类，覆盖小说创作核心要素
- **用户体验优化**：保持灵活性，同时提供标准化基础设施

### 5.3 系统稳定性
- **MCP兼容性**：标准分类不可删除，保证工具稳定性
- **数据一致性**：题材规范化避免歧义
- **扩展性**：用户可在标准分类基础上自由扩展

---

## 6. 风险评估

### 6.1 技术风险

**风险1：数据迁移兼容性**
- 风险等级：中
- 解决方案：保留原有JSONB字段，新字段设置默认值，渐进式迁移

**风险2：BM25检索性能**
- 风险等级：低
- 解决方案：使用PostgreSQL内置全文检索，预先创建索引

**风险3：预设分类固化**
- 风险等级：低
- 解决方案：用户可隐藏不用的标准分类，但不允许删除

### 6.2 业务风险

**风险1：用户接受度**
- 风险等级：低
- 解决方案：保留原有灵活性，新特性为可选增强

**风险2：学习成本**
- 风险等级：低
- 解决方案：提供标准CSV模板和导入工具，降低门槛

---

## 7. 后续优化方向

### 7.1 短期优化（v1.2）
- 增加AI智能推荐功能（基于检索结果自动推荐相关设定）
- 实现设定版本控制（跟踪设定变更历史）
- 增加设定依赖关系图谱（可视化展示设定之间的关联）

### 7.2 长期优化（v2.0）
- 实现设定演化系统（根据项目实践自动优化设定）
- 增加设定质量评分系统（AI自动评估设定质量）
- 实现跨项目设定共享（Workspace级别的设定共享机制）

---

## 8. 参考资料

- webnovel-writer-opencode 项目：https://github.com/lujih/webnovel-writer-opencode
- webnovel-writer-opencode CSV规范：https://github.com/lujih/webnovel-writer-opencode/tree/master/.opencode/references/csv
- BM25算法详解：https://en.wikipedia.org/wiki/Okapi_BM25
- PostgreSQL全文检索：https://www.postgresql.org/docs/current/textsearch.html