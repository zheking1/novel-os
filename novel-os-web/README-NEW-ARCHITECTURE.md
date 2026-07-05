# Novel OS Web Client - New Architecture

## 概述

这是一个完全重构的Web客户端架构，采用现代化的前端开发模式。

## 架构改进

### 1. 模块化设计

```
js/
├── core/              # 核心模块
│   ├── api-wrapper.js # API封装层
│   ├── store.js       # 全局状态管理
│   ├── router.js      # 路由管理
│   └── i18n.js        # 国际化
├── components/        # 通用组件
│   ├── data-table.js  # 数据表格
│   ├── modal-dialog.js # 模态框
│   ├── form-builder.js # 表单构建
│   └── ...
└── pages/             # 页面组件
    ├── story/         # 故事相关
    ├── worldbuilding/ # 世界设定
    ├── knowledge/     # 知识管理
    └── system/        # 系统管理
```

### 2. 技术栈

- **Alpine.js**: 轻量级响应式框架
- **Tailwind CSS**: 实用优先的CSS框架
- **原生ES6+**: 现代JavaScript特性

### 3. 新增功能

#### 通用组件
- **DataTable**: 支持排序、分页、过滤的表格
- **ModalDialog**: 可复用的模态框
- **FormBuilder**: 带验证的表单构建
- **ToastContainer**: 全局通知系统

#### 页面功能
- **物品等级管理**: 完整的CRUD功能
- **小说类型管理**: 增删改查
- **分类管理**: 带系统分类保护

#### UI/UX
- 响应式侧边栏（可折叠）
- 面包屑导航
- 加载状态指示
- 双语支持（中文/英文）

## 部署

### 本地测试

```bash
cd novel-os-web
python server.py
```

访问 http://localhost:8790

### Docker部署

```bash
docker-compose up -d --build novel-os-web
```

### NAS部署

```bash
# 在NAS上执行
cd /opt/novel-os
docker-compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web
```

## 开发指南

### 添加新页面

1. 在 `js/pages/` 下创建组件文件
2. 在 `router.js` 中添加路由配置
3. 在 `index.html` 中添加页面容器
4. 在语言包中添加翻译

### 使用通用组件

```javascript
// 使用DataTable
Alpine.data('myManager', () => ({
  ...dataTable({
    columns: [
      { field: 'name', label: '名称' },
      { field: 'actions', label: '操作', type: 'actions' }
    ],
    onLoad: async () => await apiClient.item.list(ws, catId)
  })
}));
```

## API调用

使用新的API封装层：

```javascript
// 获取分类列表
const categories = await apiClient.setting.list('default');

// 创建条目
await apiClient.item.upsert('default', {
  category_id: catId,
  core_summary: '名称',
  detailed_expansion: '描述'
});
```

## 国际化

添加新翻译：

```json
// i18n/zh.json
{
  "myFeature": {
    "title": "我的功能",
    "description": "功能描述"
  }
}
```

使用翻译：

```javascript
const title = i18n.t('myFeature.title');
```

## 文件变更

### 新增文件
- `js/core/api-wrapper.js` - API封装
- `js/core/store.js` - 状态管理
- `js/core/router.js` - 路由管理
- `js/core/i18n.js` - 国际化
- `js/components/*.js` - 通用组件
- `i18n/zh.json` - 中文语言包
- `i18n/en.json` - 英文语言包

### 修改文件
- `index.html` - 全新主入口
- `server.py` - 添加i18n支持
- `Dockerfile` - 添加i18n目录

### 备份文件
- `index.html.old` - 旧版主入口备份
- `index.html.backup.v2` - 备份

## 迁移计划

当前已完成：
- ✅ 基础架构
- ✅ 通用组件
- ✅ 物品等级管理
- ✅ 小说类型管理
- ✅ 分类管理

待完成：
- 🔄 Canon文档管理
- 🔄 实体管理
- 🔄 创作规则
- 🔄 情节线管理
- 🔄 系统管理

## 向后兼容性

- API接口保持不变
- 数据库结构不变
- 可以与旧版客户端共存（通过不同路由访问）

## 性能优化

- 按需加载页面组件
- API响应缓存
- 分类ID缓存
- 语言包异步加载

## 浏览器支持

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 许可证

与项目主许可证相同。
