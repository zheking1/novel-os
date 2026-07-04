# Novel OS NAS 运维手册

## 1. 基础信息

### 1.1 NAS服务器信息

| 属性 | 值 |
|------|-----|
| IP地址 | ${NAS_HOST} |
| SSH端口 | 22 |
| SSH用户 | root |
| SSH密码 | ${NAS_SSH_PASSWORD} |
| 部署目录 | /opt/novel-os |

### 1.2 数据库信息

| 属性 | 值 |
|------|-----|
| 类型 | PostgreSQL 16 + pgvector |
| 主机 | ${NAS_HOST}（容器内 localhost） |
| 端口 | 5432 |
| 数据库名 | novel_os |
| 用户名 | novel_os |
| 密码 | ${POSTGRES_PASSWORD} |

### 1.3 Redis信息

| 属性 | 值 |
|------|-----|
| 主机 | ${NAS_HOST} |
| 端口 | 6379 |
| 数据库 | 0 |
| 密码 | ${REDIS_PASSWORD} |

### 1.4 服务端口

| 服务 | 端口 | 说明 |
|------|-----|------|
| PostgreSQL | 5432 | 数据库 |
| Qdrant HTTP | 6333 | 向量数据库 |
| Qdrant GRPC | 6334 | 向量数据库 |
| Adminer | 8088 | 数据库管理（可选） |
| Novel OS MCP | 8787 | MCP服务 |
| Novel OS Web | 8790 | Web控制台 |

## 2. SSH连接方式

### 2.1 Windows PowerShell 连接

```powershell
# 方式1：使用Python paramiko脚本（推荐，自动处理密码）
python deploy/nas/nas_ssh.py "command"

# 方式2：手动SSH（需要交互输入密码）
ssh root@${NAS_HOST}
# 密码: ${NAS_SSH_PASSWORD}

# 方式3：SSH隧道（用于访问Adminer等本地服务）
ssh -L 8088:127.0.0.1:8088 root@${NAS_HOST}
```

### 2.2 常用命令

```bash
# 查看容器状态
docker compose ps

# 查看容器日志
docker compose logs -f novel-postgres
docker compose logs -f novel-os-mcp

# 进入PostgreSQL容器
docker exec -it novel-postgres psql -U novel_os -d novel_os

# 进入Redis容器
docker exec -it novel-os-redis redis-cli -a ${REDIS_PASSWORD}
```

## 3. 数据导入流程

### 3.1 数据源路径

```
/opt/novel-os/Github/webnovel-writer-opencode-master/.opencode/references/csv/
```

包含以下CSV文件：
- 金手指与设定.csv
- 人设与关系.csv
- 题材与调性推理.csv
- 桥段套路.csv
- 爽点与节奏.csv
- 场景写法.csv
- 写作技法.csv
- 命名规则.csv
- 裁决规则.csv

### 3.2 导入脚本

导入脚本位于：`deploy/nas/import_opencode_subcategory.py`

功能：
1. 清理旧的opencode数据
2. 读取CSV文件中的分类字段，自动创建子分类
3. 将数据分配到对应的细分子分类
4. 输出分类层级统计

### 3.3 执行导入

**方式1：使用Windows脚本**

```powershell
python deploy/nas/nas_deploy.py --import
```

**方式2：在NAS上直接执行**

```bash
# 登录NAS
ssh root@${NAS_HOST}

# 进入部署目录
cd /opt/novel-os

# 执行导入脚本
python3 deploy/nas/import_opencode_subcategory.py
```

**方式3：通过Docker exec执行**

```bash
cd /opt/novel-os
docker compose exec -T postgres python3 /opt/novel-os/deploy/nas/import_opencode_subcategory.py
```

### 3.4 分类映射关系

| CSV文件 | 一级分类slug | 一级分类名称 | 细分子分类示例 |
|---------|-------------|-------------|---------------|
| 金手指与设定.csv | skill | 术法技能 | 设定 |
| 人设与关系.csv | character | 角色人设 | 人设、配角、主角、反派、关系、快穿、种田等 |
| 写作技法.csv | writing_technique | 写作技法 | 结构、对话、伏笔、推理、战斗、场景等 |
| 桥段套路.csv | plot_archetype | 桥段套路 | 桥段 |
| 爽点与节奏.csv | pacing | 爽点节奏 | 节奏、快穿、仙侠、种田、历史等 |
| 场景写法.csv | scene_template | 场景模板 | 战斗、情感、对话、日常、竞技等 |
| 命名规则.csv | naming | 命名规范 | 书名、章节名、卷名、角色等 |
| 题材与调性推理.csv | genre_guide | 题材指南 | 题材路由 |
| 裁决规则.csv | genre_guide | 题材指南 | 裁决 |

### 3.5 PRESETS.md 数据导入

PRESETS.md 包含小说生成预设数据库，有23个章节的表格数据：

