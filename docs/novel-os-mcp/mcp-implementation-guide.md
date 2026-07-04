# MCP 工具实现规范

> 版本：v1.0
> 日期：2026-06-28
> 描述：定义 Service 层和 MCP 工具的实现规范，包含 GlobalSettingsService 实现模板

---

## 1. 架构模式总览

```
┌─────────────────────────────────────────────────────────────────┐
│  MCP 工具层 (main.py)                                          │
│  - @mcp.tool() 装饰器注册                                      │
│  - 参数校验、权限检查、Service 调用                              │
│  - 返回结构化响应                                                │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌───────────────────────────▼─────────────────────────────────────┐
│  Service 层 (services.py)                                      │
│  - 业务逻辑处理                                                  │
│  - 数据库操作                                                    │
│  - 返回字典/列表                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            ↓
┌───────────────────────────▼─────────────────────────────────────┐
│  Database 层 (db.py)                                           │
│  - 连接池管理                                                    │
│  - SQL 执行                                                     │
│  - fetchrow / fetch / execute                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Service 层实现规范

### 2.1 Service 类结构

```python
class <Entity>Service:
    """<实体>服务类"""
    
    def __init__(self, db: Database):
        self._db = db
    
    # ========== 查询类方法 ==========
    
    async def list_<entities>(
        self,
        project_id: str,
        filters: dict | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """列出<实体>列表"""
        # 1. 构建查询条件
        conditions = ["project_id = $1"]
        params = [project_id]
        param_idx = 2
        
        # 2. 动态添加过滤条件
        if filters:
            if filters.get("status"):
                conditions.append(f"status = ${param_idx}")
                params.append(filters["status"])
                param_idx += 1
        
        # 3. 执行查询
        where_clause = " AND ".join(conditions)
        rows = await self._db.fetch(
            f"""
            SELECT id::text, name, status, created_at, updated_at
            FROM <table_name>
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """,
            *params,
            limit,
            offset,
        )
        
        # 4. 转换并返回
        return rows_to_dicts(rows)
    
    async def get_<entity>(
        self,
        project_id: str,
        entity_id: str | None = None,
        **identifiers,
    ) -> dict | None:
        """获取单个<实体>"""
        # 根据 ID 或其他标识符查询
        ...
    
    # ========== 写入类方法 ==========
    
    async def upsert_<entity>(
        self,
        project_id: str,
        username: str,
        **fields,
    ) -> dict:
        """创建或更新<实体>"""
        # 1. 验证必填字段
        if not fields.get("name"):
            raise ValueError("name is required")
        
        # 2. 执行 upsert
        row = await self._db.fetchrow(
            """
            INSERT INTO <table_name> (project_id, name, ..., created_by, updated_by)
            VALUES ($1, $2, ..., $N, $N+1, $N+1)
            ON CONFLICT (project_id, unique_key) 
            DO UPDATE SET 
                name = EXCLUDED.name,
                ...,
                updated_by = EXCLUDED.updated_by,
                updated_at = now()
            RETURNING id::text, name, ..., created_at, updated_at
            """,
            project_id,
            fields["name"],
            ...,  # 其他字段
            username,
        )
        
        return row_to_dict(row)
    
    async def delete_<entity>(
        self,
        project_id: str,
        entity_id: str,
    ) -> dict:
        """删除<实体>"""
        row = await self._db.fetchrow(
            """
            DELETE FROM <table_name>
            WHERE id = $1 AND project_id = $2
            RETURNING id::text
            """,
            entity_id,
            project_id,
        )
        
        if not row:
            raise ValueError(f"<Entity> not found: {entity_id}")
        
        return {"id": row["id"], "deleted": True}
```

### 2.2 数据库辅助函数

```python
# utils.py 中的辅助函数

def row_to_dict(row) -> dict:
    """将单行结果转为字典"""
    if row is None:
        return None
    return {k: v for k, v in row.items()}


def rows_to_dicts(rows) -> list[dict]:
    """将多行结果转为字典列表"""
    return [row_to_dict(row) for row in rows]


def ensure_json_value(value) -> Any:
    """确保 JSON 字段的值是正确类型"""
    if isinstance(value, str):
        text = value.strip()
        if text.startswith(("{", "[")):
            try:
                import json
                return json.loads(text)
            except Exception:
                return value
    return value
```

### 2.3 错误处理规范

```python
class ServiceError(Exception):
    """服务层异常基类"""
    def __init__(self, code: str, message: str, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class NotFoundError(ServiceError):
    """资源不存在"""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} not found: {identifier}",
        )


