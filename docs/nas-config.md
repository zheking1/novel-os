# NAS 配置信息

> 注意：此文件包含敏感信息，请勿提交到Git仓库

## 连接信息

| 项目 | 值 |
|------|-----|
| 名称 | nas_u |
| 地址 | ${NAS_HOST} |
| 端口 | 22 |
| 用户 | root |
| 密码 | ${NAS_SSH_PASSWORD} |

## 部署目录

```
/opt/novel-os
```

## 常用命令

```bash
# 连接NAS
ssh root@${NAS_HOST}

# 复制文件到NAS
scp local_file root@${NAS_HOST}:/opt/novel-os/

# 重启服务
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml restart novel-os-mcp novel-os-web
```
