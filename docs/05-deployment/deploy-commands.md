# 部署命令速查

## 上传文件

```bash
# 单个 JS 页面
pscp -pw "${NAS_SSH_PASSWORD}" js/pages/xxx.js root@${NAS_HOST}:/opt/novel-os/novel-os-web/js/pages/

# 核心框架
pscp -pw "${NAS_SSH_PASSWORD}" js/core/api-client.js root@${NAS_HOST}:/opt/novel-os/novel-os-web/js/core/

# index.html
pscp -pw "${NAS_SSH_PASSWORD}" index.html root@${NAS_HOST}:/opt/novel-os/novel-os-web/index.html

# server.py
pscp -pw "${NAS_SSH_PASSWORD}" server.py root@${NAS_HOST}:/opt/novel-os/novel-os-web/server.py

# MCP 工具文件
pscp -pw "${NAS_SSH_PASSWORD}" src/novel_os_mcp/tools/xxx.py root@${NAS_HOST}:/opt/novel-os/novel-os-mcp/src/novel_os_mcp/tools/

# MCP 服务文件
pscp -pw "${NAS_SSH_PASSWORD}" src/novel_os_mcp/services/xxx.py root@${NAS_HOST}:/opt/novel-os/novel-os-mcp/src/novel_os_mcp/services/

# 整目录上传
pscp -pw "${NAS_SSH_PASSWORD}" -r js/* root@${NAS_HOST}:/opt/novel-os/novel-os-web/js/
```

## 重建容器

```bash
# 仅重建 Web（JS/CSS/HTML/server.py 变更）
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web"

# 仅重建 MCP（Python 变更）
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker build --no-cache -t novel-os-mcp:latest -f novel-os-mcp/Dockerfile novel-os-mcp/ && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d novel-os-mcp"

# 重建两者
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-mcp novel-os-web"

# 完全重启所有服务
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build"
```

## 查看状态

```bash
# 四个容器状态
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# MCP 日志（最近30行）
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker logs novel-os-mcp 2>&1 | tail -30"

# Web 日志
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker logs novel-os-web 2>&1 | tail -30"

# Postgres 日志
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker logs novel-postgres 2>&1 | tail -30"

# 检查 MCP 工具注册
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker logs novel-os-mcp 2>&1 | tail -5"

# 实时跟踪 MCP 日志
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker logs -f novel-os-mcp"
```

## 数据库操作

```bash
# 执行查询（必须通过文件，PowerShell 引号有问题）
echo "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;" > q.sql
pscp -pw "${NAS_SSH_PASSWORD}" q.sql root@${NAS_HOST}:/tmp/q.sql
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker exec -i novel-postgres psql -U novel_os -d novel_os -f /tmp/q.sql"

# 查看某表内容
echo "SELECT * FROM prompt_templates LIMIT 5;" > q.sql
pscp -pw "${NAS_SSH_PASSWORD}" q.sql root@${NAS_HOST}:/tmp/q.sql
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker exec -i novel-postgres psql -U novel_os -d novel_os -f /tmp/q.sql"

# 交互式 psql
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker exec -it novel-postgres psql -U novel_os -d novel_os"
```