class ValidationError(ServiceError):
    """验证错误"""
    def __init__(self, field: str, reason: str):
        super().__init__(
            code="VALIDATION_ERROR",
            message=f"Validation failed: {field}",
            details={"field": field, "reason": reason},
        )
```

---

## 3. MCP 工具注册规范

### 3.1 工具函数结构

```python
@mcp.tool(name="<domain>.<action>")
async def <domain>_<action>(
    # === 路径参数（必填）===
    workspace: str,
    project: str,
    
    # === 查询参数（可选）===
    status: str | None = None,
    query: str | None = None,
    limit: int = 100,
    offset: int = 0,
    
    # === 业务参数 ===
    name: str | None = None,
    content: str | None = None,
    **kwargs,
) -> dict[str, Any]:
    """
    工具描述...
    
    Args:
        workspace: 工作区 slug
        project: 项目 slug
        status: 状态过滤
        ...
    
    Returns:
        结构化响应
    """
    # 1. 连接数据库（每个工具都要）
    await db.connect()
    
    # 2. 获取当前用户身份
    principal = await auth.current_principal()
    
    # 3. 权限检查
    principal.require("read")   # 查询类工具
    # 或
    principal.require("write")  # 写入类工具
    
    # 4. 解析项目 ID（会自动检查 workspace 访问权限）
    project_id = await auth.resolve_project_id(workspace, project, principal)
    # 或
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    
    # 5. 调用 Service
    result = await <service>.<method>(
        project_id=project_id,
        username=principal.username,
        # ... 其他参数
    )
    
    # 6. 返回结果
    return result
```

### 3.2 权限检查模式

| 权限 | 说明 | 适用场景 |
|------|------|---------|
| `principal.require("read")` | 读取权限 | list, get, search |
| `principal.require("write")` | 写入权限 | upsert, create, update, delete |
| `principal.require("admin")` | 管理员权限 | 用户管理、工作区管理 |

### 3.3 响应格式规范

```python
# 成功响应
{
    "id": "uuid",
    "name": "xxx",
    "status": "active",
    "created_at": "2026-01-01T00:00:00Z",
    # ... 业务字段
}

# 列表响应
[
    {"id": "uuid1", "name": "xxx1", ...},
    {"id": "uuid2", "name": "xxx2", ...},
]

