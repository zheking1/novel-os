#!/usr/bin/env python3
"""
全量分析147个函数：提取每个函数的完整代码、分析目的和调用关系
输出到 JSON 和 Markdown 文档
"""
import re, json

with open('/opt/novel-os/novel-os-web/index.html.backup_20260704','r',encoding='utf-8') as f:
    c = f.read()

script_start = c.find('<script>') + 8
script_end = c.find('</script>', script_start)
sc = c[script_start:script_end]

# ===== Extract all functions with complete bodies =====
func_pattern = re.compile(
    r'(?:(?P<async>async)\s+)?function\s+(?P<name>\w+)\s*\((?P<params>[^)]*)\)\s*\{(?P<body>.*?)\n\s*\}',
    re.MULTILINE | re.DOTALL
)

functions = {}
for m in func_pattern.finditer(sc):
    name = m.group('name')
    body = m.group('body').strip()
    params = m.group('params')
    is_async = bool(m.group('async'))
    
    if not body: continue
    
    # Count nested braces to ensure complete match
    open_count = body.count('{')
    close_count = body.count('}')
    if open_count != close_count:
        # Incomplete match, try to find the complete function
        pos = sc.find(f'function {name}', m.start())
        if pos > 0:
            brace = sc.find('{', pos)
            depth = 1
            i = brace + 1
            while depth > 0 and i < len(sc):
                if sc[i] == '{': depth += 1
                elif sc[i] == '}': depth -= 1
                i += 1
            full_body = sc[brace+1:i-1]
            body = full_body.strip()
    
    # Analyze what functions this function calls
    called = set()
    for other_name in functions:
        if other_name in body:
            called.add(other_name)
    
    # Count lines
    lines = body.count('\n') + 1
    
    # Get first line of body as functional summary
    first_line = body.split('\n')[0].strip()
    
    functions[name] = {
        'name': name,
        'async': is_async,
        'params': params,
        'body_preview': body[:200],
        'body': body,
        'lines': lines,
        'calls': list(called),
    }

print(f'Extracted {len(functions)} functions')

# ===== Second pass: update caller relationships =====
for name in functions:
    functions[name]['called_by'] = []
    for other_name, other in functions.items():
        if other_name != name and name in other['body']:
            functions[name]['called_by'].append(other_name)

