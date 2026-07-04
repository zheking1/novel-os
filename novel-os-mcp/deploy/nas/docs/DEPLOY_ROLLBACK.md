# Novel OS 发布与回滚流程

> 版本：v1.0
> 日期：2026-06-29
> 状态：正式运行

---

## 1. 发布前检查清单

### 1.1 代码检查
- [ ] 所有新增功能已通过单元测试
- [ ] 数据库迁移脚本可重复执行
- [ ] 新增的 MCP 工具已注册并测试
- [ ] 配置文件已更新（如需要）

### 1.2 备份
- [ ] 执行数据库全量备份
- [ ] 备份 docker-compose.yml 和配置文件
- [ ] 备份 Web 静态资源（如有修改）

### 1.3 通知
- [ ] 通知相关人员发布计划
- [ ] 确认回滚时间窗口

---

## 2. 标准发布流程

### 2.1 构建镜像
```bash
# 在开发机器执行
cd /opt/novel-os

# 拉取最新代码
git pull origin main

# 构建 MCP 镜像
docker compose build novel-os-mcp

# 构建 Web 镜像（如果有修改）
docker compose build novel-os-web
```

### 2.2 执行数据库迁移
```bash
# 检查待执行的迁移
docker exec novel-postgres psql -U novel_os -d novel_os -f /tmp/migrations/pending.sql --echo-queries

# 执行迁移（如有）
docker exec novel-postgres psql -U novel_os -d novel_os -f /tmp/migrations/<migration_name>.sql
```

### 2.3 滚动更新服务
```bash
# 重启 MCP 服务（不停服）
docker compose -f docker-compose.yml -f docker-compose.app.example.yml restart novel-os-mcp

# 重启 Web 服务
docker compose -f docker-compose.yml -f docker-compose.app.example.yml restart novel-os-web
```

### 2.4 验证
```bash
# 检查 MCP 服务健康
curl http://localhost:8787/health

# 检查 MCP 工具注册
curl http://localhost:8787/tools | grep -c "name"

# 检查 Web 服务
curl http://localhost:8080/health
```

---

## 3. 回滚流程（5 分钟）

### 3.1 快速回滚触发条件
- MCP 服务启动失败
- 数据库迁移失败
- 关键 MCP 工具不可用
- Web 页面无法加载

### 3.2 回滚步骤

#### 步骤 1：停止服务（30 秒）
```bash
cd /opt/novel-os

# 停止有问题的服务
docker compose -f docker-compose.yml -f docker-compose.app.example.yml stop novel-os-mcp
docker compose -f docker-compose.yml -f docker-compose.app.example.yml stop novel-os-web
```

#### 步骤 2：恢复代码（1 分钟）
```bash
# 回到上一个稳定版本
git reset --hard HEAD~1

# 重新构建
docker compose -f docker-compose.yml -f docker-compose.app.example.yml build novel-os-mcp
docker compose -f docker-compose.yml -f docker-compose.app.example.yml build novel-os-web
```

#### 步骤 3：恢复数据库（2 分钟）
```bash
# 如果迁移有问题，执行回滚
docker exec novel-postgres psql -U novel_os -d novel_os -f /tmp/rollback.sql

# 或者从备份恢复
docker exec novel-postgres psql -U novel_os -d novel_os < /backups/pre_deploy_backup.sql
```

#### 步骤 4：启动服务（1 分钟）
```bash
# 启动服务
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d novel-os-mcp
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d novel-os-web

# 验证
curl http://localhost:8787/health
```

### 3.3 回滚完成检查
- [ ] MCP 服务健康
- [ ] 关键 MCP 工具可用
- [ ] Web 页面正常访问
- [ ] 数据库连接正常

---

## 4. 迁移回滚

### 4.1 可重复执行原则
所有迁移脚本必须使用 `CREATE TABLE IF NOT EXISTS` 和 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`，确保可重复执行。

### 4.2 迁移回滚示例
```sql
-- 回滚添加的列
ALTER TABLE some_table DROP COLUMN IF EXISTS new_column;

-- 回滚创建的表（谨慎使用）
DROP TABLE IF EXISTS new_table;
```

---

## 5. 紧急回滚（极端情况）

如果上述流程无法解决问题：

### 5.1 使用快照回滚
```bash
# 如果 NAS 支持快照
# 在 NAS 管理界面选择回滚到发布前快照
```

### 5.2 完全重建
```bash
# 1. 停止所有服务
docker compose -f docker-compose.yml -f docker-compose.app.example.yml down

# 2. 恢复整个目录
git reset --hard HEAD~1
git clean -fdx

# 3. 恢复数据库
gunzip < /backups/full_backup.sql.gz | docker exec -i novel-postgres psql -U novel_os -d novel_os

# 4. 重新启动
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d
```

---

## 6. 联系方式

- 紧急联系人：[填写联系方式]
- 发布记录：[维护发布日志]

---

## 7. 发布检查清单（后）

发布成功后更新：
- [ ] 记录发布版本
- [ ] 更新部署文档
- [ ] 通知相关人员发布完成
- [ ] 观察监控指标 24 小时
