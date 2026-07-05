# Novel OS Web Client - API Conventions

## MCP Tool Naming

### Dots, Not Underscores
MCP tools use **dots** as separators:
```
prompt.template.upsert    ✓
prompt_template_upsert    ✗
model.profile.list        ✓
model_profile_list        ✗
```

### API Client Methods Use camelCase
```javascript
ApiClient.promptTemplate.list()    // calls prompt.template.list
ApiClient.modelProfile.create()    // calls model.profile.upsert
```

## Tool Parameter Conventions

### Required Parameters
Most tools require `workspace` and `project`:
```python
@mcp.tool(name="prompt.template.upsert")
async def prompt_template_upsert(
    workspace: str,    # Required
    project: str,      # Required for project-scoped tools
    template_key: str,
    ...
)
```

### Auto-Injected Project
The `api-client.js` auto-injects `project` from `AppState`:
```javascript
promptTemplate: {
  async list(workspace, filters = {}, options = {}) {
    const project = window.AppState?.currentProject;
    return ApiClient.callTool('prompt.template.list', { workspace, project, ...filters }, options);
  }
}
```

## Return Value Format

### Success Response
```python
return {"ok": True, "template_key": "my_template"}
```

### Error Response
```python
raise ValueError("Template not found")
# Caught by MCP framework, returned as error to client
```

### Delete Tool Pattern
Delete tools MUST return a dict (FastMCP constraint):
```python
# WRONG - causes "structured_content must be a dict or None" error
return await service.delete(project_id, key)  # Returns bool

# CORRECT
deleted = await service.delete(project_id, key)
return {"ok": deleted, "key": key}
```

## Frontend API Client

### Namespace Structure
```javascript
ApiClient = {
  workspace: { list, create, ... },
  project: { list, create, ... },
  setting: { category: { list, create, ... }, item: { list, create, ... } },
  genre: { list, create, ... },
  promptTemplate: { list, get, create, update, delete },
  modelProfile: { list, get, create, update },
  // ... more namespaces
}
```

### Common Methods
```javascript
// List
await ApiClient.promptTemplate.list(workspace, filters)

// Get
await ApiClient.promptTemplate.get(workspace, templateKey)

// Create
await ApiClient.promptTemplate.create(workspace, { name, template_key, ... })

// Update
await ApiClient.promptTemplate.update(workspace, templateKey, { name: 'new name' })

// Delete
await ApiClient.promptTemplate.delete(workspace, templateKey)
```

## Database Schema Notes

### Business Key vs UUID
- `id` = UUID (internal, not exposed to frontend)
- `template_key` = Business key (used in API calls, exposed to frontend)

Always use business keys for API operations, not UUIDs.

### is_system Flag
Some records have `is_system = TRUE` which prevents deletion:
```sql
DELETE FROM prompt_templates
WHERE project_id = $1 AND template_key = $2 AND is_system = FALSE
```