# Manual annotations for function purposes
purposes = {
    '$': 'DOM element getter by ID',
    'api': 'API fetch wrapper with error handling',
    'callTool': 'MCP tool call wrapper',
    'argsFor': 'Build MCP tool arguments',
    'escapeHtml': 'HTML entity escaping',
    'showToast': 'Toast notification display',
    'setStatus': 'Status bar message update',
    'show': 'Toggle element visibility',
    'showModal': 'Modal dialog display',
    'closeModal': 'Modal dialog close',
    't': 'Internationalization lookup',
    'applyLanguage': 'Language switcher',
    'updateTokenState': 'Update token state UI',
    'updateConnectionStatus': 'Update online/offline status',
    'parseJson': 'Parse JSON safely',
    'parseCsv': 'Parse CSV string',
    'renderMarkdown': 'Simple markdown to HTML',
    'buildTree': 'Build tree structure from flat list',
    'loadWorkspaces': 'Load workspace list from API',
    'loadProjects': 'Load project list from API', 
    'refreshAuth': 'Check auth state and update UI',
    'getActiveWorkspace': 'Get current workspace slug',
    'getActiveProjectArgs': 'Get active project arguments',
    'baseProjectArgs': 'Get base project API arguments',
    'updateProjectDropdowns': 'Update all project select dropdowns',
    'goToPage': 'Navigate to page by name',
    'setupMenuGroups': 'Setup menu accordion groups',
    'setupDropdown': 'Setup dropdown menu behavior',
    'closeAllDropdowns': 'Close all open dropdowns',
    'toggleSidebar': 'Toggle sidebar collapse',
    'loadModule': 'Load module/page content',
    'loadCanonDoc': 'Load canon document detail',
    'renderCanonList': 'Render canon document list',
    'loadEntityDetails': 'Load entity detail data',
    'renderEntityList': 'Render entity list',
    'renderRelationList': 'Render relationship list',
    'renderSnapshotList': 'Render state snapshot list',
    'loadState': 'Load entity state data',
    'saveState': 'Save entity state changes',
    'renderRulesResult': 'Render rules search result',
    'renderRuleProposals': 'Render rule proposals list',
    'renderThreads': 'Render plot threads',
    'renderVolumes': 'Render volumes list',
    'renderChapterPlans': 'Render chapter plans',
    'renderForeshadowingKanban': 'Render foreshadowing kanban board',
    'renderForeshadowingDetail': 'Render foreshadowing detail',
    'openForeshadowingDetail': 'Open foreshadowing detail view',
    'loadKnowledgeModule': 'Load knowledge module by page name',
    'loadKnowledgeList': 'Load knowledge item list',
    'loadKnowledgeStats': 'Load knowledge statistics',
    'loadKnowledgeCategories': 'Load knowledge categories tree',
    'loadKnowledgeMaintain': 'Load knowledge maintenance page',
    'loadKnowledgeItems': 'Load knowledge items for category',
    'loadKnowledgePack': 'Load project knowledge pack config',
    'loadKnowledgeGraphCategory': 'Load knowledge graph for category',
    'renderKnowledgeList': 'Render knowledge list',
    'renderKnowledgeItemList': 'Render knowledge item list',
    'renderKnowledgeItemDetail': 'Render knowledge item detail',
    'renderKnowledgeEditor': 'Render knowledge item editor',
    'renderKnowledgeListPagination': 'Render knowledge list pagination',
    'renderCategoryTree': 'Render category tree in sidebar',
    'renderTreeNode': 'Render single tree node',
    'renderCacheList': 'Render cache statistics list',
    'resetKnowledgeList': 'Reset knowledge list to default',
    'selectKnowledgeItemEdit': 'Select item for editing',
    'selectCategory': 'Select category in tree',
    'openCatManage': 'Open category management modal',
    'closeKnowledgeEditor': 'Close knowledge editor',
    'saveKnowledgeEditor': 'Save knowledge item from editor',
    'createNewKnowledgeItem': 'Create new knowledge item',
    'saveNewKnowledgeItem': 'Save new knowledge item',
    'deleteKnowledgeItemEdit': 'Delete knowledge item',
    'createPrivateCopy': 'Create private copy of public knowledge',
    'submitKnowledgeForReview': 'Submit knowledge for admin review',
    'saveKnowledgePack': 'Save knowledge pack config',
    'createKnowledgePack': 'Create new knowledge pack',
    'addCustomCategory': 'Add custom category to pack',
    'removeCustomCategory': 'Remove custom category from pack',
    'toggleCategory': 'Toggle category enabled/disabled',
    'loadCacheStats': 'Load cache statistics',
    'clearCache': 'Clear cache',
    'warmCache': 'Warm up cache',
    'loadMoreKnowledgeList': 'Load more knowledge items',
    'getAllChildSlugs': 'Get all child category slugs',
    'getNodeCount': 'Get tree node count',
    'init_auto_search': 'Initialize auto search page',
    'init_knowledge_graph': 'Initialize knowledge graph',
    'init_knowledge_expiry': 'Initialize knowledge expiry alerts',
    'initUkManage': 'Initialize UK manage page',
    'loadUkStats': 'Load UK statistics',
    'loadUkTree': 'Load UK category tree',
    'loadUkItems': 'Load UK items',
    'renderUkTree': 'Render UK tree view',
    'openUkEdit': 'Open UK item editor',
    'saveUkEntry': 'Save UK entry',
    'confirmDeleteCategory': 'Confirm category deletion',
    'renderPagination': 'Render pagination controls',
    'saveCategory': 'Save category changes',
    'loadReviewList': 'Load review list',
    'renderReviewList': 'Render review list',
    'renderReviewDetail': 'Render review detail panel',
    'selectReviewItem': 'Select review item to view',
    'approveReview': 'Approve review submission',
    'rejectReview': 'Reject review submission',
    'renderRevisionTasks': 'Render revision tasks',
    'renderCouncilConfigs': 'Render review council configs',
    'loadSystemHealth': 'Load system health check',
    'loadApiTokens': 'Load API token list',
    'loadBackupList': 'Load backup records',
    'saveBackupSchedule': 'Save backup schedule',
    'createBackup': 'Create new backup',
    'renderModelProfiles': 'Render model profile list',
    'renderOfflineQueue': 'Render offline sync queue',
    'renderMarketTemplates': 'Render prompt template marketplace',
    'init_model_profiles_fn': 'Init model profiles page',
    'init_model_cost_fn': 'Init model cost page',
    'init_template_list_fn': 'Init template list page',
    'loadMarketTemplates': 'Load marketplace templates',
    'renderTemplates': 'Render template list',
    'renderGraph': 'Render relationship graph',
    'loadSkillList': 'Load skill management list',
    'renderSkillList': 'Render skill list',
    'selectSkill': 'Select skill to view/edit',
    'saveSkill': 'Save skill changes',
    'deleteSkillConfirm': 'Confirm skill deletion',
    'deleteSkillExecute': 'Execute skill deletion',
    'openSkillEdit': 'Open skill editor modal',
    'init_skill_manage_fn': 'Init skill management page',
    'openStepEdit': 'Open skill step editor',
    'saveStep': 'Save skill step',
    'removeStep': 'Remove skill step',
    'renderStepList': 'Render skill step list',
    'loadLocalChapters': 'Load local chapters list',
    'readChapterContent': 'Read chapter content from local',
    'viewChapterDetail': 'View chapter detail',
    'loadChapterList': 'Load chapter list for project',
    'runPipeline': 'Run generation pipeline',
    'createPipelinePlan': 'Create pipeline plan',
    'loadPipelineStatus': 'Load pipeline status',
    'registerLocalProject': 'Register local project binding',
    'scanLocalProject': 'Scan local project directory',
    'scanProject': 'Scan project files',
    'viewProjectStats': 'View project statistics',
    'loadLocalProjects': 'Load local project list',
    'init': 'Application initialization entry point',
    'init_project_world_rules': 'Init project world rules page',
    'init_project_characters': 'Init project characters page',
    'init_project_factions': 'Init project factions page',
    'init_project_world_state': 'Init project world state page',
}

