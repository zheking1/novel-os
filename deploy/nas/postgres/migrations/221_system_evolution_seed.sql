-- Migration: 221_system_evolution_seed.sql
-- Description: 系统级进化架构默认数据导入
-- Author: OpenCode AI Agent
-- Date: 2024-01-15
-- Depends: 220_system_evolution.sql

-- ========================================
-- 1. 导入系统级文风档案
-- ========================================

INSERT INTO system_style_profiles 
(profile_key, display_name, narrative_pov, tense, tone, target_metrics, 
 description, characteristics, sample_paragraphs, applicable_genres, status)
VALUES
('xuanhuan_heroic', '玄幻热血', 'third_limited', 'past', '热血激昂',
 '{"avg_sentence_length": 22, "avg_paragraph_length": 120, "dialogue_ratio": 0.25, "action_scene_ratio": 0.35, "chapter_word_count": {"min": 2500, "target": 3000, "max": 3500}}',
 '传统玄幻热血风格，注重主角成长、战斗场面、打脸反派，节奏紧凑，爽点密集。',
 '{"narrative_features": ["主角视角为主，偶尔上帝视角", "心理活动丰富，突出主角情绪变化", "战斗场景动作描写详细", "反派脸谱化但下场凄惨"], "language_features": ["使用大量成语和四字短语", "动词前置增强冲击力", "短句用于高潮场景", "排比句增强气势"], "rhythm_features": ["每章至少一个爽点", "每五章一个中高潮", "每二十章一个大高潮", "打脸场景节奏要快"]}',
 ARRAY['林动双拳紧握，指甲深深嵌入掌心，鲜血顺着指缝滴落。但他的眼神却愈发坚定，仿佛有两团火焰在瞳孔中燃烧。三年之约，我林动必当赴约！少年的声音不大，却如惊雷般在每个人耳边炸响。那股不屈的意志，让在场所有人都不禁动容。', '轰！狂暴的元力如海啸般席卷而出，整个比武台瞬间崩塌。烟尘弥漫中，一道身影倒飞而出，重重砸在地面，一口鲜血狂喷而出。怎么可能……王炎难以置信地瞪大眼睛，你明明只是元丹境！林动缓步走出烟尘，嘴角勾起一抹冷笑：元丹境又如何？杀你，足够了。'],
 ARRAY['玄幻', '东方玄幻'], 'active'
),
('xianxia_cultivation', '仙侠修真', 'third_limited', 'past', '飘逸出尘',
 '{"avg_sentence_length": 25, "avg_paragraph_length": 150, "dialogue_ratio": 0.30, "description_ratio": 0.40, "chapter_word_count": {"min": 2800, "target": 3200, "max": 4000}}',
 '传统仙侠修真风格，注重境界突破、法宝丹药、师门情谊，文风飘逸，意境深远。',
 '{"narrative_features": ["第三人称限知视角", "大量环境描写营造意境", "突破境界时的细腻刻画", "师门情谊与正邪对立"], "language_features": ["使用古典词汇和道家术语", "四字短语营造韵律感", "诗词化描写景色", "对话文雅含蓄"], "rhythm_features": ["修炼场景节奏缓慢细腻", "战斗场景节奏紧凑", "突破境界详写", "日常场景简写"]}',
 ARRAY['晨雾缭绕，仙鹤长鸣。王林盘膝坐在洞府前的青石上，周身灵气如潮水般涌动。他的呼吸绵长而悠远，每一次吐纳，都有肉眼可见的灵气漩涡在身周形成。忽然，他眉头一皱，体内的灵力开始躁动不安，如脱缰野马般在经脉中横冲直撞。来了！王林心中一凛，知道这是突破筑基期的关键时刻。', '那是一柄通体碧绿的长剑，剑身上刻有繁复的云纹，剑柄处镶嵌着一颗鸽卵大小的夜明珠。青冥剑，上品法器。长老的声音缓缓响起，此剑随老夫三百余年，今日便赐予你。望你日后勤加修炼，莫要辱没了这柄剑的威名。'],
 ARRAY['仙侠', '修真', '古典仙侠'], 'active'
),
('urban_supernatural', '都市异能', 'first', 'present', '轻松诙谐',
 '{"avg_sentence_length": 18, "avg_paragraph_length": 100, "dialogue_ratio": 0.40, "humor_ratio": 0.20, "chapter_word_count": {"min": 2000, "target": 2500, "max": 3000}}',
 '现代都市背景下的异能风格，语言轻松幽默，结合现代生活场景，爽文与搞笑并存。',
 '{"narrative_features": ["第一人称视角，代入感强", "内心吐槽丰富", "现代网络用语", "校园/职场日常与异能结合"], "language_features": ["现代口语化表达", "网络流行语适度使用", "短句为主，节奏轻快", "内心独白多用破折号"], "rhythm_features": ["每章至少一个笑点", "装逼打脸要爽快", "感情线细水长流", "异能展示要酷炫"]}',
 ARRAY['我叫张浩，二十二岁，普通大学毕业生，目前失业在家。好吧，以上是昨天的我。今天的我——好吧，还是失业，但我有了超能力！事情要从昨晚说起。我在楼下便利店买了桶泡面，老板找零时多给了我十块钱。我本着良心发现的态度回去退还，结果一脚踩空摔进了下水道。然后，我就觉醒了一个超能力——透视。', '小伙子，看你骨骼清奇，是个练武的好苗子。我：大爷，您这话我听过，下一句是不是要卖给我一本如来神掌？老头：你怎么知道？我：……十分钟后，我手里多了本《异能入门指南》，微信转账出去五百块。我是不是被骗了？'],
 ARRAY['都市', '异能', '超能力'], 'active'
),
('sci_fi_space', '科幻星际', 'third_limited', 'past', '宏大冷峻',
 '{"avg_sentence_length": 28, "avg_paragraph_length": 180, "dialogue_ratio": 0.20, "tech_description_ratio": 0.30, "chapter_word_count": {"min": 3000, "target": 3500, "max": 4500}}',
 '硬科幻星际风格，注重科技设定、宇宙尺度、文明冲突，文风宏大严谨，逻辑自洽。',
 '{"narrative_features": ["多视角叙事", "科技设定详细", "宇宙尺度的时间感", "文明冲突的哲学思考"], "language_features": ["科技术语准确使用", "数据化描述", "长句构建复杂场景", "专业词汇表"], "rhythm_features": ["科技解密节奏缓慢", "战斗场景紧凑", "文明冲突史诗感", "伏笔埋设长远"]}',
 ARRAY['距离太阳系4.2光年的半人马座α星，三体文明的母星。三颗恒星在天空中做着无法预测的混沌运动，引力潮汐将行星表面撕扯得千疮百孔。在这样的地狱环境中，三体文明发展出了独特的脱水生存技术，在恒纪元与乱纪元之间艰难延续。', '曲率引擎启动的那一刻，整艘飞船仿佛被一只无形的大手攥住。程心感到一阵强烈的眩晕，窗外的星空开始扭曲，星光被拉伸成一条条长长的光线。飞船前方的空间被压缩，后方的空间被拉伸，形成一个巨大的空间泡。'],
 ARRAY['科幻', '星际', '硬科幻'], 'active'
),
('wuxia_jianghu', '武侠江湖', 'third_limited', 'past', '快意恩仇',
 '{"avg_sentence_length": 20, "avg_paragraph_length": 130, "dialogue_ratio": 0.35, "action_ratio": 0.30, "chapter_word_count": {"min": 2500, "target": 3000, "max": 3500}}',
 '传统武侠江湖风格，注重侠义精神、武功招式、门派恩怨，文风洒脱，快意恩仇。',
 '{"narrative_features": ["侠义精神贯穿始终", "武功招式详细描写", "门派恩怨纠葛", "江湖规矩与潜规则"], "language_features": ["古典武侠用语", "招式名称诗意化", "对白有江湖气", "四字短语营造节奏"], "rhythm_features": ["打斗场景动作分解", "报仇雪恨节奏紧凑", "儿女情长细腻", "江湖夜雨诗意"]}',
 ARRAY['刀光剑影，血溅三尺。李寻欢的飞刀已经出手，没有人能形容那一刀的速度，正如没有人能形容闪电的速度。刀光一闪，一切归于平静。上官金虹瞪大了眼睛，不可置信地看着插入自己咽喉的那柄小刀。', '江湖道义？楚留香轻笑一声，什么是江湖道义？是强者为尊，还是弱肉强食？他仰头灌下一口酒，目光望向远方：我只知道，做人要对得起自己的良心。'],
 ARRAY['武侠', '传统武侠', '江湖'], 'active'
);