| 章节 | 数据库分类 | 数据量 |
|------|-----------|--------|
| 1.叙事结构类型 | narrative_structure | 12 |
| 2.核心冲突类型 | core_conflict | 8 |
| 3.世界观基调 | world_tone | 8 |
| 4.读者群体定位 | reader_groups | 6 |
| 5.故事复杂层级 | story_complexity | 5 |
| 6.叙事节奏模式 | pacing | 8 |
| 7.情感驱动力 | emotion_driver | 10 |
| 8.主题深度 | theme_depth | 6 |
| 9.40种题材分类 | genre_guide | 40 |
| 10.40种风格分类 | style_categories | 40 |
| 11.10种年代分类 | era_setting | 10 |
| 12.语言与视角 | language_choice | 11 |
| 13.100种角色身份职业 | identity_occupation | 100 |
| 14.10种发表平台风格 | platform_style | 10 |
| 15.7种预设文风 | writing_style | 7 |
| 16.50种标题结构 | title_structure | 50 |
| 17.金手指体系 | cheat_types | 52 |
| 18.100种男主人设预设 | male_protagonist | 100 |
| 19.100种女主人设预设 | female_protagonist | 100 |
| 20.100种反派人设预设 | antagonist | 100 |
| 21.300种情节模板 | plot_templates | 300 |
| 22.200种时空背景 | setting_background | 198 |
| 23.500种结局类型 | ending_types | 500 |

**执行PRESETS导入**

```powershell
python deploy/nas/nas_ssh.py presets_import
```

**验证PRESETS导入**

```powershell
python deploy/nas/nas_ssh.py presets_verify
```

## 4. 验证命令

### 4.1 查看分类层级结构

```sql
SELECT id, slug, name, parent_id, level 
FROM categories 
ORDER BY level, sort_order;
```

### 4.2 查看各分类数据统计

```sql
SELECT c.slug, c.name, c.level, COUNT(k.id) as count
FROM categories c
LEFT JOIN knowledge_base k ON k.category_id = c.id AND k.source = 'opencode'
GROUP BY c.id, c.slug, c.name, c.level
ORDER BY c.level, c.sort_order;
```

### 4.3 查看一级分类数据汇总

```sql
SELECT pc.slug, pc.name, COUNT(k.id) as count
FROM categories pc
LEFT JOIN categories sc ON sc.parent_id = pc.id
LEFT JOIN knowledge_base k ON k.category_id IN (pc.id, sc.id) AND k.source = 'opencode'
WHERE pc.level = 0
GROUP BY pc.id, pc.slug, pc.name
ORDER BY pc.sort_order;
```

### 4.4 查看总记录数

```sql
SELECT COUNT(*) FROM knowledge_base WHERE source = 'opencode';
```

## 5. 部署维护

### 5.1 启动服务

```bash
cd /opt/novel-os

# 启动基础服务（PostgreSQL + Qdrant）
docker compose up -d postgres qdrant

# 启动MCP和Web服务
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d

# 启动所有服务
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d
```

### 5.2 停止服务

```bash
docker compose stop
```

### 5.3 重启服务

```bash
docker compose restart
```

### 5.4 查看服务状态

```bash
# 查看容器状态
docker compose ps

# 健康检查
sh scripts/health-check.sh
```

### 5.5 日志查看

```bash
# 查看所有日志
docker compose logs -f

# 查看特定容器日志
docker compose logs -f novel-postgres
docker compose logs -f novel-os-mcp
docker compose logs -f novel-os-web
```

## 6. 备份与恢复

### 6.1 备份

```bash
# 备份PostgreSQL
sh scripts/backup-postgres.sh

# 备份所有数据（PostgreSQL + Qdrant）
sh scripts/backup-all.sh
```

### 6.2 备份路径

```
/opt/novel-os/data/backups/postgres/
```

## 7. 故障排查

### 7.1 数据库连接失败

```bash
# 检查PostgreSQL容器是否运行
docker compose ps postgres

# 检查PostgreSQL日志
docker compose logs novel-postgres

# 测试数据库连接
docker exec -it novel-postgres pg_isready -U novel_os -d novel_os
```

### 7.2 MCP服务无法启动

```bash
# 检查MCP日志
docker compose logs novel-os-mcp

# 检查数据库连接配置
cat .env | grep POSTGRES
```

### 7.3 数据导入失败

```bash
# 检查CSV文件是否存在
ls -la /opt/novel-os/Github/webnovel-writer-opencode-master/.opencode/references/csv/

# 检查文件编码
file /opt/novel-os/Github/webnovel-writer-opencode-master/.opencode/references/csv/*.csv

# 手动测试导入
cd /opt/novel-os
python3 deploy/nas/import_opencode_subcategory.py 2>&1 | head -100
```

## 8. 配置文件说明

### 8.1 .env 文件

```bash
# 复制模板创建
cp .env.example .env

# 需要修改的配置
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
QDRANT_API_KEY=your_api_key
REDIS_PASSWORD=${REDIS_PASSWORD}
```

### 8.2 Docker Compose 文件

| 文件 | 说明 |
|------|------|
| docker-compose.yml | 基础服务（PostgreSQL、Qdrant、Adminer） |
| docker-compose.app.example.yml | 应用服务（MCP、Web控制台） |

## 9. 安全注意事项

1. **不要提交.env文件到Git**，包含敏感信息
2. PostgreSQL、Qdrant、Adminer默认绑定127.0.0.1，仅必要时暴露到LAN
3. 定期备份数据库
4. 使用强密码
5. 不要给写入型Agent直接的PostgreSQL或文件系统访问权限