for name in functions:
    functions[name]['purpose'] = purposes.get(name, 'Unknown')

# ===== Write JSON =====
with open('/opt/novel-os/functions_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(functions, f, ensure_ascii=False, indent=2)
print('JSON written: functions_analysis.json')

# ===== Generate Markdown =====
md = '# Novel OS Web Client - 全量函数分析文档\n\n'
md += f'> 总计 {len(functions)} 个函数 | 自动生成于 2026-07-04\n\n'

# TOC
md += '## 目录\n\n'
for name in sorted(functions.keys()):
    md += f'- [{name}](#{name.lower()})\n'

md += '\n---\n\n'

# Module summary first
md += '## 模块概览\n\n'
md += '| 模块 | 函数数 | 文件 |\n'
md += '|------|--------|------|\n'

module_counts = {}
for name, func in functions.items():
    mod = 'uncategorized'
    if name.startswith('load') or name.startswith('render') or name.startswith('init_'):
        mod = name.split('_')[0] + '_*' if '_' in name else name
    module_counts.setdefault(mod, 0)
    module_counts[mod] += 1

for mod in sorted(module_counts.keys()):
    md += f'| {mod} | {module_counts[mod]} | |\n'

md += '\n---\n\n'

# Individual function docs
for name in sorted(functions.keys()):
    func = functions[name]
    md += f'## {name}\n\n'
    md += f'- **用途**: {func["purpose"]}\n'
    md += f'- **Async**: {"✅" if func["async"] else "❌"}\n'
    md += f'- **参数**: `({func["params"]})`\n'
    md += f'- **行数**: {func["lines"]}\n'
    md += f'- **调用**: {", ".join(func["calls"][:10]) or "无"}\n'
    md += f'- **被调用**: {", ".join(func["called_by"][:10]) or "无"}\n'
    md += '\n```javascript\n'
    md += f'function {name}({func["params"]}) {{\n  {func["body"][:500]}...\n}}'
    md += '\n```\n\n'
    md += '---\n\n'

with open('/opt/novel-os/novel-os-web/docs/functions-analysis.md', 'w', encoding='utf-8') as f:
    f.write(md)
print(f'Docs written: {len(md)} chars')

# ===== Print module suggestions =====
print('\n=== Suggested Module Split ===')
print('1. js/app.js (core): $, api, escapeHtml, showToast, setStatus, showModal, closeModal, t, applyLanguage')
print('2. js/auth.js: loadWorkspaces, loadProjects, refreshAuth, baseProjectArgs, getActiveProjectArgs')
print('3. js/menu.js: goToPage, setupMenuGroups, setupDropdown, toggleSidebar, loadModule')
print('4. js/pages/canon.js: loadCanonDoc, renderCanonList')
print('5. js/pages/entities.js: 6 functions')
print('6. js/pages/rules.js: 2 functions')
print('7. js/pages/plot.js: 6 functions')
print('8. js/pages/knowledge.js: 48 functions (largest)')
print('9. js/pages/review.js: 8 functions')
print('10. js/pages/system.js: 25 functions')
print('11. js/pages/local.js: 12 functions')
print('12. js/pages/init.js: 7 functions')