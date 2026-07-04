# Novel OS 部署配置指南

> 版本：v1.0
> 日期：2026-06-29
> 描述：完整的部署配置说明，包含 Docker Compose、环境变量、服务配置、备份恢复等

---

## 1. NAS 连接信息

| 项目 | 值 |
|------|------|
| **名称** | nas_u |
| **地址** | ${NAS_HOST} |
| **端口** | 22 |
| **用户** | root |
| **部署目录** | /opt/novel-os |
| **部署方式** | Docker Compose |

### 1.1 文件传输命令

```bash
# 从 Windows 传输文件到 NAS
pscp -pw "密码" "本地文件路径" root@${NAS_HOST}:/opt/novel-os/目标路径

# 示例：传输 Web 控制台
pscp -pw "密码" "novel-os-web\index.html" root@${NAS_HOST}:/opt/novel-os/novel-os-web/index.html

# 示例：传输 MCP 源代码
pscp -pw "密码" "novel-os-mcp\src\novel_os_mcp\services.py" root@${NAS_HOST}:/opt/novel-os/novel-os-mcp/src/novel_os_mcp/services.py
```

### 1.2 SSH 命令执行

```bash
# 执行远程命令（使用 -batch 避免交互提示）
plink -batch -pw "密码" root@${NAS_HOST} "cd /opt/novel-os && docker compose ps"

# 重建 MCP 容器（代码更新后需要重建镜像）
plink -batch -pw "密码" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-mcp"

# 重启容器（无需重建镜像时）
plink -batch -pw "密码" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml restart novel-os-mcp novel-os-web"
```

**注意**：
- MCP 容器使用镜像内置代码，代码更新后必须重建镜像 (`--build`)
- Web 控制台挂载宿主机目录，只需传输文件并重启容器即可

---

## 2. 架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Novel OS 部署架构                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                      Docker Network: novel_net                    │   │
│   │                                                                  │   │
│   │   ┌─────────────────┐    ┌─────────────────┐                     │   │
│   │   │  novel-os-mcp   │    │  novel-os-web   │                     │   │
│   │   │   (FastMCP)     │    │   (React)       │                     │   │
│   │   │   Port: 8787    │    │   Port: 8790    │                     │   │
│   │   └────────┬────────┘    └────────┬────────┘                     │   │
│   │            │                      │                               │   │
│   │            └──────────┬───────────┘                               │   │
│   │                       │                                           │   │
│   │   ┌─────────────────▼─────────────────┐                          │   │
│   │   │          PostgreSQL + pgvector     │                          │   │
│   │   │              Port: 5432           │                          │   │
│   │   └───────────────────────────────────┘                          │   │
│   │                                                                  │   │
│   │   ┌─────────────────────────────────────┐                        │   │
│   │   │            Qdrant (向量数据库)       │                        │   │
│   │   │       HTTP: 6333  GRPC: 6334        │                        │   │
│   │   └─────────────────────────────────────┘                        │   │
│   │                                                                  │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │              External Services (Host Network)                     │   │
│   │                                                                  │   │
│   │   ┌─────────────────┐                                           │   │
│   │   │     Redis       │  ← 复用现有的 Redis                        │   │
│   │   │   Port: 6379   │                                           │   │
│   │   └─────────────────┘                                           │   │
│   │                                                                  │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Docker Compose 配置

### 2.1 基础服务（必须）

**文件名**: `docker-compose.yml`

```yaml
version: "3.8"

services:
  # ========== PostgreSQL + pgvector ==========
  postgres:
    image: pgvector/pgvector:pg16
    container_name: novel-postgres
    restart: unless-stopped
    env_file:
      - .env
    environment:
      TZ: ${TZ}
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_BIND_ADDR}:${POSTGRES_PORT}:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10
    networks:
      - novel_net

  # ========== Qdrant 向量数据库 ==========
  qdrant:
    image: qdrant/qdrant:latest
    container_name: novel-qdrant
    restart: unless-stopped
    environment:
      TZ: ${TZ}
      QDRANT__SERVICE__API_KEY: ${QDRANT_API_KEY}
    ports:
      - "${QDRANT_BIND_ADDR}:${QDRANT_HTTP_PORT}:6333"
      - "${QDRANT_BIND_ADDR}:${QDRANT_GRPC_PORT}:6334"
    volumes:
      - ./data/qdrant:/qdrant/storage
    networks:
      - novel_net

networks:
  novel_net:
    name: novel_net
```