# 错误响应（通过异常）
raise ValueError("Invalid status")  # 会自动转为结构化错误
raise NotFoundError("Entity", "id") # 会自动转为 404
```

---

## 4. GlobalSettingsService 实现模板

### 4.1 Service 类实现

```python
class GlobalSettingsService:
    """全局设定服务"""
    
    def __init__(self, db: Database):
        self._db = db
    
    # ========== 分类管理 ==========
    
    async def list_categories(
        self,
        workspace_id: str,
        is_active: bool | None = True,
    ) -> list[dict]:
        """列出设定分类"""
        rows = await self._db.fetch(
            """
            SELECT 
                id::text, 
                name, 
                slug, 
                description,
                icon,
                sort_order,
                is_active,
                is_standard,
                created_at,
                updated_at
            FROM setting_categories
            WHERE workspace_id = $1
                AND ($2::boolean IS NULL OR is_active = $2)
            ORDER BY sort_order, name
            """,
            workspace_id,
            is_active,
        )
        return rows_to_dicts(rows)
    
    async def get_category(
        self,
        workspace_id: str,
        category_id: str | None = None,
        slug: str | None = None,
    ) -> dict | None:
        """获取分类详情（含字段定义）"""
        if not category_id and not slug:
            raise ValueError("category_id or slug is required")
        
        if category_id:
            row = await self._db.fetchrow(
                """
                SELECT id::text, name, slug, description, icon, sort_order, 
                       is_active, is_standard, metadata, created_at, updated_at
                FROM setting_categories
                WHERE id = $1 AND workspace_id = $2
                """,
                category_id,
                workspace_id,
            )
        else:
            row = await self._db.fetchrow(
                """
                SELECT id::text, name, slug, description, icon, sort_order, 
                       is_active, is_standard, metadata, created_at, updated_at
                FROM setting_categories
                WHERE slug = $1 AND workspace_id = $2
                """,
                slug,
                workspace_id,
            )
        
        if not row:
            return None
        
        result = row_to_dict(row)
        
        # 加载字段定义
        fields = await self._db.fetch(
            """
            SELECT 
                id::text,
                field_name,
                field_key,
                field_type,
                options,
                is_required,
                is_searchable,
                default_value,
                placeholder,
                help_text,
                sort_order
            FROM setting_field_definitions
            WHERE category_id = $1
            ORDER BY sort_order
            """,
            row["id"],
        )
        result["field_definitions"] = rows_to_dicts(fields)
        
        return result
    
    async def upsert_category(
        self,
        workspace_id: str,
        slug: str,
        name: str,
        username: str,
        description: str | None = None,
        icon: str = "📁",
        sort_order: int = 0,
        is_standard: bool = False,
        metadata: dict | None = None,
    ) -> dict:
        """创建或更新分类"""
        # 标准分类不能被删除（但可以更新）
        if is_standard:
            # 检查是否已存在
            existing = await self._db.fetchrow(
                "SELECT id FROM setting_categories WHERE slug = $1 AND workspace_id = $2",
                slug,
                workspace_id,
            )
            if existing:
                # 更新现有标准分类
                row = await self._db.fetchrow(
                    """
                    UPDATE setting_categories
                    SET name = $3, description = $4, icon = $5, sort_order = $6, metadata = $7, updated_at = now()
                    WHERE id = $1 AND workspace_id = $2
                    RETURNING id::text, name, slug, description, icon, sort_order, is_active, is_standard, created_at, updated_at
                    """,
                    existing["id"],
                    workspace_id,
                    name,
                    description,
                    icon,
                    sort_order,
                    json.dumps(metadata or {}),
                )
                return row_to_dict(row)
        
        # 创建新分类
        row = await self._db.fetchrow(
            """
            INSERT INTO setting_categories (
                workspace_id, slug, name, description, icon, sort_order, is_standard, metadata,
                created_by, updated_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)
            ON CONFLICT (workspace_id, slug) 
            DO UPDATE SET 
                name = EXCLUDED.name,
                description = COALESCE(EXCLUDED.description, setting_categories.description),
                icon = EXCLUDED.icon,
                sort_order = EXCLUDED.sort_order,
                metadata = EXCLUDED.metadata,
                updated_by = EXCLUDED.updated_by,
                updated_at = now()
            RETURNING id::text, name, slug, description, icon, sort_order, is_active, is_standard, created_at, updated_at
            """,
            workspace_id,
            slug,
            name,
            description,
            icon,
            sort_order,
            is_standard,
            json.dumps(metadata or {}),
            username,
        )
        return row_to_dict(row)
    
    async def delete_category(
        self,
        workspace_id: str,
        category_id: str,
    ) -> dict:
        """删除分类（标准分类不可删除）"""
        # 检查是否是标准分类
        row = await self._db.fetchrow(
            "SELECT is_standard FROM setting_categories WHERE id = $1 AND workspace_id = $2",
            category_id,
            workspace_id,
        )
        
        if not row:
            raise ValueError(f"Category not found: {category_id}")
        
        if row["is_standard"]:
            # 标准分类改为隐藏，不删除
            await self._db.execute(
                """
                UPDATE setting_categories SET is_active = FALSE, updated_at = now()
                WHERE id = $1
                """,
                category_id,
            )
            return {"id": category_id, "deleted": False, "reason": "standard_category_hidden"}
        
        # 删除分类（字段定义会级联删除）
        await self._db.execute(
            "DELETE FROM setting_categories WHERE id = $1 AND workspace_id = $2",
            category_id,
            workspace_id,
        )
        
        return {"id": category_id, "deleted": True}
    
    # ========== 设定项目管理 ==========
    
    async def list_items(
        self,
        workspace_id: str,
        category_id: str | None = None,
        is_global: bool | None = None,
        level: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """列出设定项目"""
        conditions = ["(workspace_id = $1 OR is_global = TRUE)"]
        params = [workspace_id]
        param_idx = 2
        
        if category_id:
            conditions.append(f"category_id = ${param_idx}")
            params.append(category_id)
            param_idx += 1
        
        if is_global is not None:
            conditions.append(f"is_global = ${param_idx}")
            params.append(is_global)
            param_idx += 1
        
        if level:
            conditions.append(f"level = ${param_idx}")
            params.append(level)
            param_idx += 1
        
        where_clause = " AND ".join(conditions)
        
        rows = await self._db.fetch(
            f"""
            SELECT 
                id::text,
                category_id::text,
                item_code,
                core_summary,
                detailed_expansion,
                ai_instruction,
                level,
                is_global,
                keywords,
                intent_synonyms,
                poison_points,
                applicable_skills,
                applicable_genres,
                tags,
                sort_order,
                created_at,
                updated_at
            FROM setting_items
            WHERE {where_clause}
            ORDER BY sort_order, created_at DESC
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """,
            *params,
            limit,
            offset,
        )
        return rows_to_dicts(rows)
    
    async def get_item(
        self,
        workspace_id: str,
        item_id: str | None = None,
        item_code: str | None = None,
    ) -> dict | None:
        """获取设定项目详情"""
        if not item_id and not item_code:
            raise ValueError("item_id or item_code is required")
        
        if item_id:
            row = await self._db.fetchrow(
                """
                SELECT 
                    id::text,
                    category_id::text,
                    workspace_id::text,
                    item_code,
                    keywords,
                    intent_synonyms,
                    core_summary,
                    detailed_expansion,
                    ai_instruction,
                    poison_points,
                    level,
                    applicable_skills,
                    applicable_genres,
                    data,
                    tags,
                    is_global,
                    sort_order,
                    metadata,
                    created_at,
                    updated_at
                FROM setting_items
                WHERE id = $1 AND (workspace_id = $2 OR is_global = TRUE)
                """,
                item_id,
                workspace_id,
            )
        else:
            row = await self._db.fetchrow(
                """
                SELECT 
                    id::text,
                    category_id::text,
                    workspace_id::text,
                    item_code,
                    keywords,
                    intent_synonyms,
                    core_summary,
                    detailed_expansion,
                    ai_instruction,
                    poison_points,
                    level,
                    applicable_skills,
                    applicable_genres,
                    data,
                    tags,
                    is_global,
                    sort_order,
                    metadata,
                    created_at,
                    updated_at
                FROM setting_items
                WHERE workspace_id = $1 AND item_code = $2
                """,
                workspace_id,
                item_code,
            )
        
        return row_to_dict(row)
    
    async def upsert_item(
        self,
        workspace_id: str,
        category_id: str,
        username: str,
        core_summary: str,
        item_code: str | None = None,
        keywords: list[str] | None = None,
        intent_synonyms: list[str] | None = None,
        detailed_expansion: str | None = None,
        ai_instruction: str | None = None,
        poison_points: list[str] | None = None,
        level: str = "knowledge",
        applicable_skills: list[str] | None = None,
        applicable_genres: list[str] | None = None,
        data: dict | None = None,
        tags: list[str] | None = None,
        is_global: bool = True,
        sort_order: int = 0,
        metadata: dict | None = None,
    ) -> dict:
        """创建或更新设定项目"""
        # 生成 item_code 如果未提供
        if not item_code:
            count = await self._db.fetchval(
                "SELECT COUNT(*) FROM setting_items WHERE category_id = $1",
                category_id,
            )
            item_code = f"GS-{count + 1:04d}"
        
        row = await self._db.fetchrow(
            """
            INSERT INTO setting_items (
                category_id, workspace_id, item_code,
                keywords, intent_synonyms, core_summary, detailed_expansion,
                ai_instruction, poison_points,
                level, applicable_skills, applicable_genres,
                data, tags, is_global, sort_order, metadata,
                created_by, updated_by
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $18)
            ON CONFLICT (workspace_id, item_code) 
            DO UPDATE SET 
                category_id = EXCLUDED.category_id,
                keywords = EXCLUDED.keywords,
                intent_synonyms = EXCLUDED.intent_synonyms,
                core_summary = EXCLUDED.core_summary,
                detailed_expansion = EXCLUDED.detailed_expansion,
                ai_instruction = EXCLUDED.ai_instruction,
                poison_points = EXCLUDED.poison_points,
                level = EXCLUDED.level,
                applicable_skills = EXCLUDED.applicable_skills,
                applicable_genres = EXCLUDED.applicable_genres,
                data = EXCLUDED.data,
                tags = EXCLUDED.tags,
                is_global = EXCLUDED.is_global,
                sort_order = EXCLUDED.sort_order,
                metadata = EXCLUDED.metadata,
                updated_by = EXCLUDED.updated_by,
                updated_at = now()
            RETURNING id::text, item_code, category_id::text, core_summary, level, is_global, created_at, updated_at
            """,
            category_id,
            workspace_id,
            item_code,
            keywords or [],
            intent_synonyms or [],
            core_summary,
            detailed_expansion,
            ai_instruction,
            poison_points or [],
            level,
            applicable_skills or [],
            applicable_genres or [],
            json.dumps(data or {}),
            tags or [],
            is_global,
            sort_order,
            json.dumps(metadata or {}),
        )
        return row_to_dict(row)
    
    async def delete_item(
        self,
        workspace_id: str,
        item_id: str,
    ) -> dict:
        """删除设定项目"""
        row = await self._db.fetchrow(
            """
            DELETE FROM setting_items
            WHERE id = $1 AND workspace_id = $2 AND is_global = FALSE
            RETURNING id::text
            """,
            item_id,
            workspace_id,
        )
        
        if not row:
            raise ValueError(f"Setting item not found or cannot be deleted: {item_id}")
        
        return {"id": row["id"], "deleted": True}
    
    # ========== BM25 检索 ==========
    
    async def bm25_search(
        self,
        workspace_id: str,
        query: str,
        category_id: str | None = None,
        level: str | None = None,
        skill: str | None = None,
        genre: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """BM25 智能检索"""
        # 调用数据库函数
        rows = await self._db.fetch(
            """
            SELECT * FROM fn_setting_items_bm25_search(
                $1, $2, $3, $4, $5, $6, $7, $8
            )
            """,
            query,
            workspace_id,
            category_id,
            level,
            skill,
            genre,
            limit,
            offset,
        )
        return rows_to_dicts(rows)
    
    # ========== 题材规范化 ==========
    
    async def resolve_genre(self, input_text: str) -> list[dict]:
        """题材规范化解析"""
        rows = await self._db.fetch(
            "SELECT * FROM fn_genre_resolve($1)",
            input_text,
        )
        return rows_to_dicts(rows)
    
    async def list_genres(self) -> list[dict]:
        """列出所有 canonical genre"""
        rows = await self._db.fetch(
            "SELECT * FROM v_genre_canonical_list ORDER BY canonical_genre"
        )
        return rows_to_dicts(rows)
    
    # ========== CSV 导入导出 ==========
    
    async def csv_import(
        self,
        workspace_id: str,
        category_id: str,
        username: str,
        csv_content: str,
    ) -> dict:
        """CSV 导入"""
        import csv
        import io
        
        # 解析 CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        imported = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):
            try:
                await self.upsert_item(
                    workspace_id=workspace_id,
                    category_id=category_id,
                    username=username,
                    item_code=row.get("item_code"),
                    core_summary=row.get("core_summary", ""),
                    keywords=self._parse_array(row.get("keywords")),
                    intent_synonyms=self._parse_array(row.get("intent_synonyms")),
                    detailed_expansion=row.get("detailed_expansion"),
                    ai_instruction=row.get("ai_instruction"),
                    poison_points=self._parse_array(row.get("poison_points")),
                    applicable_skills=self._parse_array(row.get("applicable_skills")),
                    applicable_genres=self._parse_array(row.get("applicable_genres")),
                    level=row.get("level", "knowledge"),
                    tags=self._parse_array(row.get("tags")),
                    is_global=True,
                )
                imported += 1
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})
        
        return {
            "imported": imported,
            "errors": errors,
            "total": imported + len(errors),
        }
    
    async def csv_export(
        self,
        workspace_id: str,
        category_id: str | None = None,
    ) -> str:
        """CSV 导出"""
        import csv
        import io
        
        conditions = ["(workspace_id = $1 OR is_global = TRUE)"]
        params = [workspace_id]
        
        if category_id:
            conditions.append("category_id = $2")
            params.append(category_id)
        
        where_clause = " AND ".join(conditions)
        
        rows = await self._db.fetch(
            f"""
            SELECT 
                item_code,
                keywords,
                intent_synonyms,
                core_summary,
                detailed_expansion,
                ai_instruction,
                poison_points,
                level,
                applicable_skills,
                applicable_genres,
                tags
            FROM setting_items
            WHERE {where_clause}
            ORDER BY item_code
            """,
            *params,
        )
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "item_code", "keywords", "intent_synonyms", "core_summary",
            "detailed_expansion", "ai_instruction", "poison_points",
            "level", "applicable_skills", "applicable_genres", "tags"
        ])
        
        for row in rows:
            writer.writerow([
                row["item_code"],
                "|".join(row["keywords"] or []),
                "|".join(row["intent_synonyms"] or []),
                row["core_summary"],
                row["detailed_expansion"],
                row["ai_instruction"],
                "|".join(row["poison_points"] or []),
                row["level"],
                "|".join(row["applicable_skills"] or []),
                "|".join(row["applicable_genres"] or []),
                "|".join(row["tags"] or []),
            ])
        
        return output.getvalue()
    
    def _parse_array(self, value: str | None, delimiter: str = "|") -> list[str]:
        """解析数组字符串"""
        if not value:
            return []
        return [v.strip() for v in value.split(delimiter) if v.strip()]
