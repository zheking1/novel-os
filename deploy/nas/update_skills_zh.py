import paramiko
import json

SSH_HOST = '${NAS_HOST}'
SSH_USER = 'root'
SSH_PASS = '${NAS_SSH_PASSWORD}'

SKILLS_ZH = [
    {
        "name": "novel-init",
        "description": "初始化新小说项目，包括本地目录、卷章结构和基本设置",
        "content": "# 小说项目初始化\n\n## 触发条件\n用户说\"初始化项目\"、\"新建小说\"、\"开始写小说\"\n\n## 步骤\n1. 注册项目 - 工具: local.project.register\n2. 扫描目录 - 工具: local.project.scan\n3. 创建卷 - 工具: volume.upsert\n4. 设置写作规则 - 工具: rules.upsert",
        "tags": ["initialize project", "new novel", "start writing", "初始化项目", "新建小说"],
    },
    {
        "name": "novel-write",
        "description": "生成单章完整流程（上下文准备→生成→记录→审核）",
        "content": "# 章节生成流程\n\n## 触发条件\n用户说\"写第X章\"、\"生成第X章\"\n\n## 工作流程\n1. 上下文准备: workflow.prepare_chapter_context\n2. 生成: Agent执行\n3. 记录: pipeline.record_pass\n4. 持久化: local.chapter.write\n5. 追踪: arc.record_emotion, causality.record",
        "tags": ["write chapter", "generate chapter", "写第X章", "生成章节", "写小说"],
    },
    {
        "name": "novel-batch",
        "description": "批量生成多章，支持断点续写",
        "content": "# 批量章节生成\n\n## 触发条件\n用户说\"批量生成\"、\"连续写10章\"\n\n## 工作流程\n1. 确定章节范围\n2. 逐章执行完整流程\n3. 每章保存断点\n4. 中断后可从断点恢复",
        "tags": ["batch generate", "write multiple chapters", "批量生成", "连续写", "批量写"],
    },
    {
        "name": "novel-review",
        "description": "13维度结构化章节质量审核",
        "content": "# 章节审核\n\n## 触发条件\n用户说\"审核第X章\"、\"检查质量\"\n\n## 13维度\n世界观一致性、角色OOC、剧情连续性、节奏、对话、描写、情感、悬念、伏笔兑现、世界构建、可读性、反AI检测、类型规范\n\n## 工作流程\n1. 读取章节: local.chapter.read\n2. 启动审核: review.start_job\n3. 提取经验: workflow.learn_from_review",
        "tags": ["review chapter", "check quality", "审查章节", "检查质量", "审稿"],
    },
    {
        "name": "novel-kb",
        "description": "知识库管理——添加角色、势力、地点和关系",
        "content": "# 知识库管理\n\n## 触发条件\n用户说\"添加角色\"、\"导入知识\"、\"添加势力\"\n\n## 实体类型\ncharacter(角色)、faction(势力)、location(地点)、item(物品)、concept(概念)\n\n## 工作流程\n1. 创建实体: kb.entity.create\n2. 添加关系: kb.relation.create\n3. 添加知识: kb.uk.create",
        "tags": ["add character", "import knowledge", "add entity", "添加角色", "导入知识", "添加势力"],
    },
    {
        "name": "novel-setting",
        "description": "配置世界规则、正典文档和写作约束",
        "content": "# 世界设定配置\n\n## 触发条件\n用户说\"设置世界观\"、\"配置规则\"\n\n## 工作流程\n1. 设置写作规则: rules.upsert\n2. 创建正典文档: canon.doc.upsert\n3. 配置类型规范\n4. 设置平台要求",
        "tags": ["set world rules", "configure world", "设置世界观", "配置规则", "编写设定"],
    },
    {
        "name": "novel-style",
        "description": "配置和分析写作风格指纹",
        "content": "# 写作风格配置\n\n## 触发条件\n用户说\"设置文风\"、\"配置写作风格\"\n\n## 工作流程\n1. 创建风格档案: style.create_profile\n2. 分析已有章节: style.analyze\n3. 监控风格漂移: style.detect_drift",
        "tags": ["set style", "configure writing style", "设置文风", "调整风格", "文风配置"],
    },
    {
        "name": "novel-foreshadow",
        "description": "埋设和管理伏笔元素",
        "content": "# 伏笔管理\n\n## 触发条件\n用户说\"埋伏笔\"、\"设置伏笔\"\n\n## 伏笔类型\nhint(暗示)、seed(铺垫)、red_herring(误导)、callback(回顾)\n\n## 工作流程\n1. 埋设伏笔: plot.upsert_foreshadowing\n2. 追踪伏笔: plot.list_foreshadowing\n3. 兑现伏笔: foreshadowing.payoff",
        "tags": ["plant foreshadowing", "add foreshadowing", "埋伏笔", "设置伏笔", "伏笔管理"],
    },
    {
        "name": "novel-arc",
        "description": "追踪角色弧光——情绪、关系、实力成长",
        "content": "# 角色弧光管理\n\n## 触发条件\n用户说\"记录角色变化\"、\"追踪弧光\"\n\n## 工作流程\n1. 记录情绪: arc.record_emotion\n2. 记录关系: arc.record_relationship\n3. 记录实力: arc.record_power\n4. 获取摘要: arc.get_summary_for_context",
        "tags": ["record character change", "track arc", "记录角色变化", "角色弧光", "追踪角色"],
    },
    {
        "name": "novel-pacing",
        "description": "节奏控制——张力曲线、呼吸空间、高潮时机",
        "content": "# 节奏控制\n\n## 触发条件\n用户说\"设置节奏\"、\"调整韵律\"\n\n## 工作流程\n1. 创建蓝图: pacing.create_blueprint\n2. 记录情绪: pacing.record_emotion\n3. 健康检查: pacing.check_health\n4. 查看曲线: pacing.get_curve",
        "tags": ["set pacing", "adjust rhythm", "设置节奏", "调整节奏", "节奏控制"],
    },
]

def update_skills():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS)
    
    for skill in SKILLS_ZH:
        content_escaped = skill["content"].replace("'", "''")
        desc_escaped = skill["description"].replace("'", "''")
        tags_escaped = [t.replace("'", "''") for t in skill["tags"]]
        tags_array = "ARRAY[" + ",".join(["'" + t + "'" for t in tags_escaped]) + "]"
        
        sql = f"""UPDATE skills SET description = '{desc_escaped}', content = '{content_escaped}', instruction = '{content_escaped}', tags = {tags_array}, updated_at = now() WHERE name = '{skill['name']}' AND scope = 'public' RETURNING id::text;"""
        
        sftp = ssh.open_sftp()
        with sftp.open('/tmp/update.sql', 'w') as f:
            f.write(sql)
        sftp.close()
        
        stdin, stdout, stderr = ssh.exec_command(
            "docker cp /tmp/update.sql novel-postgres:/tmp/update.sql && docker exec novel-postgres psql -U novel_os -d novel_os -t -f /tmp/update.sql"
        )
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        
        # Check for UUID in output
        if out and len([l for l in out.split('\n') if l.strip() and len(l.strip()) == 36]) > 0:
            print(f"OK: {skill['name']}")
        else:
            print(f"FAIL: {skill['name']}")
            if out: print(f"  out: {out[:100]}")
            if err: print(f"  err: {err[:100]}")
    
    ssh.close()
    print("\nDone!")

if __name__ == "__main__":
    update_skills()
