# 部署凭证清单（模板）

> ⚠️ 本目录**只记录需要哪些凭证，不记录凭证的值**。
> 真实口令一律保存在仓库之外（`.env`、密码管理器或部署机环境），`.env` 已被 `.gitignore` 忽略。
> 如果你在本地保存了一份含真实值的清单，请确认它**不在**本仓库内。

## 需要准备的凭证

| 用途 | 变量名 | 存放位置 |
| --- | --- | --- |
| NAS / 部署机 SSH | `NAS_HOST`、`NAS_SSH_PASSWORD` | 本地 `~/.novel-os.env` |
| PostgreSQL | `POSTGRES_USER`、`POSTGRES_PASSWORD` | `deploy/nas/.env` |
| Qdrant | `QDRANT_API_KEY` | `deploy/nas/.env` |
| Redis | `REDIS_HOST`、`REDIS_PASSWORD` | `deploy/nas/.env` |
| LLM / Embedding | `api_url`、`api_key` | 数据库 `model_profiles` 表 |
| MCP 访问 Token | `apiKey` 请求头 | 数据库 `api_tokens` 表（SHA256 哈希存储） |

复制模板后填写：

```bash
cp deploy/nas/.env.example deploy/nas/.env
```

## 默认服务端口

| 服务 | 端口 | 默认绑定 |
| --- | --- | --- |
| Web 控制台 | 8790 | 127.0.0.1 |
| MCP | 8787 | 127.0.0.1 |
| PostgreSQL | 5432 | 127.0.0.1 |
| Qdrant HTTP / gRPC | 6333 / 6334 | 127.0.0.1 |
| Adminer（可选 profile） | 8088 | 127.0.0.1 |

## 认证

- `NOVEL_OS_AUTH_MODE=dev` — 免鉴权，仅用于本地试用
- `NOVEL_OS_AUTH_MODE=token` — 校验 `apiKey` / `Authorization: Bearer` 头，Token 以 SHA256 落库
- 作用域：`admin`、`read`、`write`

## 管理员

- 管理员名单默认在 `novel-os-web/server.py` 中定义，可通过环境变量覆盖
- 种子管理员的初始口令为 `123456`，**首次登录后必须立即修改**
- 口令哈希：bcrypt（`$2b$...`），兼容旧版 `pbkdf2_sha256`

## 安全基线

- 不要提交 `.env`
- 所有服务默认绑定 `127.0.0.1`，对外暴露请走 nginx + TLS
- 不要让写作 Agent 直连数据库或文件系统，一律经由 MCP 工具