```

---

## 5. MCP 工具注册（main.py）

```python
# 在 main.py 中添加
from .services import GlobalSettingsService

# 初始化服务
global_settings_service = GlobalSettingsService(db)

# ========== 全局设定工具 ==========

@mcp.tool(name="setting.category.list")
async def setting_category_list(
    workspace: str,
    is_active: bool = True,
) -> list[dict[str, Any]]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("read")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.list_categories(
        workspace_id=workspace_id,
        is_active=is_active,
    )


@mcp.tool(name="setting.category.get")
async def setting_category_get(
    workspace: str,
    category_id: str | None = None,
    slug: str | None = None,
) -> dict[str, Any]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("read")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    result = await global_settings_service.get_category(
        workspace_id=workspace_id,
        category_id=category_id,
        slug=slug,
    )
    if not result:
        raise ValueError(f"Category not found")
    return result


@mcp.tool(name="setting.category.upsert")
async def setting_category_upsert(
    workspace: str,
    slug: str,
    name: str,
    description: str | None = None,
    icon: str = "📁",
    sort_order: int = 0,
    is_standard: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("write")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.upsert_category(
        workspace_id=workspace_id,
        slug=slug,
        name=name,
        username=principal.username,
        description=description,
        icon=icon,
        sort_order=sort_order,
        is_standard=is_standard,
        metadata=metadata,
    )


@mcp.tool(name="setting.category.delete")
async def setting_category_delete(
    workspace: str,
    category_id: str,
) -> dict[str, Any]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("write")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.delete_category(
        workspace_id=workspace_id,
        category_id=category_id,
    )


@mcp.tool(name="setting.item.list")
async def setting_item_list(
    workspace: str,
    category_id: str | None = None,
    is_global: bool | None = None,
    level: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("read")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.list_items(
        workspace_id=workspace_id,
        category_id=category_id,
        is_global=is_global,
        level=level,
        limit=limit,
        offset=offset,
    )


@mcp.tool(name="setting.item.get")
async def setting_item_get(
    workspace: str,
    item_id: str | None = None,
    item_code: str | None = None,
) -> dict[str, Any]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("read")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    result = await global_settings_service.get_item(
        workspace_id=workspace_id,
        item_id=item_id,
        item_code=item_code,
    )
    if not result:
        raise ValueError(f"Setting item not found")
    return result


@mcp.tool(name="setting.item.upsert")
async def setting_item_upsert(
    workspace: str,
    category_id: str,
    core_summary: str,
    item_code: str | None = None,
    keywords: list[str] | None = None,
    intent_synonyms: list[str] | None = None,
    detailed_expansion: str | None = None,
    ai_instruction: str | None = None,
    poison_points: list[str] | None = None,
    level: str = "knowledge",
    applicable_skills: list[str] | None = None,
    applicable_genres: list[str] | None = None,
    data: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    is_global: bool = True,
    sort_order: int = 0,
) -> dict[str, Any]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("write")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.upsert_item(
        workspace_id=workspace_id,
        category_id=category_id,
        username=principal.username,
        item_code=item_code,
        core_summary=core_summary,
        keywords=keywords,
        intent_synonyms=intent_synonyms,
        detailed_expansion=detailed_expansion,
        ai_instruction=ai_instruction,
        poison_points=poison_points,
        level=level,
        applicable_skills=applicable_skills,
        applicable_genres=applicable_genres,
        data=data,
        tags=tags,
        is_global=is_global,
        sort_order=sort_order,
    )


@mcp.tool(name="setting.item.bulk_upsert")
async def setting_item_bulk_upsert(
    workspace: str,
    category_id: str,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("write")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    
    created = 0
    updated = 0
    errors = []
    
    for i, item in enumerate(items):
        try:
            result = await global_settings_service.upsert_item(
                workspace_id=workspace_id,
                category_id=category_id,
                username=principal.username,
                **item,
            )
            if result.get("created_at") == result.get("updated_at"):
                created += 1
            else:
                updated += 1
        except Exception as e:
            errors.append({"index": i, "error": str(e)})
    
    return {
        "created": created,
        "updated": updated,
        "errors": errors,
    }


@mcp.tool(name="setting.item.delete")
async def setting_item_delete(
    workspace: str,
    item_id: str,
) -> dict[str, Any]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("write")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.delete_item(
        workspace_id=workspace_id,
        item_id=item_id,
    )


@mcp.tool(name="setting.search")
async def setting_search(
    workspace: str,
    query: str,
    category_id: str | None = None,
    level: str | None = None,
    skill: str | None = None,
    genre: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("read")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.bm25_search(
        workspace_id=workspace_id,
        query=query,
        category_id=category_id,
        level=level,
        skill=skill,
        genre=genre,
        limit=limit,
        offset=offset,
    )


@mcp.tool(name="setting.genre.resolve")
async def setting_genre_resolve(
    input_text: str,
) -> list[dict[str, Any]]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("read")
    return await global_settings_service.resolve_genre(input_text=input_text)


@mcp.tool(name="setting.genre.list")
async def setting_genre_list() -> list[dict[str, Any]]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("read")
    return await global_settings_service.list_genres()


@mcp.tool(name="setting.csv.import")
async def setting_csv_import(
    workspace: str,
    category_id: str,
    csv_content: str,
) -> dict[str, Any]:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("write")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.csv_import(
        workspace_id=workspace_id,
        category_id=category_id,
        username=principal.username,
        csv_content=csv_content,
    )


@mcp.tool(name="setting.csv.export")
async def setting_csv_export(
    workspace: str,
    category_id: str | None = None,
) -> str:
    await db.connect()
    principal = await auth.current_principal()
    principal.require("read")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.csv_export(
        workspace_id=workspace_id,
        category_id=category_id,
    )
```

---

## 6. 验证清单

新增 GlobalSettingsService 后，验证以下内容：

- [ ] 数据库连接正常
- [ ] 分类 CRUD 操作正常
- [ ] 设定项目 CRUD 操作正常
- [ ] BM25 检索返回相关结果
- [ ] 题材规范化正确匹配
- [ ] CSV 导入导出正常
- [ ] 权限检查生效
- [ ] 工作区隔离正确

---

## 7. 参考文档

- [novel-os-requirements.md](novel-os-requirements.md) - 需求规格说明书
- [novel-os-development-plan.md](novel-os-development-plan.md) - 开发计划
- [160_global_settings.sql](../deploy/nas/postgres/init/160_global_settings.sql) - 全局设定系统 SQL
- [services.py](../novel-os-mcp/src/novel_os_mcp/services.py) - Service 层参考实现
- [main.py](../novel-os-mcp/src/novel_os_mcp/main.py) - MCP 工具注册参考