### 2.2 应用服务（必须）

**文件名**: `docker-compose.app.yml`

```yaml
version: "3.8"

services:
  # ========== MCP 服务 ==========
  novel-os-mcp:
    build:
      context: ./novel-os-mcp
      dockerfile: Dockerfile
    image: novel-os-mcp:latest
    container_name: novel-os-mcp
    restart: unless-stopped
    env_file:
      - .env
    environment:
      TZ: ${TZ}
      # 数据库配置
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      # Qdrant 配置
      QDRANT_URL: http://qdrant:6333
      QDRANT_API_KEY: ${QDRANT_API_KEY}
      QDRANT_MEMORY_COLLECTION: ${QDRANT_MEMORY_COLLECTION}
      QDRANT_REFERENCE_COLLECTION: ${QDRANT_REFERENCE_COLLECTION}
      # Redis 配置
      REDIS_URL: redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}
      REDIS_HOST: ${REDIS_HOST}
      REDIS_PORT: ${REDIS_PORT}
      REDIS_DB: ${REDIS_DB}
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      # MCP 配置
      NOVEL_PROJECTS_DIR: /app/projects
      NOVEL_OS_AUTH_MODE: ${NOVEL_OS_AUTH_MODE:-dev}
      NOVEL_OS_DEV_USER: ${NOVEL_OS_DEV_USER:-admin}
      NOVEL_OS_DEV_WORKSPACE: ${NOVEL_OS_DEV_WORKSPACE:-default}
      NOVEL_OS_DEV_SCOPES: ${NOVEL_OS_DEV_SCOPES:-admin,read,write}
      NOVEL_OS_HOST: 0.0.0.0
      NOVEL_OS_PORT: ${NOVEL_MCP_PORT:-8787}
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      # 上下文缓存配置
      CONTEXT_CACHE_TTL: 300
      CONTEXT_CACHE_MAX_SIZE: 1000
    ports:
      - "${NOVEL_MCP_BIND_ADDR:-127.0.0.1}:${NOVEL_MCP_PORT:-8787}:${NOVEL_MCP_PORT:-8787}"
    volumes:
      - ./data/projects:/app/projects
      - ./data/logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_started
    networks:
      - novel_net

  # ========== Web 控制台 ==========
  novel-os-web:
    build:
      context: ./novel-os-web
      dockerfile: Dockerfile
    image: novel-os-web:latest
    container_name: novel-os-web
    restart: unless-stopped
    environment:
      TZ: ${TZ}
      NOVEL_OS_WEB_HOST: 0.0.0.0
      NOVEL_OS_WEB_PORT: ${NOVEL_WEB_PORT:-8790}
      NOVEL_OS_MCP_URL: http://novel-os-mcp:${NOVEL_MCP_PORT:-8787}/mcp
      NOVEL_OS_WEB_DATA_DIR: /app/data
    ports:
      - "${NOVEL_WEB_BIND_ADDR:-127.0.0.1}:${NOVEL_WEB_PORT:-8790}:${NOVEL_WEB_PORT:-8790}"
    volumes:
      - ./data/web:/app/data
    depends_on:
      - novel-os-mcp
    networks:
      - novel_net

networks:
  novel_net:
    name: novel_net
    external: false
```

### 2.3 可选服务

**文件名**: `docker-compose.admin.yml`

```yaml
version: "3.8"

services:
  # ========== Adminer 数据库管理 ==========
  adminer:
    image: adminer:latest
    container_name: novel-adminer
    restart: unless-stopped
    profiles:
      - admin
    environment:
      TZ: ${TZ}
      ADMINER_DEFAULT_SERVER: postgres
    ports:
      - "${ADMINER_BIND_ADDR:-127.0.0.1}:${ADMINER_PORT:-8088}:8080"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - novel_net

  # ========== Redis Commander ==========
  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: novel-redis-commander
    restart: unless-stopped
    profiles:
      - admin
    environment:
      TZ: ${TZ}
      REDIS_HOSTS: local:redis:${REDIS_PORT}:0:${REDIS_PASSWORD}
    ports:
      - "${REDIS_BIND_ADDR:-127.0.0.1}:${REDISCommander_PORT:-8081}:8081"
    depends_on:
      - novel-os-mcp
    networks:
      - novel_net
```