-- ========================================
-- 2. 导入系统级提示词模板
-- ========================================

INSERT INTO system_prompt_templates
(template_key, template_name, template_content, description, template_type, genre, scene, variables, status)
VALUES
('chapter_outline', '章节大纲生成', 
'请根据以下信息生成第{chapter_no}章的详细大纲：

【故事背景】
{story_background}

【前文概要】
{previous_summary}

【本章目标】
{chapter_goal}

【约束条件】
- 章节字数：{word_count}字
- 节奏类型：{pacing_type}
- 紧张度：{tension_level}/10

请生成以下格式的大纲：

## 章节标题
（10字以内，有吸引力）

## 场景列表
1. 场景一名称 - 场景描述 - 字数分配
2. ...

## 情节推进
- 起因：
- 发展：
- 高潮：
- 结局：

## 人物出场
- 主要人物及任务

## 伏笔与回收
- 埋设伏笔：
- 回收伏笔：

## 爽点/情绪点
（本章的高潮或爽点设计）',
'根据故事背景和前文生成详细的章节大纲，包含场景分解、情节推进、人物安排等',
'outline', null, null,
'[{"name": "chapter_no", "type": "number", "required": true, "description": "章节号"}, {"name": "story_background", "type": "text", "required": true, "description": "故事整体背景"}, {"name": "previous_summary", "type": "text", "required": true, "description": "前文章节概要"}, {"name": "chapter_goal", "type": "text", "required": true, "description": "本章需要完成的目标"}, {"name": "word_count", "type": "number", "required": true, "description": "目标字数"}, {"name": "pacing_type", "type": "string", "required": true, "description": "节奏类型(fast/normal/slow)"}, {"name": "tension_level", "type": "number", "required": true, "description": "紧张度1-10"}]',
'active'
),
('battle_scene', '战斗场景生成',
'请根据以下信息生成一段精彩的战斗场景：

【战斗双方】
甲方：{party_a}
乙方：{party_b}

【战斗背景】
{battle_context}

【战斗环境】
{environment}

【战斗阶段】
{phase}（开场/高潮/结束）

【必须展现的元素】
{required_elements}

【风格要求】
{style_requirements}

生成要求：
1. 动作描写详细，有画面感
2. 突出双方的实力对比和心理变化
3. 适当加入环境互动
4. 字数控制在{word_count}字左右
5. 使用{tone}的文风',
'生成精彩的战斗场景，包含详细动作描写和环境互动',
'scene', '玄幻', '战斗',
'[{"name": "party_a", "type": "object", "required": true, "description": "甲方信息(姓名、实力、特点)"}, {"name": "party_b", "type": "object", "required": true, "description": "乙方信息"}, {"name": "battle_context", "type": "text", "required": true, "description": "战斗背景和原因"}, {"name": "environment", "type": "text", "required": true, "description": "战斗环境"}, {"name": "phase", "type": "string", "required": true, "description": "战斗阶段"}, {"name": "required_elements", "type": "array", "required": false, "description": "必须展现的元素"}, {"name": "style_requirements", "type": "text", "required": true, "description": "风格要求"}, {"name": "word_count", "type": "number", "required": true, "description": "目标字数"}, {"name": "tone", "type": "string", "required": true, "description": "文风基调"}]',
'active'
),
('character_profile', '人物档案生成',
'请根据以下信息生成详细的人物档案：

【人物姓名】
{name}

【人物角色】
{role}（主角/反派/配角/龙套）

【基础描述】
{basic_description}

【故事背景】
{story_background}

【人物关系】
{relationships}

请生成以下格式的人物档案：

## 基本信息
- 姓名：
- 年龄：
- 身份：
- 修为/能力等级：

## 外貌特征
（详细的视觉描写）

## 性格特点
- 主要性格：
- 优点：
- 缺点：
- 性格缺陷/成长点：

## 背景故事
（详细的出身和成长经历）

## 能力设定
- 主要能力：
- 技能列表：
- 特殊物品：

## 人物弧线
- 初始状态：
- 成长目标：
- 关键转折点：
- 最终状态：

## 经典台词
（3-5句符合人物性格的台词）',
'根据基础信息生成详细的人物档案，包含外貌、性格、背景、能力等',
'profile', null, null,
'[{"name": "name", "type": "string", "required": true, "description": "人物姓名"}, {"name": "role", "type": "string", "required": true, "description": "人物角色"}, {"name": "basic_description", "type": "text", "required": true, "description": "基础描述"}, {"name": "story_background", "type": "text", "required": true, "description": "故事背景"}, {"name": "relationships", "type": "array", "required": false, "description": "人物关系"}]',
'active'
),
('chapter_review', '章节审核',
'请对以下章节进行专业审核：

【章节正文】
{chapter_content}

【章节信息】
- 章节号：{chapter_no}
- 目标字数：{target_word_count}
- 本章目标：{chapter_goal}

【审核维度】
{review_dimensions}

【审核标准】
{review_criteria}

请输出以下格式的审核报告：

## 总体评分
（百分制）

## 各维度评分
1. 剧情连贯性：
2. 人物一致性：
3. 文笔质量：
4. 节奏控制：
5. 爽点/情绪点：

## 优点
（列出本章的优点）

## 问题列表
1. [严重程度] 问题描述 - 修改建议
2. ...

## 修改建议
（具体的修改建议）

## 是否符合设定
- 世界观一致性：
- 人物行为逻辑：
- 伏笔处理：',
'对章节进行多维度专业审核，输出详细的审核报告',
'review', null, null,
'[{"name": "chapter_content", "type": "text", "required": true, "description": "章节正文"}, {"name": "chapter_no", "type": "number", "required": true, "description": "章节号"}, {"name": "target_word_count", "type": "number", "required": true, "description": "目标字数"}, {"name": "chapter_goal", "type": "text", "required": true, "description": "本章目标"}, {"name": "review_dimensions", "type": "array", "required": true, "description": "审核维度"}, {"name": "review_criteria", "type": "text", "required": true, "description": "审核标准"}]',
'active'
);

