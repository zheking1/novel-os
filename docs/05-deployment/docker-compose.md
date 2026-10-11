# Docker Compose 配置详解

## 基础服务 (`docker-compose.yml`)

### PostgreSQL
```yaml
services:
  postgres:
    image: docker.1ms.run/pgvector/pgvector:pg16
    container_name: novel-postgres
    ports: ["${POSTGRES_BIND_ADDR}:${POSTGRES_PORT}:5432"]
    volumes:
      - ./data/postgres:/var/lib/postgresql/data          # 持久化数据
      - ./postgres/init:/docker-entrypoint-initdb.d:ro     # 初始化脚本（18个）
      - ./postgres/postgresql.conf:/etc/postgresql/...     # 配置
    command: postgres -c config_file=/etc/postgresql/postgresql.conf
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
    resources: {limits: {cpus: 1.0, memory: 2G}}
```

### Qdrant
```yaml
  qdrant:
    image: docker.1ms.run/qdrant/qdrant:latest
    container_name: novel-qdrant
    ports: ["${QDRANT_BIND_ADDR}:${QDRANT_HTTP_PORT}:6333", "...:${QDRANT_GRPC_PORT}:6334"]
    volumes: [./data/qdrant:/qdrant/storage]
    resources: {limits: {cpus: 1.0, memory: 3G}}
```

### Adminer (可选)
```yaml
  adminer:
    image: adminer:latest
    container_name: novel-adminer
    profiles: ["admin"]                                    # 需显式启用
    ports: ["${ADMINER_BIND_ADDR}:${ADMINER_PORT}:8080"]
```

## 应用服务 (`docker-compose.app.example.yml`)

### novel-os-mcp
```yaml
  novel-os-mcp:
    build:
      context: ./novel-os-mcp
      dockerfile: Dockerfile
    image: novel-os-mcp:latest
    container_name: novel-os-mcp
    ports: ["${NOVEL_MCP_BIND_ADDR}:${NOVEL_MCP_PORT}:8787"]
    volumes:
      - ./data/projects:/app/projects    # 项目管理
      - ./data/logs:/app/logs            # 日志
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      QDRANT_URL: http://qdrant:6333
      REDIS_URL: redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}
      NOVEL_OS_AUTH_MODE: ${NOVEL_OS_AUTH_MODE:-dev}
      NOVEL_OS_DEV_USER: admin
      NOVEL_OS_DEV_WORKSPACE: default
    depends_on:
      postgres: {condition: service_healthy}
      qdrant: {condition: service_started}
    resources: {limits: {cpus: 2.0, memory: 4G}}
```

### novel-os-web
```yaml
  novel-os-web:
    build:
      context: ./novel-os-web
      dockerfile: Dockerfile
    image: novel-os-web:latest
    container_name: novel-os-web
    ports: ["${NOVEL_WEB_BIND_ADDR}:${NOVEL_WEB_PORT}:8790"]
    volumes:
      - ./data/web:/app/data
      - ./novel-os-web/index.html:/app/index.html
    environment:
      NOVEL_OS_MCP_URL: http://novel-os-mcp:8787/mcp
    depends_on:
      novel-os-mcp: {condition: service_started}
    resources: {limits: {cpus: 0.5, memory: 512M}}
```

## 网络

```yaml
networks:
  novel_net:
    name: novel_net
    driver: bridge
    ipam:
      config: [{subnet: 172.20.0.0/16}]
```

## 启动命令

```bash
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d

# 含 Adminer
docker compose -f docker-compose.yml -f docker-compose.app.example.yml --profile admin up -d
```

## 依赖关系

```
postgres (healthy) ──┐
                      ├── novel-os-mcp ── novel-os-web
qdrant (started) ────┘
```

## 注意

- 源 Dockerfile 使用清华源 pip (`pypi.tuna.tsinghua.edu.cn`) 加速
- 基础镜像使用 `docker.1ms.run` 代理
- 容器内不能编辑文件，必须 mount 或 rebuild