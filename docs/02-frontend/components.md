# 可复用组件

> 全部 6 个组件，位于 `novel-os-web/js/components/`

---

## 1. ModalDialog

> 文件: `js/components/modal-dialog.js` (190行)

### 关键规则

**`show()` 不返回 boolean。** 必须使用 `onConfirm` 回调模式，并在回调内部调用 `ModalDialog.close()`。

```javascript
// 正确 ✅
ModalDialog.show({
  title: '确认删除',
  content: '<p>确定删除吗？</p>',
  onConfirm: async () => {
    await doDelete();
    ModalDialog.close();  // 必须在回调内手动关闭
  }
});

// 错误 ❌ — show() 不返回 true/false
const confirmed = ModalDialog.show({...});
if (confirmed) { ... }
```

### 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `id` | string | `'modal-' + Date.now()` | 模态框 DOM ID |
| `title` | string | `''` | 标题 |
| `content` | string | `''` | HTML 内容 |
| `size` | string | `'md'` | `'sm'/'md'/'lg'/'xl'` |
| `showClose` | boolean | `true` | 显示 X 关闭按钮 |
| `showFooter` | boolean | `true` | 显示底部按钮区 |
| `confirmText` | string | `t('common.confirm')` | 确认按钮文本 |
| `cancelText` | string | `t('common.cancel')` | 取消按钮文本 |
| `onConfirm` | function | `null` | **确认回调签名**: `async (modalId) => { ... ModalDialog.close(); }` |
| `onCancel` | function | `null` | 取消回调 |

### 快捷方法

```javascript
// 确认对话框
ModalDialog.confirm('确定删除吗？', async () => {
  await deleteItem();
});

// 信息提示
ModalDialog.alert('操作成功', 'success');  // type: info/success/warning/error

// 获取内容容器（用于动态填充）
ModalDialog.getContentContainer(modalId);
```

### 行为细节

- 同一时间只有一个模态框（新开会自动关旧）
- ESC 键关闭
- 点击背景遮罩关闭

---

## 2. DataTable

> 文件: `js/components/data-table.js` (138行)

### 用法

```javascript
DataTable.render({
  containerId: 'table-container',  // 容器元素 ID
  columns: [
    { key: 'name', header: '名称', width: '200px' },
    { key: 'status', header: '状态', type: 'badge', badgeClass: 'bg-green-100 text-green-700' },
    { key: 'description', header: '描述', type: 'truncate' },
    { key: 'tags', header: '标签', type: 'tags' },
    { key: 'order', header: '排序', type: 'order' }
  ],
  data: [{ name: '项目A', status: 'active', description: '...' }],
  actions: [
    { label: '编辑', icon: '✏️', onClick: "editItem", class: 'bg-blue-100 text-blue-700' },
    { label: '删除', icon: '🗑️', onClick: "deleteItem", class: 'bg-red-100 text-red-700' }
  ],
  emptyMessage: '暂无数据',
  onRowClick: null  // 'MyPage.handleRowClick' 字符串
});
```

### Column 类型

| type | 说明 | 渲染 |
|---|---|---|
| 默认 | 直接渲染值 | `value \|\| '-'` |
| `badge` | 状态徽章 | `<span class="px-2 rounded-full ...">value</span>` |
| `order` | 排序号 | `<span class="font-mono">value</span>` |
| `tags` | 标签数组 | 多个蓝色 tag |
| `truncate` | 长文本截断 | 超过 50 字符截断 + title 显示全量 |

### 嵌套值访问

支持点号路径: `key: 'user.name'` → `item.user.name`

---

## 3. Toast Container

> 文件: `js/components/toast-container.js` (83行)

Alpine 数据组件，集成到 Alpine store `app` 中。

### 快捷调用

```javascript
window.showToast(type, title, message, duration)
// type: 'success' | 'error' | 'warning' | 'info'
// duration: 默认 3000ms
```

### 样式

| type | 颜色 | 图标 |
|---|---|---|
| success | 绿色 `bg-green-500` | ✓ |
| error | 红色 `bg-red-500` | ✕ |
| warning | 黄色 `bg-yellow-500` | ⚠ |
| info | 蓝色 `bg-blue-500` | ℹ |

---

## 4. Loading Overlay

> 文件: `js/components/loading-overlay.js` (122行)

Alpine 数据组件，响应 `app:loading` 事件显示/隐藏全局遮罩。

包含三个子组件:
- `loadingOverlay` — 全局加载遮罩 (visible + message)
- `skeletonScreen` — 骨架屏占位（rows × columns 网格）
- `loadingButton` — 按钮加载态（`execute(fn, text)` 自动管理状态）

---

## 5. Form Builder

> 文件: `js/components/form-builder.js` (428行)

Alpine 数据组件 `formBuilder(config)`：

### 功能

- 字段类型: `text`, `textarea`, `number`, `select`, `checkbox`, `radio`
- 验证: `required`, `minLength`, `maxLength`, `min`, `max`, `pattern`, `validator` 自定义函数
- 脏跟踪: `dirty` 状态，`getChangedFields()` 返回变更字段
- 触摸状态: `blur()` 才显示验证错误
- 提交: `submit()` → 验证 → `onSubmit(model)` → 重置脏状态

### `window.formFieldTypes`

渲染辅助对象，根据字段类型生成 HTML 模板字符串。

---

## 6. Item Level

> 文件: `js/components/item-level.js` (78行)

Alpine 数据组件 `itemLevelManager`，用于管理分级配置（如重要度级别）。

基于 `setting.category` + `setting.item` API 的 CRUD 操作。表单包含: name, desc, order, range 四字段。