# Novel OS MCP 部署与运维交接

更新时间：2026-06-27

## NAS 限定目录

用户明确要求：只能在 NAS 的以下目录操作：

```text
/opt/novel-os
```

不要修改 NAS 其他目录。nginx 配置文件位置仅用于了解反代：

```text
/home/docker/nginx/conf/conf.d/mcp.conf
```

除非用户重新授权，不要编辑 nginx 配置。

## 本地到 NAS 的路径映射

本地工作区：

```text
D:\Project\novels codex
```

NAS 工作区：

```text
/opt/novel-os
```

常见文件映射：

```text
novel-os-mcp/src/novel_os_mcp/main.py
  -> /opt/novel-os/novel-os-mcp/src/novel_os_mcp/main.py

novel-os-mcp/src/novel_os_mcp/services.py
  -> /opt/novel-os/novel-os-mcp/src/novel_os_mcp/services.py

deploy/nas/postgres/init/*.sql
  -> /opt/novel-os/postgres/init/*.sql

deploy/nas/scripts/*.sh
  -> /opt/novel-os/scripts/*.sh

docs/novel-os-mcp/*.md
  -> /opt/novel-os/docs/novel-os-mcp/*.md

novel-os-mcp/docs/*.md
  -> /opt/novel-os/novel-os-mcp/docs/*.md
```

## 容器

Compose 文件：

```text
/opt/novel-os/docker-compose.yml
/opt/novel-os/docker-compose.app.example.yml
```

服务：

```text
postgres       container novel-postgres
qdrant         container novel-qdrant
adminer        container novel-adminer, optional profile
novel-os-mcp   container novel-os-mcp
novel-os-web   container novel-os-web
```

端口默认：

```text
MCP: 127.0.0.1:8787 -> 8787
Web: 127.0.0.1:8790 -> 8790
PostgreSQL/Qdrant/Adminer 按 .env 绑定
```

不要把 `.env` 内容写进文档。所有 secret 从 NAS `.env` 读取。

## 重建 MCP

在 NAS 执行：

```sh
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-mcp
```

检查：

```sh
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml ps novel-os-mcp
docker logs novel-os-mcp --tail 100
```

## 重建 Web

在 NAS 执行：

```sh
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web
```

检查：

```sh
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml ps novel-os-web
docker logs novel-os-web --tail 100
```

## 应用 SQL 迁移

初始化目录：

```text
/opt/novel-os/postgres/init
```

已有脚本：

```text
/opt/novel-os/scripts/apply-schema.sh
```

一般流程：

```sh
cd /opt/novel-os
sh scripts/apply-schema.sh
```

如果新增迁移，请确保迁移可重复执行。

## Qdrant 初始化

已有脚本：

```text
/opt/novel-os/scripts/init-qdrant.sh
```

执行：

```sh
cd /opt/novel-os
set -a
. ./.env
set +a
sh scripts/init-qdrant.sh
```

集合：

```text
novel_memory_chunks
novel_reference_chunks
```

## 健康检查

已有脚本：

```sh
cd /opt/novel-os
sh scripts/health-check.sh
```

日志：

```sh
cd /opt/novel-os
sh scripts/logs-tail.sh novel-os-mcp
sh scripts/logs-tail.sh novel-os-web
```

## 备份

PostgreSQL 备份：

```sh
cd /opt/novel-os
set -a
. ./.env
set +a
PGPASSWORD="$POSTGRES_PASSWORD" sh ./scripts/backup-postgres.sh
```

完整备份：

```sh
cd /opt/novel-os
sh ./scripts/backup-all.sh
```

备份目录：

```text
/opt/novel-os/data/backups/postgres
```

## 冒烟测试

Phase 1：

```sh
cd /opt/novel-os
sh scripts/verify-phase1-schema.sh
sh scripts/verify-mcp-after-phase1.sh
```

Phase 2 单项：

```sh
cd /opt/novel-os
sh scripts/verify-phase2-state-tools.sh
sh scripts/verify-phase2-plot-tools.sh
sh scripts/verify-phase2-foreshadowing-tools.sh
sh scripts/verify-phase2-rules-tools.sh
sh scripts/verify-phase2-context-tools.sh
sh scripts/verify-phase2-sync-tools.sh
sh scripts/verify-phase2-review-learning-tools.sh
sh scripts/verify-phase2-compliance-tools.sh
```

Phase 2 组合：

```sh
cd /opt/novel-os
sh scripts/verify-phase2-state-tools.sh &&
sh scripts/verify-phase2-plot-tools.sh &&
sh scripts/verify-phase2-foreshadowing-tools.sh &&
sh scripts/verify-phase2-rules-tools.sh &&
sh scripts/verify-phase2-context-tools.sh &&
sh scripts/verify-phase2-sync-tools.sh &&
sh scripts/verify-phase2-review-learning-tools.sh &&
sh scripts/verify-phase2-compliance-tools.sh &&
docker compose -f docker-compose.yml -f docker-compose.app.example.yml ps novel-os-mcp
```

Phase 2.10 完成后应新增：

```text
scripts/verify-phase2-model-cost-tools.sh
```

并加入组合冒烟。

## 远程复制注意事项

新窗口如果需要复制文件到 NAS：

- 只复制到 `/opt/novel-os` 内对应路径。
- 不要在文档或最终回复中暴露 SSH 密码。
- 复制后需要重建容器才能生效。
- 只改脚本/文档时不一定需要重建容器。

## 回滚建议

当前没有完善自动发布回滚系统。出现严重问题时：

1. 停止继续写入。
2. 查看 `docker logs novel-os-mcp --tail 200`。
3. 如果是代码问题，复制上一版文件并重建 MCP。
4. 如果是 schema 问题，先备份数据库，再写兼容迁移修复。
5. 不使用破坏性 `DROP`、`TRUNCATE` 或重置数据，除非用户明确授权。

## 当前最近一次部署状态

2026-06-27，Phase 2.9 后部署成功：

```text
novel-os-mcp Up, 127.0.0.1:8787->8787/tcp
```

通过：

```text
phase2 state tools smoke ok
phase2 plot tools smoke ok
phase2 foreshadowing tools smoke ok
phase2 rules tools smoke ok
phase2 context tools smoke ok
phase2 sync tools smoke ok
phase2 review learning tools smoke ok
phase2 compliance tools smoke ok
```