-- ========================================
-- 3. 导入系统级模型配置
-- ========================================

INSERT INTO system_model_profiles
(profile_key, display_name, provider, model_name, task_types, default_params, cost_config, rate_limit_config, recommended_for, status)
VALUES
('creative_writing', '创意写作专用', 'anthropic', 'claude-3-5-sonnet-20241022',
 ARRAY['outline', 'draft', 'polish', 'review'],
 '{"temperature": 0.8, "max_tokens": 4000, "top_p": 0.9}',
 '{"input_cost_per_1k": 0.003, "output_cost_per_1k": 0.015, "currency": "USD"}',
 '{"requests_per_minute": 50, "tokens_per_minute": 100000, "concurrent_requests": 5}',
 '{"best_for": ["章节生成", "大纲创作", "文风润色"], "pros": ["创意丰富", "理解力强", "文笔优美"], "cons": ["成本较高", "速度较慢"], "suitable_genres": ["玄幻", "仙侠", "都市", "科幻"], "suitable_for": "追求高质量创作的项目"}',
'active'
),
('fast_generation', '快速生成专用', 'openai', 'gpt-4o-mini',
 ARRAY['outline', 'draft', 'context'],
 '{"temperature": 0.7, "max_tokens": 2000, "top_p": 0.95}',
 '{"input_cost_per_1k": 0.00015, "output_cost_per_1k": 0.0006, "currency": "USD"}',
 '{"requests_per_minute": 100, "tokens_per_minute": 200000, "concurrent_requests": 10}',
 '{"best_for": ["快速草稿", "大纲生成", "上下文准备"], "pros": ["速度极快", "成本低廉", "响应及时"], "cons": ["创意一般", "质量中等"], "suitable_genres": ["所有类型"], "suitable_for": "追求效率、快速迭代的项目"}',
'active'
),
('professional_review', '专业审核专用', 'anthropic', 'claude-3-opus-20240229',
 ARRAY['review', 'analysis'],
 '{"temperature": 0.3, "max_tokens": 8000, "top_p": 0.95}',
 '{"input_cost_per_1k": 0.015, "output_cost_per_1k": 0.075, "currency": "USD"}',
 '{"requests_per_minute": 20, "tokens_per_minute": 50000, "concurrent_requests": 2}',
 '{"best_for": ["质量审核", "问题诊断", "深度分析"], "pros": ["分析深入", "逻辑严谨", "建议专业"], "cons": ["成本极高", "速度最慢"], "suitable_genres": ["所有类型"], "suitable_for": "关键章节、重要节点的质量把关"}',
'active'
),
('local_backup', '本地模型备用', 'local', 'qwen2.5-72b-instruct',
 ARRAY['outline', 'draft', 'context'],
 '{"temperature": 0.7, "max_tokens": 4000, "top_p": 0.9}',
 '{"input_cost_per_1k": 0, "output_cost_per_1k": 0, "currency": "USD"}',
 '{"requests_per_minute": 30, "tokens_per_minute": 50000, "concurrent_requests": 3}',
 '{"best_for": ["离线写作", "隐私保护", "成本控制"], "pros": ["完全免费", "隐私安全", "无需联网"], "cons": ["质量波动", "需要本地部署"], "suitable_genres": ["所有类型"], "suitable_for": "注重隐私、成本敏感的项目"}',
'active'
);

-- ========================================
-- 4. 验证导入结果
-- ========================================

SELECT '文风档案' as type, COUNT(*) as count FROM system_style_profiles
UNION ALL
SELECT '提示词模板', COUNT(*) FROM system_prompt_templates
UNION ALL
SELECT '模型配置', COUNT(*) FROM system_model_profiles;

-- ========================================
-- Migration Complete
-- ========================================

SELECT 'Migration 221_system_evolution_seed completed successfully' as status;