---

## 3. 环境变量配置

### 3.1 环境变量文件

**文件名**: `.env`

```bash
# ============================================================================
# Novel OS 环境变量配置
# ============================================================================
# 复制此文件为 .env 并填入实际值
# 敏感信息（密码、API Key）只保存在 .env，不提交到 git
# ============================================================================

# ========== 项目标识 ==========
COMPOSE_PROJECT_NAME=novel-os
TZ=Asia/Shanghai

# NAS 根目录，所有数据都在此目录下
NAS_ROOT=/opt/novel-os

# ========== PostgreSQL + pgvector ==========
POSTGRES_BIND_ADDR=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=novel_os
POSTGRES_USER=novel_os
POSTGRES_PASSWORD=your_secure_postgres_password_here

# ========== Qdrant ==========
QDRANT_BIND_ADDR=127.0.0.1
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_API_KEY=your_secure_qdrant_api_key_here
QDRANT_MEMORY_COLLECTION=novel_memory_chunks
QDRANT_REFERENCE_COLLECTION=novel_reference_chunks

# ========== Redis（使用现有的 Redis） ==========
REDIS_HOST=${NAS_HOST}
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password_here

# ========== MCP 服务 ==========
NOVEL_MCP_BIND_ADDR=127.0.0.1
NOVEL_MCP_PORT=8787

# 认证模式：dev=开发模式（自动创建dev用户），prod=生产模式（需要真实认证）
NOVEL_OS_AUTH_MODE=dev

# 开发模式下的默认用户配置
NOVEL_OS_DEV_USER=admin
NOVEL_OS_DEV_WORKSPACE=default
NOVEL_OS_DEV_SCOPES=admin,read,write

# 日志级别：DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# ========== Web 控制台 ==========
NOVEL_WEB_BIND_ADDR=127.0.0.1
NOVEL_WEB_PORT=8790

# ========== 可选服务 ==========
ADMINER_BIND_ADDR=127.0.0.1
ADMINER_PORT=8088
REDISCommander_PORT=8081
```

### 3.2 环境变量说明

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `COMPOSE_PROJECT_NAME` | 否 | novel-os | Docker Compose 项目名称 |
| `TZ` | 否 | Asia/Shanghai | 时区 |
| `NAS_ROOT` | 是 | - | NAS 数据根目录 |
| `POSTGRES_*` | 是 | - | PostgreSQL 连接配置 |
| `QDRANT_*` | 是 | - | Qdrant 连接配置 |
| `REDIS_*` | 是 | - | Redis 连接配置 |
| `NOVEL_MCP_BIND_ADDR` | 否 | 127.0.0.1 | MCP 服务绑定地址 |
| `NOVEL_MCP_PORT` | 否 | 8787 | MCP 服务端口 |
| `NOVEL_OS_AUTH_MODE` | 否 | dev | 认证模式 |
| `NOVEL_OS_DEV_*` | 条件 | - | 开发模式用户配置 |
| `LOG_LEVEL` | 否 | INFO | 日志级别 |

---

## 4. 部署流程

### 4.1 首次部署

```bash
# 1. 创建目录结构
mkdir -p $NAS_ROOT/data/{postgres,qdrant,projects,logs,web}
mkdir -p $NAS_ROOT/postgres/init

# 2. 复制 SQL 迁移文件
cp novel-os-mcp/deploy/nas/postgres/init/*.sql $NAS_ROOT/postgres/init/

# 3. 创建 .env 文件
cp deploy/nas/.env.example $NAS_ROOT/.env
# 编辑 .env 填入实际值

# 4. 启动基础服务
cd $NAS_ROOT
docker compose -f docker-compose.yml up -d

# 5. 等待服务健康
docker compose ps

# 6. 启动应用服务
docker compose -f docker-compose.yml -f docker-compose.app.yml up -d

# 7. 验证服务
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8790
```

### 4.2 迁移执行

```bash
# SQL 迁移文件在 postgres/init 目录中，PostgreSQL 容器启动时自动执行
# 如需手动执行：
docker exec -it novel-postgres psql -U novel_os -d novel_os -f /docker-entrypoint-initdb.d/160_global_settings.sql
```

