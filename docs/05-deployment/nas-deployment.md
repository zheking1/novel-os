# NAS 部署指南

## 服务器信息

| 项目 | 值 |
|------|-----|
| 主机 | `${NAS_HOST}` |
| SSH 用户 | `root` |
| SSH 密码 | `${NAS_SSH_PASSWORD}` |
| SSH 工具 | `plink` (PuTTY 命令行) |
| 文件复制 | `pscp` (PuTTY SCP) |

## 源文件目录

```
/opt/novel-os/
├── novel-os-web/          # 前端源文件
│   ├── index.html
│   ├── server.py
│   ├── js/
│   ├── css/
│   └── i18n/
├── novel-os-mcp/          # 后端源文件
│   ├── src/novel_os_mcp/
│   │   ├── tools/         # MCP 工具定义
│   │   ├── services/      # 业务服务
│   │   └── ...
│   └── Dockerfile
├── docker-compose.yml
├── docker-compose.app.example.yml
└── data/                  # 持久化数据卷
    ├── postgres/
    ├── qdrant/
    ├── projects/
    └── logs/
```

## 核心规则

1. **先上传源文件，再重建容器** — 容器重启会丢失非持久化文件
2. **使用 `docker compose`（v2）** — 不是 `docker-compose`
3. **JS 变更 → 重建 web 容器；MCP 变更 → 重建 MCP 容器**

## 部署命令

### 部署 JS 变更（单个文件）
```bash
pscp -pw "${NAS_SSH_PASSWORD}" js/pages/my-page.js root@${NAS_HOST}:/opt/novel-os/novel-os-web/js/pages/my-page.js
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web"
```

### 部署 JS 变更（整个 js/ 目录）
```bash
pscp -pw "${NAS_SSH_PASSWORD}" -r js/* root@${NAS_HOST}:/opt/novel-os/novel-os-web/js/
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web"
```

### 部署 MCP 变更（单个文件）
```bash
pscp -pw "${NAS_SSH_PASSWORD}" src/novel_os_mcp/tools/my_tool.py root@${NAS_HOST}:/opt/novel-os/novel-os-mcp/src/novel_os_mcp/tools/my_tool.py
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker build --no-cache -t novel-os-mcp:latest -f novel-os-mcp/Dockerfile novel-os-mcp/ && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d novel-os-mcp"
```

### 同时重建两个容器
```bash
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-mcp novel-os-web"
```

## 运维命令

### 查看容器状态
```bash
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
```

### 查看 Web 日志
```bash
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker logs novel-os-web 2>&1 | tail -30"
```

### 查看 MCP 日志
```bash
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker logs novel-os-mcp 2>&1 | tail -30"
```

### 检查 MCP 工具注册
```bash
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker logs novel-os-mcp 2>&1 | grep -E 'registering|tool' | tail -20"
```

## 数据库查询

PowerShell 引号问题导致不能内联 SQL，必须通过文件上传：

```bash
echo "SELECT id, template_key, name FROM prompt_templates;" > query.sql
pscp -pw "${NAS_SSH_PASSWORD}" query.sql root@${NAS_HOST}:/tmp/query.sql
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker exec -i novel-postgres psql -U novel_os -d novel_os -f /tmp/query.sql"
```

## 容器信息

| 容器名 | 镜像 | 端口 | 用途 |
|--------|------|------|------|
| `novel-postgres` | pgvector/pgvector:pg16 | 5432 | 数据库 |
| `novel-qdrant` | qdrant/qdrant:latest | 6333/6334 | 向量数据库 |
| `novel-os-mcp` | novel-os-mcp:latest | 8787 | MCP 后端 |
| `novel-os-web` | novel-os-web:latest | 8790 | Web 前端 |