### 4.3 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker compose -f docker-compose.yml -f docker-compose.app.yml build

# 3. 滚动更新
docker compose -f docker-compose.yml -f docker-compose.app.yml up -d

# 4. 检查日志
docker compose -f docker-compose.yml -f docker-compose.app.yml logs -f
```

---

## 5. 备份与恢复

### 5.1 自动备份脚本

**文件名**: `backup-all.sh`

```bash
#!/bin/bash
# Novel OS 全量备份脚本
# 使用: ./backup-all.sh

set -e

BACKUP_DIR="${NAS_ROOT}/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="novel-os_${DATE}"

mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

echo "=== 开始备份 Novel OS ==="
echo "时间: ${DATE}"

# 1. 备份 PostgreSQL
echo "[1/4] 备份 PostgreSQL..."
docker exec novel-postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > "${BACKUP_DIR}/${BACKUP_NAME}/postgres.sql"
echo "      完成: postgres.sql"

# 2. 备份 Qdrant
echo "[2/4] 备份 Qdrant..."
docker exec novel-qdrant tar -czf - -C /qdrant/storage . > "${BACKUP_DIR}/${BACKUP_NAME}/qdrant.tar.gz"
echo "      完成: qdrant.tar.gz"

# 3. 备份配置文件
echo "[3/4] 备份配置文件..."
cp "${NAS_ROOT}/.env" "${BACKUP_DIR}/${BACKUP_NAME}/.env"
echo "      完成: .env"

# 4. 备份项目数据
echo "[4/4] 备份项目数据..."
if [ -d "${NAS_ROOT}/data/projects" ]; then
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/projects.tar.gz" -C "${NAS_ROOT}/data" projects
    echo "      完成: projects.tar.gz"
fi

# 5. 创建备份清单
cat > "${BACKUP_DIR}/${BACKUP_NAME}/manifest.json" << EOF
{
    "backup_date": "${DATE}",
    "components": [
        "postgres.sql",
        "qdrant.tar.gz",
        ".env",
        "projects.tar.gz"
    ]
}
EOF

# 6. 清理旧备份（保留最近 7 天）
find "${BACKUP_DIR}" -maxdepth 1 -type d -name "novel-os_*" -mtime +7 -exec rm -rf {} \;

echo ""
echo "=== 备份完成 ==="
echo "备份目录: ${BACKUP_DIR}/${BACKUP_NAME}"
ls -la "${BACKUP_DIR}/${BACKUP_NAME}/"
```

### 5.2 恢复流程

```bash
# 1. 停止服务
docker compose -f docker-compose.yml -f docker-compose.app.yml down

# 2. 恢复 PostgreSQL
docker exec -i novel-postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} < backup_file/postgres.sql

# 3. 恢复 Qdrant
docker exec novel-qdrant rm -rf /qdrant/storage/*
docker exec -i novel-qdrant tar -xzf - -C /qdrant/storage < backup_file/qdrant.tar.gz

# 4. 恢复项目数据（如需要）
tar -xzf backup_file/projects.tar.gz -C ${NAS_ROOT}/data

# 5. 恢复配置（如需要）
cp backup_file/.env ${NAS_ROOT}/.env

# 6. 重启服务
docker compose -f docker-compose.yml -f docker-compose.app.yml up -d

# 7. 验证
curl http://127.0.0.1:8787/health
```

---

## 6. 健康检查

### 6.1 健康检查脚本

**文件名**: `health-check.sh`

```bash
#!/bin/bash
# Novel OS 健康检查脚本

set -e

echo "=== Novel OS 健康检查 ==="
echo ""

# 检查 PostgreSQL
echo "[1] PostgreSQL..."
if docker exec novel-postgres pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} > /dev/null 2>&1; then
    echo "      ✓ PostgreSQL 正常"
else
    echo "      ✗ PostgreSQL 异常"
    exit 1
fi

# 检查 Qdrant
echo "[2] Qdrant..."
if curl -s -f http://127.0.0.1:${QDRANT_HTTP_PORT}/health > /dev/null 2>&1; then
    echo "      ✓ Qdrant 正常"
else
    echo "      ✗ Qdrant 异常"
    exit 1
fi

# 检查 MCP 服务
echo "[3] MCP 服务..."
if curl -s -f http://127.0.0.1:${NOVEL_MCP_PORT}/health > /dev/null 2>&1; then
    echo "      ✓ MCP 服务正常"
else
    echo "      ✗ MCP 服务异常"
    exit 1
fi

# 检查 Web 服务
echo "[4] Web 服务..."
if curl -s -f http://127.0.0.1:${NOVEL_WEB_PORT} > /dev/null 2>&1; then
    echo "      ✓ Web 服务正常"
else
    echo "      ✗ Web 服务异常"
    exit 1
fi

# 检查 Redis
echo "[5] Redis..."
if docker exec novel-os-mcp redis-cli -h ${REDIS_HOST} -p ${REDIS_PORT} -a ${REDIS_PASSWORD} ping > /dev/null 2>&1; then
    echo "      ✓ Redis 正常"
else
    echo "      ⚠ Redis 异常（可能不影响核心功能）"
fi

echo ""
echo "=== 检查完成 ==="
```

### 6.2 定时健康检查

```bash
# crontab 配置，每 5 分钟检查一次
*/5 * * * * /opt/novel-os/scripts/health-check.sh >> /opt/novel-os/logs/health-check.log 2>&1
```

---

## 7. 日志配置

### 7.1 日志目录

```
${NAS_ROOT}/
└── data/
    └── logs/
        ├── mcp/                    # MCP 服务日志
        │   ├── novel-os-mcp.log
        │   └── novel-os-mcp.err
        ├── web/                    # Web 服务日志
        │   └── novel-os-web.log
        └── health-check.log        # 健康检查日志
```

### 7.2 日志轮转

**文件名**: `logrotate.conf`

```
/opt/novel-os/data/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 root root
    sharedscripts
    postrotate
        docker compose -f /opt/novel-os/docker-compose.yml -f /opt/novel-os/docker-compose.app.yml restart novel-os-mcp novel-os-web > /dev/null 2>&1 || true
    endscript
}
```

---

## 8. 性能调优

### 8.1 PostgreSQL 优化

```sql
-- postgresql.conf 优化参数

# 连接数
max_connections = 100

# 内存
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 128MB

# 写入优化
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 1GB

# 并行查询
max_worker_processes = 4
max_parallel_workers_per_gather = 2

# 日志
log_statement = 'none'
log_min_duration_statement = 1000
```

### 8.2 Redis 优化

```bash
# redis.conf 关键参数

maxmemory 512mb
maxmemory-policy allkeys-lru
save ""
appendonly no
```

### 8.3 Qdrant 优化

```yaml
# qdrant.yaml
service:
  max_request_size_mb: 32

storage:
  # 优化存储性能
  hnsw_on_disk: true
  on_disk_payload: true
```

---

## 9. 故障排除

### 9.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| MCP 无法连接 PostgreSQL | 网络/密码错误 | 检查 .env 中的 POSTGRES_PASSWORD |
| Qdrant 返回 401 | API Key 不匹配 | 确认 .env 中 QDRANT_API_KEY 一致 |
| 上下文包生成超时 | 数据库查询慢 | 检查索引，清理冷数据 |
| Web 无法加载 | MCP 服务不可用 | 检查 MCP 健康状态 |

### 9.2 日志查看

```bash
# 查看 MCP 日志
docker compose -f docker-compose.yml -f docker-compose.app.yml logs -f novel-os-mcp

# 查看 PostgreSQL 日志
docker compose -f docker-compose.yml logs postgres

# 查看 Qdrant 日志
docker compose -f docker-compose.yml logs qdrant
```

---

## 10. 参考文档

- [.env.example](.env.example) - 环境变量模板
- [docker-compose.yml](docker-compose.yml) - 基础服务配置
- [docker-compose.app.example.yml](docker-compose.app.example.yml) - 应用服务配置
- [backup-all.sh](../scripts/backup-all.sh) - 备份脚本
- [health-check.sh](../scripts/health-check.sh) - 健康检查脚本
- [novel-os-requirements.md](../docs/novel-os-mcp/novel-os-requirements.md) - 需求规格
- [novel-os-development-plan.md](../docs/novel-os-mcp/novel-os-development-plan.md) - 开发计划
