# Novel OS Web Client - 全量函数分析文档

> 总计 145 个函数 | 自动生成于 2026-07-04

## 目录

- [addCustomCategory](#addcustomcategory)
- [api](#api)
- [applyLanguage](#applylanguage)
- [approveReview](#approvereview)
- [argsFor](#argsfor)
- [baseProjectArgs](#baseprojectargs)
- [buildTree](#buildtree)
- [callTool](#calltool)
- [clearCache](#clearcache)
- [closeAllDropdowns](#closealldropdowns)
- [closeKnowledgeEditor](#closeknowledgeeditor)
- [confirmDeleteCategory](#confirmdeletecategory)
- [createBackup](#createbackup)
- [createKnowledgePack](#createknowledgepack)
- [createNewKnowledgeItem](#createnewknowledgeitem)
- [createPipelinePlan](#createpipelineplan)
- [createPrivateCopy](#createprivatecopy)
- [deleteKnowledgeItemEdit](#deleteknowledgeitemedit)
- [deleteSkillConfirm](#deleteskillconfirm)
- [deleteSkillExecute](#deleteskillexecute)
- [escapeHtml](#escapehtml)
- [getActiveProjectArgs](#getactiveprojectargs)
- [getActiveWorkspace](#getactiveworkspace)
- [getAllChildSlugs](#getallchildslugs)
- [getNodeCount](#getnodecount)
- [goToPage](#gotopage)
- [init](#init)
- [initUkManage](#initukmanage)
- [init_auto_search](#init_auto_search)
- [init_knowledge_expiry](#init_knowledge_expiry)
- [init_knowledge_graph](#init_knowledge_graph)
- [init_model_cost_fn](#init_model_cost_fn)
- [init_model_profiles_fn](#init_model_profiles_fn)
- [init_project_characters](#init_project_characters)
- [init_project_factions](#init_project_factions)
- [init_project_world_rules](#init_project_world_rules)
- [init_project_world_state](#init_project_world_state)
- [init_skill_manage_fn](#init_skill_manage_fn)
- [init_template_list_fn](#init_template_list_fn)
- [loadApiTokens](#loadapitokens)
- [loadBackupList](#loadbackuplist)
- [loadCacheStats](#loadcachestats)
- [loadCanonDoc](#loadcanondoc)
- [loadChapterList](#loadchapterlist)
- [loadEntityDetails](#loadentitydetails)
- [loadKnowledgeCategories](#loadknowledgecategories)
- [loadKnowledgeGraphCategory](#loadknowledgegraphcategory)
- [loadKnowledgeItems](#loadknowledgeitems)
- [loadKnowledgeList](#loadknowledgelist)
- [loadKnowledgeMaintain](#loadknowledgemaintain)
- [loadKnowledgeModule](#loadknowledgemodule)
- [loadKnowledgePack](#loadknowledgepack)
- [loadKnowledgeStats](#loadknowledgestats)
- [loadLocalChapters](#loadlocalchapters)
- [loadLocalProjects](#loadlocalprojects)
- [loadMarketTemplates](#loadmarkettemplates)
- [loadModule](#loadmodule)
- [loadMoreKnowledgeList](#loadmoreknowledgelist)
- [loadPipelineStatus](#loadpipelinestatus)
- [loadProjects](#loadprojects)
- [loadReviewList](#loadreviewlist)
- [loadSkillList](#loadskilllist)
- [loadState](#loadstate)
- [loadSystemHealth](#loadsystemhealth)
- [loadUkItems](#loadukitems)
- [loadUkStats](#loadukstats)
- [loadUkTree](#loaduktree)
- [loadWorkspaces](#loadworkspaces)
- [openCatManage](#opencatmanage)
- [openForeshadowingDetail](#openforeshadowingdetail)
- [openSkillEdit](#openskilledit)
- [openStepEdit](#openstepedit)
- [openUkEdit](#openukedit)
- [parseCsv](#parsecsv)
- [parseJson](#parsejson)
- [readChapterContent](#readchaptercontent)
- [refreshAuth](#refreshauth)
- [registerLocalProject](#registerlocalproject)
- [rejectReview](#rejectreview)
- [removeCustomCategory](#removecustomcategory)
- [removeStep](#removestep)
- [renderCacheList](#rendercachelist)
- [renderCanonList](#rendercanonlist)
- [renderCategoryTree](#rendercategorytree)
- [renderChapterPlans](#renderchapterplans)
- [renderCouncilConfigs](#rendercouncilconfigs)
- [renderEntityList](#renderentitylist)
- [renderForeshadowingDetail](#renderforeshadowingdetail)
- [renderForeshadowingKanban](#renderforeshadowingkanban)
- [renderGraph](#rendergraph)
- [renderKnowledgeEditor](#renderknowledgeeditor)
- [renderKnowledgeItemDetail](#renderknowledgeitemdetail)
- [renderKnowledgeItemList](#renderknowledgeitemlist)
- [renderKnowledgeList](#renderknowledgelist)
- [renderKnowledgeListPagination](#renderknowledgelistpagination)
- [renderMarkdown](#rendermarkdown)
- [renderMarketTemplates](#rendermarkettemplates)
- [renderModelProfiles](#rendermodelprofiles)
- [renderOfflineQueue](#renderofflinequeue)
- [renderPagination](#renderpagination)
- [renderRelationList](#renderrelationlist)
- [renderReviewDetail](#renderreviewdetail)
- [renderReviewList](#renderreviewlist)
- [renderRevisionTasks](#renderrevisiontasks)
- [renderRuleProposals](#renderruleproposals)
- [renderRulesResult](#renderrulesresult)
- [renderSnapshotList](#rendersnapshotlist)
- [renderStepList](#rendersteplist)
- [renderTemplates](#rendertemplates)
- [renderThreads](#renderthreads)
- [renderTreeNode](#rendertreenode)
- [renderUkTree](#renderuktree)
- [renderVolumes](#rendervolumes)
- [resetKnowledgeList](#resetknowledgelist)
- [runPipeline](#runpipeline)
- [saveBackupSchedule](#savebackupschedule)
- [saveCategory](#savecategory)
- [saveKnowledgeEditor](#saveknowledgeeditor)
- [saveKnowledgePack](#saveknowledgepack)
- [saveNewKnowledgeItem](#savenewknowledgeitem)
- [saveSkill](#saveskill)
- [saveState](#savestate)
- [saveStep](#savestep)
- [saveUkEntry](#saveukentry)
- [scanLocalProject](#scanlocalproject)
- [scanProject](#scanproject)
- [selectCategory](#selectcategory)
- [selectKnowledgeItemEdit](#selectknowledgeitemedit)
- [selectReviewItem](#selectreviewitem)
- [selectSkill](#selectskill)
- [setStatus](#setstatus)
- [setupDropdown](#setupdropdown)
- [setupMenuGroups](#setupmenugroups)
- [show](#show)
- [showToast](#showtoast)
- [submitKnowledgeForReview](#submitknowledgeforreview)
- [t](#t)
- [toggleCategory](#togglecategory)
- [toggleSidebar](#togglesidebar)
- [updateConnectionStatus](#updateconnectionstatus)
- [updateProjectDropdowns](#updateprojectdropdowns)
- [updateTokenState](#updatetokenstate)
- [viewChapterDetail](#viewchapterdetail)
- [viewProjectStats](#viewprojectstats)
- [warmCache](#warmcache)

---

## 模块概览

| 模块 | 函数数 | 文件 |
|------|--------|------|
| init_* | 11 | |
| loadApiTokens | 1 | |
| loadBackupList | 1 | |
| loadCacheStats | 1 | |
| loadCanonDoc | 1 | |
| loadChapterList | 1 | |
| loadEntityDetails | 1 | |
| loadKnowledgeCategories | 1 | |
| loadKnowledgeGraphCategory | 1 | |
| loadKnowledgeItems | 1 | |
| loadKnowledgeList | 1 | |
| loadKnowledgeMaintain | 1 | |
| loadKnowledgeModule | 1 | |
| loadKnowledgePack | 1 | |
| loadKnowledgeStats | 1 | |
| loadLocalChapters | 1 | |
| loadLocalProjects | 1 | |
| loadMarketTemplates | 1 | |
| loadModule | 1 | |
| loadMoreKnowledgeList | 1 | |
| loadPipelineStatus | 1 | |
| loadProjects | 1 | |
| loadReviewList | 1 | |
| loadSkillList | 1 | |
| loadState | 1 | |
| loadSystemHealth | 1 | |
| loadUkItems | 1 | |
| loadUkStats | 1 | |
| loadUkTree | 1 | |
| loadWorkspaces | 1 | |
| renderCacheList | 1 | |
| renderCanonList | 1 | |
| renderCategoryTree | 1 | |
| renderChapterPlans | 1 | |
| renderCouncilConfigs | 1 | |
| renderEntityList | 1 | |
| renderForeshadowingDetail | 1 | |
| renderForeshadowingKanban | 1 | |
| renderGraph | 1 | |
| renderKnowledgeEditor | 1 | |
| renderKnowledgeItemDetail | 1 | |
| renderKnowledgeItemList | 1 | |
| renderKnowledgeList | 1 | |
| renderKnowledgeListPagination | 1 | |
| renderMarkdown | 1 | |
| renderMarketTemplates | 1 | |
| renderModelProfiles | 1 | |
| renderOfflineQueue | 1 | |
| renderPagination | 1 | |
| renderRelationList | 1 | |
| renderReviewDetail | 1 | |
| renderReviewList | 1 | |
| renderRevisionTasks | 1 | |
| renderRuleProposals | 1 | |
| renderRulesResult | 1 | |
| renderSnapshotList | 1 | |
| renderStepList | 1 | |
| renderTemplates | 1 | |
| renderThreads | 1 | |
| renderTreeNode | 1 | |
| renderUkTree | 1 | |
| renderVolumes | 1 | |
| uncategorized | 73 | |

---

## addCustomCategory

- **用途**: Add custom category to pack
- **Async**: ✅
- **参数**: `()`
- **行数**: 12
- **调用**: showToast, loadKnowledgePack, api, t, setStatus, show
- **被调用**: init

```javascript
function addCustomCategory() {
  var name = $("customCatName").value.trim();
      var parent = $("customCatParent").value.trim();
      if (!name) { showToast("warning", "请输入分类名称"); return; }
      if (!currentPackProjectId) { showToast("warning", "请先选择项目"); return; }
      setStatus("添加自定义分类...");
      var result = await api("/api/tool", { tool: "kb.pack.custom.add", arguments: { project_id: currentPackProjectId, name: name, parent: parent || null } });
      if (result && !result.error) {
        showToast("success", "自定义分类...
}
```

---

## api

- **用途**: API fetch wrapper with error handling
- **Async**: ✅
- **参数**: `(path, body)`
- **行数**: 21
- **调用**: t, show
- **被调用**: init_auto_search, init_knowledge_graph, loadKnowledgeGraphCategory, init_knowledge_expiry, saveCategory, confirmDeleteCategory, loadUkStats, loadUkTree, loadUkItems, saveUkEntry

```javascript
function api(path, body) {
  try {
        const options = body ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body)
        } : {};
        const response = await fetch(path, options);
        if (!response.ok) {
          var errText = await response.text().catch(function() { return response.statusText; });
          showToast("error", "请求失败 (" + response.status + ")", errText.substring(0, 200));
          return { error: errText };
        }
       ...
}
```

---

## applyLanguage

- **用途**: Language switcher
- **Async**: ❌
- **参数**: `(language)`
- **行数**: 10
- **调用**: t, updateTokenState
- **被调用**: init

```javascript
function applyLanguage(language) {
  currentLanguage = translations[language] ? language : "en";
      localStorage.setItem("novel_os_language", currentLanguage);
      document.documentElement.lang = currentLanguage === "zh" ? "zh-CN" : "en";
      document.querySelectorAll("[data-i18n]").forEach((node) => {
        node.textContent = t(node.dataset.i18n);
      });
      document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
        node.placeholder = t(node.dataset.i18nPlaceholder);
      });
      updateTokenS...
}
```

---

## approveReview

- **用途**: Approve review submission
- **Async**: ✅
- **参数**: `(reviewId)`
- **行数**: 7
- **调用**: t, loadReviewList, selectReviewItem
- **被调用**: renderReviewDetail

```javascript
function approveReview(reviewId) {
  const comment = prompt("Enter review comment (optional):");
      const result = await api("/api/tool", { tool: "knowledge.review.approve", arguments: { review_id: reviewId, comment } });
      if (result.ok) {
        showToast("success", "Approved successfully");
        await loadReviewList();
        selectReviewItem(reviewId);
      }...
}
```

---

## argsFor

- **用途**: Build MCP tool arguments
- **Async**: ❌
- **参数**: `(form)`
- **行数**: 8
- **调用**: t, baseProjectArgs
- **被调用**: init

```javascript
function argsFor(form) {
  if (form === "user") return { username: $("newUser").value, display_name: $("displayName").value || null, password: $("newUserPassword").value || null, email: $("newUserEmail").value || null };
      if (form === "workspace") return { slug: $("newWorkspace").value, name: $("newWorkspace").value };
      if (form === "project") return { workspace: $("newWorkspace").value || $("workspace").value, slug: $("projectSlug").value, title: $("projectTitle").value };
      if (form === "projectList") retu...
}
```

---

## baseProjectArgs

- **用途**: Get base project API arguments
- **Async**: ❌
- **参数**: `()`
- **行数**: 4
- **调用**: t
- **被调用**: argsFor, init, createPipelinePlan, loadPipelineStatus, loadChapterList, createBackup, saveBackupSchedule, runPipeline

```javascript
function baseProjectArgs() {
  return {
        workspace: $("workspaceSelect")?.value || $("workspace")?.value || "",
        project: $("projectSelect")?.value || $("project")?.value || ""
      };...
}
```

---

## buildTree

- **用途**: Build tree structure from flat list
- **Async**: ❌
- **参数**: `(parentKey, depth = 0, parentElement = container)`
- **行数**: 54
- **调用**: t, buildTree
- **被调用**: loadUkTree, renderCategoryTree

```javascript
function buildTree(parentKey, depth = 0, parentElement = container) {
  const children = parentMap[parentKey] || [];
          if (children.length === 0) return;

          children.forEach(cat => {
            const childKey = cat.id;
            const hasChildren = parentMap[childKey] && parentMap[childKey].length > 0;

            const itemDiv = document.createElement('div');
            itemDiv.style.cursor = 'pointer';
            itemDiv.style.padding = '4px 6px';
            itemDiv.style.borderRadius = '4px';
            
            itemDiv.onmouseover = (...
}
```

---

## callTool

- **用途**: MCP tool call wrapper
- **Async**: ✅
- **参数**: `(tool, arguments_)`
- **行数**: 10
- **调用**: t, api, setStatus
- **被调用**: init

```javascript
function callTool(tool, arguments_) {
  setStatus(t("status.running") + " " + tool);
      const payload = { tool, arguments: arguments_ };
      if ($("mcpUrl")?.value) payload.mcp_url = $("mcpUrl").value;
      const response = await api("/api/tool", payload);
      
      const outputEl = $("output");
      if (outputEl) outputEl.textContent = JSON.stringify(response, null, 2);
      
      setStatus(response.ok ? t("status.done") : t("status.error"));
      return response;...
}
```

---

## clearCache

- **用途**: Clear cache
- **Async**: ✅
- **参数**: `()`
- **行数**: 6
- **调用**: showToast, api, loadCacheStats, t, show
- **被调用**: init

```javascript
function clearCache() {
  if (!confirm("确定要清空所有缓存吗？")) return;
      var result = await api("/api/tool", { tool: "system.cache.invalidate", arguments: {} });
      if (result && !result.error) {
        showToast("success", "缓存已清空");
        loadCacheStats();
      }...
}
```

---

## closeAllDropdowns

- **用途**: Close all open dropdowns
- **Async**: ❌
- **参数**: `()`
- **行数**: 1
- **调用**: t
- **被调用**: goToPage, setupDropdown

```javascript
function closeAllDropdowns() {
  document.querySelectorAll(".dropdown-menu").forEach(m => m.classList.remove("show"));...
}
```

---

## closeKnowledgeEditor

- **用途**: Close knowledge editor
- **Async**: ❌
- **参数**: `()`
- **行数**: 9
- **调用**: t
- **被调用**: deleteKnowledgeItemEdit, createNewKnowledgeItem

```javascript
function closeKnowledgeEditor() {
  $("kbEditorCloseBtn").style.display = "none";
      selectedItemId = null;
      selectedItemType = null;
      $("kbEditorContent").innerHTML = `
        <div style="text-align:center; color:var(--muted); padding:40px;">
          <p>${t("knowledge.selectItem")}</p>
          <p style="font-size:12px; margin-top:8px;">${t("knowledge.editTip")}</p>
        </div>
      `;...
}
```

---

## confirmDeleteCategory

- **用途**: Confirm category deletion
- **Async**: ✅
- **参数**: `()`
- **行数**: 6
- **调用**: t
- **被调用**: initUkManage

```javascript
function confirmDeleteCategory() {
  if (!ukCatDeleteTargetId) return;
      const result = await api("/api/tool", { tool: "kb.category.delete", arguments: { category_id: ukCatDeleteTargetId } });
      $("ukCatDeleteModal").classList.add("hidden");
      ukCatDeleteTargetId = null;
      if (result.ok) { await loadUkStats(); await loadUkTree(); setStatus(t("msg.deleted")); }
      else setStatus(t("status.error"));...
}
```

---

## createBackup

- **用途**: Create new backup
- **Async**: ✅
- **参数**: `()`
- **行数**: 6
- **调用**: showToast, baseProjectArgs, loadBackupList, api, t, setStatus, show
- **被调用**: init

```javascript
function createBackup() {
  setStatus("创建备份...");
      var result = await api("/api/tool", { tool: "backup.create", arguments: Object.assign(baseProjectArgs(), { backup_type: "full" }) });
      if (result && !result.error) {
        showToast("success", "备份已创建");
        loadBackupList();
      }...
}
```

---

## createKnowledgePack

- **用途**: Create new knowledge pack
- **Async**: ✅
- **参数**: `()`
- **行数**: 9
- **调用**: showToast, loadKnowledgePack, api, t, setStatus, show
- **被调用**: init

```javascript
function createKnowledgePack() {
  var projectId = $("packProjectSelect").value;
      var genre = $("packGenreSelect").value;
      if (!projectId || !genre) { showToast("warning", "请选择项目和小说类型"); return; }
      setStatus("创建知识包...");
      var result = await api("/api/tool", { tool: "kb.pack.create", arguments: { project_id: projectId, genre: genre } });
      if (result && !result.error) {
        showToast("success", "知识包已创建", genre + " 类型配置已应用");
        loadKnowledgePack();
      }...
}
```

---

## createNewKnowledgeItem

- **用途**: Create new knowledge item
- **Async**: ✅
- **参数**: `()`
- **行数**: 22
- **调用**: t
- **被调用**: 无

```javascript
function createNewKnowledgeItem() {
  $("kbEditorCloseBtn").style.display = "block";
      selectedItemId = null;
      selectedItemType = "user";
      
      $("kbEditorContent").innerHTML = `
        <div class="form-group">
          <label class="form-label">${t("knowledge.title")}</label>
          <input type="text" class="form-input" id="kbNewTitle" placeholder="Title">
        </div>
        <div class="form-group">
          <label class="form-label">${t("knowledge.content")}</label>
          <textarea class="form-textare...
}
```

---

## createPipelinePlan

- **用途**: Create pipeline plan
- **Async**: ✅
- **参数**: `()`
- **行数**: 18
- **调用**: showToast, baseProjectArgs, api, t, setStatus, show
- **被调用**: init

```javascript
function createPipelinePlan() {
  var chapterNo = parseInt($("pipelineChapterNo").value);
      var targetWords = parseInt($("pipelineTargetWords").value);
      var purpose = $("pipelinePurpose").value;
      if (!chapterNo) { showToast("warning", "请输入章节号"); return; }
      setStatus("创建生成计划...");
      var result = await api("/api/tool", {
        tool: "pipeline.create_plan",
        arguments: Object.assign(baseProjectArgs(), { chapter_no: chapterNo, target_words: targetWords, purpose: purpose })
      });
      if (result &...
}
```

---

## createPrivateCopy

- **用途**: Create private copy of public knowledge
- **Async**: ✅
- **参数**: `(baseId)`
- **行数**: 6
- **调用**: t, loadKnowledgeItems
- **被调用**: renderKnowledgeEditor

```javascript
function createPrivateCopy(baseId) {
  const result = await api("/api/tool", { tool: "knowledge.user.create_from_base", arguments: { base_knowledge_id: baseId } });
      if (result.ok) {
        showToast("success", "Private copy created successfully");
        $("kbItemSource").value = "user";
        await loadKnowledgeItems();
      }...
}
```

---

## deleteKnowledgeItemEdit

- **用途**: Delete knowledge item
- **Async**: ✅
- **参数**: `(itemId)`
- **行数**: 8
- **调用**: t, loadKnowledgeItems
- **被调用**: renderKnowledgeEditor

```javascript
function deleteKnowledgeItemEdit(itemId) {
  if (!confirm("Are you sure you want to delete this item?")) return;
      
      const result = await api("/api/tool", { tool: "knowledge.user.delete", arguments: { item_id: itemId } });
      if (result.ok) {
        showToast("success", "Deleted successfully");
        closeKnowledgeEditor();
        await loadKnowledgeItems();
      }...
}
```

---

## deleteSkillConfirm

- **用途**: Confirm skill deletion
- **Async**: ❌
- **参数**: `(id)`
- **行数**: 3
- **调用**: t
- **被调用**: init_skill_manage_fn

```javascript
function deleteSkillConfirm(id) {
  skillDeleteTargetId = id;
      $("skillDeleteMsg").textContent = `Delete this skill? This cannot be undone.`;
      $("skillDeleteModal").classList.remove("hidden");...
}
```

---

## deleteSkillExecute

- **用途**: Execute skill deletion
- **Async**: ✅
- **参数**: `()`
- **行数**: 10
- **调用**: selectSkill, api, loadSkillList, t, setStatus
- **被调用**: init_skill_manage_fn

```javascript
function deleteSkillExecute() {
  if (!skillDeleteTargetId) return;
      const result = await api("/api/tool", { tool: "skill.delete", arguments: { skill_id: skillDeleteTargetId } });
      $("skillDeleteModal").classList.add("hidden");
      skillDeleteTargetId = null;
      skillCurrentId = null;
      $("skillDetailActions").style.display = "none";
      $("skillDetailTitle").textContent = t("skill.selectSkill");
      $("skillDetailContent").innerHTML = "";
      if (result.ok) { await loadSkillList(); setStatus(t("msg.dele...
}
```

---

## escapeHtml

- **用途**: HTML entity escaping
- **Async**: ❌
- **参数**: `(str)`
- **行数**: 2
- **调用**: 无
- **被调用**: init_knowledge_graph, loadKnowledgeGraphCategory, init_knowledge_expiry, toggleCategory, showToast, renderMarkdown, loadSkillList, selectSkill, renderStepList, init

```javascript
function escapeHtml(str) {
  if (!str) return '';
      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');...
}
```

---

## getActiveProjectArgs

- **用途**: Get active project arguments
- **Async**: ❌
- **参数**: `()`
- **行数**: 7
- **调用**: t, setStatus
- **被调用**: loadCanonDoc, loadEntityDetails, init, openForeshadowingDetail

```javascript
function getActiveProjectArgs() {
  const workspace = $("workspaceSelect")?.value || $("workspace")?.value;
      const project = $("projectSelect")?.value || $("project")?.value;
      if (!project) {
        setStatus(t("msg.noProject"));
        return null;
      }
      return { workspace, project };...
}
```

---

## getActiveWorkspace

- **用途**: Get current workspace slug
- **Async**: ❌
- **参数**: `()`
- **行数**: 1
- **调用**: t
- **被调用**: init

```javascript
function getActiveWorkspace() {
  return $("workspaceSelect")?.value || $("workspace")?.value || "";...
}
```

---

## getAllChildSlugs

- **用途**: Get all child category slugs
- **Async**: ❌
- **参数**: `(slug)`
- **行数**: 5
- **调用**: t
- **被调用**: loadUkItems

```javascript
function getAllChildSlugs(slug) {
  const node = ukTreeData[slug];
      if (!node || !node.children) return [];
      let result = [...node.children];
      node.children.forEach(child => { result = result.concat(getAllChildSlugs(child)); });
      return result;...
}
```

---

## getNodeCount

- **用途**: Get tree node count
- **Async**: ❌
- **参数**: `(slug)`
- **行数**: 13
- **调用**: t
- **被调用**: renderTreeNode

```javascript
function getNodeCount(slug) {
  const node = ukTreeData[slug];
      if (!node) return ukCategoryCounts[slug] || 0;

      // If this node has children, sum their counts recursively
      if (node.children && node.children.length > 0) {
        let total = ukCategoryCounts[slug] || 0;
        node.children.forEach(childSlug => {
          total += getNodeCount(childSlug);
        });
        return total;
      }

      return ukCategoryCounts[slug] || 0;...
}
```

---

## goToPage

- **用途**: Navigate to page by name
- **Async**: ❌
- **参数**: `(pageName)`
- **行数**: 42
- **调用**: t, loadModule, loadKnowledgeModule
- **被调用**: init_project_world_rules, init_project_characters, init_project_factions, setupMenuGroups, loadCanonDoc, loadEntityDetails, init

```javascript
function goToPage(pageName) {
  console.log("[DEBUG] goToPage:", pageName);
      currentPage = pageName;
      
      document.querySelectorAll(".page").forEach(p => p.classList.add("hidden"));
      
      const targetPage = $("page-" + pageName);
      console.log("[DEBUG] targetPage:", targetPage ? "found" : "NOT FOUND", "page-" + pageName);
      if (targetPage) {
        loadModule(pageName).then(() => {
          console.log("[DEBUG] loadModule done, checking init:", "init_" + pageName, "exists:", !!window["init_" + pag...
}
```

---

## init

- **用途**: Application initialization entry point
- **Async**: ❌
- **参数**: `()`
- **行数**: 3467
- **调用**: baseProjectArgs, refreshAuth, getActiveWorkspace, t, setupDropdown, loadWorkspaces, getActiveProjectArgs, showToast, argsFor, saveState
- **被调用**: loadKnowledgeModule, init_knowledge_graph, loadKnowledgeGraphCategory, init_project_world_state, goToPage, init_skill_manage_fn

```javascript
function init() {
  loadState();
      setupMenuGroups();
      setupDropdown("langBtn", "langMenu");
      setupDropdown("userBtn", "userMenu");

      // Initial project section visibility
      const projectSection = document.querySelector('[data-section="project"]');
      if (projectSection) {
        projectSection.style.display = "block";
      }

      // Sidebar toggle
      $("sidebarToggle").onclick = toggleSidebar;

      // Language dropdown
      document.querySelectorAll("#langMenu .dropdown-item").f...
}
```

---

## initUkManage

- **用途**: Initialize UK manage page
- **Async**: ✅
- **参数**: `()`
- **行数**: 23
- **调用**: t
- **被调用**: loadKnowledgeModule

```javascript
function initUkManage() {
  // Load stats FIRST so counts are available when rendering tree
      await loadUkStats();
      await loadUkTree();
      await loadUkItems(null);
      $("ukSearchInput").value = "";
      $("ukSearchBtn").onclick = () => loadUkItems($("ukSearchInput").value.trim());
      $("ukResetBtn").onclick = () => { $("ukSearchInput").value = ""; ukCurrentCategory = null; loadUkItems(); renderUkTree(); };
      $("ukCreateBtn").onclick = () => openUkEdit(null);
      $("ukEditClose").onclick = () => $("...
}
```

---

## init_auto_search

- **用途**: Initialize auto search page
- **Async**: ❌
- **参数**: `()`
- **行数**: 20
- **调用**: t
- **被调用**: loadKnowledgeModule

```javascript
function init_auto_search() {
  const btn = $("autoSearchBtn");
      if (btn) {
        btn.onclick = async () => {
          const topic = $("autoSearchTopic").value;
          const category = $("autoSearchCategory").value;
          if (!topic) return;
          setStatus("Searching...");
          const result = await api("/api/tool", {
            tool: "knowledge_base.auto_search",
            arguments: { topic, category }
          });
          if (result.ok) {
            $("autoSearchResultCard").style.display = "b...
}
```

---

## init_knowledge_expiry

- **用途**: Initialize knowledge expiry alerts
- **Async**: ❌
- **参数**: `()`
- **行数**: 20
- **调用**: t, escapeHtml
- **被调用**: loadKnowledgeModule

```javascript
function init_knowledge_expiry() {
  const container = $("knowledgeExpiryResult");
      if (!container) return;
      container.innerHTML = "<p>Loading...</p>";
      // Search for items with expiry-related keywords
      api("/api/tool", { tool: "kb.uk.search", arguments: { query: "过期 失效 待更新", limit: 100 } }).then(function(result) {
        if (result && result.items && result.items.length > 0) {
          var html = '<div class="list-container">';
          result.items.forEach(function(item) {
            html += '<div class="l...
}
```

---

## init_knowledge_graph

- **用途**: Initialize knowledge graph
- **Async**: ❌
- **参数**: `()`
- **行数**: 25
- **调用**: t, escapeHtml
- **被调用**: loadKnowledgeModule, loadKnowledgeGraphCategory

```javascript
function init_knowledge_graph() {
  const container = $("knowledgeGraphContent");
      if (!container) return;
      container.innerHTML = "<p>Loading...</p>";
      // Wire refresh button
      const refreshBtn = $("refreshKnowledgeGraphBtn");
      if (refreshBtn) {
        refreshBtn.onclick = () => init_knowledge_graph();
      }
      // Load knowledge items grouped by category
      api("/api/tool", { tool: "kb.category.list", arguments: { parent_slug: "" } }).then(function(catResult) {
        if (catResult && catResult.ca...
}
```

---

## init_model_cost_fn

- **用途**: Init model cost page
- **Async**: ✅
- **参数**: `()`
- **行数**: 8
- **调用**: t
- **被调用**: init

```javascript
function init_model_cost_fn() {
  if (modelCostInitStarted) return;
        modelCostInitStarted = true;
        // Set default date range (last 30 days)
        const today = new Date().toISOString().split('T')[0];
        const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        $("costReportFromDate").value = thirtyDaysAgo;
        $("costReportToDate").value = today;
        $("costReportBtn").click();...
}
```

---

## init_model_profiles_fn

- **用途**: Init model profiles page
- **Async**: ✅
- **参数**: `()`
- **行数**: 3
- **调用**: t
- **被调用**: init

```javascript
function init_model_profiles_fn() {
  if (modelProfilesInitStarted) return;
        modelProfilesInitStarted = true;
        $("modelProfilesListBtn").click();...
}
```

---

## init_project_characters

- **用途**: Init project characters page
- **Async**: ✅
- **参数**: `()`
- **行数**: 19
- **调用**: t
- **被调用**: 无

```javascript
function init_project_characters() {
  const container = $("projectCharactersResult");
      if (!container) return;
      container.innerHTML = "<p>Loading...</p>";
      const result = await api("/api/tool", {
        tool: "state.entity.list",
        arguments: { entity_type: "character", limit: 50 }
      });
      if (result.ok && result.result) {
        const items = result.result.items || [];
        container.innerHTML = items.length === 0 ? "<p>No characters found.</p>" :
          items.map(item => `
            <div clas...
}
```

---

## init_project_factions

- **用途**: Init project factions page
- **Async**: ✅
- **参数**: `()`
- **行数**: 19
- **调用**: t
- **被调用**: 无

```javascript
function init_project_factions() {
  const container = $("projectFactionsResult");
      if (!container) return;
      container.innerHTML = "<p>Loading...</p>";
      const result = await api("/api/tool", {
        tool: "state.entity.list",
        arguments: { entity_type: "faction", limit: 50 }
      });
      if (result.ok && result.result) {
        const items = result.result.items || [];
        container.innerHTML = items.length === 0 ? "<p>No factions found.</p>" :
          items.map(item => `
            <div class="lis...
}
```

---

## init_project_world_rules

- **用途**: Init project world rules page
- **Async**: ✅
- **参数**: `()`
- **行数**: 19
- **调用**: t
- **被调用**: 无

```javascript
function init_project_world_rules() {
  const container = $("projectWorldRulesResult");
      if (!container) return;
      container.innerHTML = "<p>Loading...</p>";
      const result = await api("/api/tool", {
        tool: "canon.doc.list",
        arguments: { doc_type: "world", limit: 50 }
      });
      if (result.ok && result.result) {
        const items = result.result.items || [];
        container.innerHTML = items.length === 0 ? "<p>No world rules found.</p>" :
          items.map(item => `
            <div class="list-i...
}
```

---

## init_project_world_state

- **用途**: Init project world state page
- **Async**: ✅
- **参数**: `()`
- **行数**: 18
- **调用**: t
- **被调用**: 无

```javascript
function init_project_world_state() {
  const container = $("projectWorldStateContent");
      if (!container) return;
      container.innerHTML = "<p>Loading...</p>";
      const result = await api("/api/tool", {
        tool: "state.world.get",
        arguments: {}
      });
      if (result.ok && result.result) {
        const state = result.result;
        container.innerHTML = `<pre class="output">${JSON.stringify(state, null, 2)}</pre>`;
      } else {
        container.innerHTML = "<p>No world state data.</p>";
      }
      /...
}
```

---

## init_skill_manage_fn

- **用途**: Init skill management page
- **Async**: ✅
- **参数**: `()`
- **行数**: 22
- **调用**: t
- **被调用**: 无

```javascript
function init_skill_manage_fn() {
  console.log("[Skill] init_skill_manage called");
      await loadSkillList();
      $("skillRefreshBtn").onclick = () => loadSkillList();
      $("skillCreateBtn").onclick = () => openSkillEdit(null);
      $("skillEditClose").onclick = () => $("skillEditModal").classList.add("hidden");
      $("skillEditCancel").onclick = () => $("skillEditModal").classList.add("hidden");
      $("skillEditSave").onclick = saveSkill;
      $("skillEditBtn").onclick = () => { if (skillCurrentId) openSkillEdit(sk...
}
```

---

## init_template_list_fn

- **用途**: Init template list page
- **Async**: ✅
- **参数**: `()`
- **行数**: 3
- **调用**: t
- **被调用**: init

```javascript
function init_template_list_fn() {
  if (templateListInitStarted) return;
        templateListInitStarted = true;
        $("templateListBtn").click();...
}
```

---

## loadApiTokens

- **用途**: Load API token list
- **Async**: ✅
- **参数**: `()`
- **行数**: 27
- **调用**: api, t, escapeHtml
- **被调用**: init

```javascript
function loadApiTokens() {
  const workspace = $("workspace")?.value || $("workspaceSelect")?.value || null;
        const args = { include_revoked: false };
        if (workspace) args.workspace = workspace;
        const result = await api("/api/tool", {
          tool: "auth.list_api_tokens",
          arguments: args
        });
        const container = $("apiTokensList");
        if (!container) return;
        if (!result.ok || !Array.isArray(result.result)) {
          container.innerHTML = '<div style="color: var(-...
}
```

---

## loadBackupList

- **用途**: Load backup records
- **Async**: ✅
- **参数**: `()`
- **行数**: 12
- **调用**: api, t, escapeHtml
- **被调用**: init, createBackup

```javascript
function loadBackupList() {
  var result = await api("/api/tool", { tool: "backup.list", arguments: {} });
      var el = $("backupList");
      if (result && result.backups && result.backups.length > 0) {
        el.innerHTML = result.backups.map(function(b) {
          return '<div class="list-item">' +
            '<div class="list-item-header"><span>' + escapeHtml(b.filename || b.id) + '</span><span class="badge">' + (b.type || "full") + '</span></div>' +
            '<div class="list-item-meta">' + (b.created_at || "") ...
}
```

---

## loadCacheStats

- **用途**: Load cache statistics
- **Async**: ✅
- **参数**: `()`
- **行数**: 7
- **调用**: api, t, escapeHtml
- **被调用**: init, clearCache

```javascript
function loadCacheStats() {
  var result = await api("/api/tool", { tool: "system.cache.get_stats", arguments: {} });
      var el = $("cacheStats");
      if (result && !result.error) {
        el.innerHTML = '<pre style="font-size:12px;background:var(--bg);padding:12px;border-radius:6px;overflow-x:auto;">' + escapeHtml(JSON.stringify(result, null, 2)) + '</pre>';
      } else {
        el.innerHTML = '<p style="color:var(--muted);">暂无缓存数据</p>';
      }...
}
```

---

## loadCanonDoc

- **用途**: Load canon document detail
- **Async**: ✅
- **参数**: `(key)`
- **行数**: 24
- **调用**: getActiveProjectArgs, api, goToPage, t, setStatus
- **被调用**: init

```javascript
function loadCanonDoc(key) {
  const base = getActiveProjectArgs();
      if (!base) return;
      const args = { ...base, key };
      const result = await api("/api/tool", { tool: "canon.doc.get", arguments: args });
      if (result.ok && result.result) {
        const doc = result.result;
        $("canonKey").value = doc.key || "";
        $("canonTitle").value = doc.title || "";
        $("canonContent").value = doc.content || "";
        $("canonType").value = doc.doc_type || "other";
        $("canonStatus").value = d...
}
```

---

## loadChapterList

- **用途**: Load chapter list for project
- **Async**: ✅
- **参数**: `()`
- **行数**: 24
- **调用**: api, t, escapeHtml, baseProjectArgs
- **被调用**: init

```javascript
function loadChapterList() {
  var volumeFilter = $("chapterVolumeFilter").value;
      var statusFilter = $("chapterStatusFilter").value;
      var args = Object.assign(baseProjectArgs(), { limit: 100 });
      if (volumeFilter) args.volume_no = parseInt(volumeFilter);
      var result = await api("/api/tool", {
        tool: "plot.list_chapter_plans",
        arguments: args
      });
      var list = $("chapterList");
      if (result && result.chapters && result.chapters.length > 0) {
        list.innerHTML = result.chapt...
}
```

---

## loadEntityDetails

- **用途**: Load entity detail data
- **Async**: ✅
- **参数**: `(entityType, name)`
- **行数**: 25
- **调用**: getActiveProjectArgs, api, goToPage, t, setStatus
- **被调用**: init

```javascript
function loadEntityDetails(entityType, name) {
  const base = getActiveProjectArgs();
      if (!base) return;
      const args = { ...base, entity_type: entityType, name };
      setStatus(t("status.running"));
      const result = await api("/api/tool", { tool: "state.entity.get", arguments: args });
      if (result.ok && result.result) {
        const entity = result.result;
        currentEntityId = entity.id;
        $("entityType").value = entity.entity_type || "character";
        $("entityName").value = entity.name || "";
        $("e...
}
```

---

## loadKnowledgeCategories

- **用途**: Load knowledge categories tree
- **Async**: ✅
- **参数**: `()`
- **行数**: 11
- **调用**: t
- **被调用**: 无

```javascript
function loadKnowledgeCategories() {
  const result = await api("/api/tool", { tool: "knowledge.category.list", arguments: { include_inactive: false } });
      if (result.ok && Array.isArray(result.result)) {
        const categories = result.result;
        const categoryOptions = categories.map(c => `<option value="${c.slug}">${c.name || c.slug}</option>`).join('');
        ["kbListCategory", "kbSearchCategory", "kbCategory"].forEach(id => {
          const select = $(id);
          if (select) {
            select.innerHTML = `<o...
}
```

---

## loadKnowledgeGraphCategory

- **用途**: Load knowledge graph for category
- **Async**: ✅
- **参数**: `(slug)`
- **行数**: 18
- **调用**: t, escapeHtml, init_knowledge_graph
- **被调用**: init_knowledge_graph

```javascript
function loadKnowledgeGraphCategory(slug) {
  var container = $("knowledgeGraphContent");
      container.innerHTML = "<p>Loading " + slug + "...</p>";
      var result = await api("/api/tool", { tool: "kb.uk.search", arguments: { category: slug, limit: 50 } });
      if (result && result.items) {
        var html = '<div style="margin-bottom:12px;"><button class="btn btn-sm" onclick="init_knowledge_graph()">← Back</button></div>';
        html += '<div class="list-container">';
        result.items.forEach(function(item) {
          html +...
}
```

---

## loadKnowledgeItems

- **用途**: Load knowledge items for category
- **Async**: ✅
- **参数**: `()`
- **行数**: 14
- **调用**: t
- **被调用**: loadKnowledgeMaintain, selectCategory, saveKnowledgeEditor, deleteKnowledgeItemEdit, submitKnowledgeForReview, createPrivateCopy, saveNewKnowledgeItem

```javascript
function loadKnowledgeItems() {
  const source = $("kbItemSource").value;
      const args = { limit: 100, offset: 0 };
      if (selectedCategorySlug) args.category_slug = selectedCategorySlug;
      
      let toolName = "knowledge.item.list";
      if (source === "user") {
        toolName = "knowledge.user.list";
      }
      
      const result = await api("/api/tool", { tool: toolName, arguments: args });
      if (result.ok && Array.isArray(result.result)) {
        const items = result.result;
        renderKnowledgeIte...
}
```

---

## loadKnowledgeList

- **用途**: Load knowledge item list
- **Async**: ✅
- **参数**: `()`
- **行数**: 19
- **调用**: t
- **被调用**: loadKnowledgeModule, resetKnowledgeList, init

```javascript
function loadKnowledgeList() {
  setStatus(t("status.running"));
      kbListOffset = 0;
      const category = $("kbListCategory").value;
      const source = $("kbListSource").value;
      const level = $("kbListLevel").value;
      const args = { limit: kbListLimit, offset: 0 };
      if (category) args.category_slug = category;
      if (source) args.source = source;
      if (level) args.level = level;
      const result = await api("/api/tool", { tool: "knowledge.item.list", arguments: args });
      if (result.ok && Arra...
}
```

---

## loadKnowledgeMaintain

- **用途**: Load knowledge maintenance page
- **Async**: ✅
- **参数**: `()`
- **行数**: 2
- **调用**: t
- **被调用**: loadKnowledgeModule

```javascript
function loadKnowledgeMaintain() {
  await renderCategoryTree();
      await loadKnowledgeItems();...
}
```

---

## loadKnowledgeModule

- **用途**: Load knowledge module by page name
- **Async**: ✅
- **参数**: `(pageName)`
- **行数**: 30
- **调用**: t
- **被调用**: loadModule, goToPage

```javascript
function loadKnowledgeModule(pageName) {
  switch (pageName) {
        case "knowledge-stats":
          await loadKnowledgeStats();
          break;
        case "knowledge-maintain":
          await loadKnowledgeMaintain();
          break;
        case "knowledge-review":
          await loadReviewList();
          break;
        case "knowledge-list":
          await loadKnowledgeList();
          break;
        case "knowledge-search":
          break;
        case "knowledge-edit":
          break;
        case "uk-manage":
       ...
}
```

---

## loadKnowledgePack

- **用途**: Load project knowledge pack config
- **Async**: ✅
- **参数**: `()`
- **行数**: 42
- **调用**: api, t, escapeHtml, toggleCategory
- **被调用**: init, createKnowledgePack, addCustomCategory, removeCustomCategory

```javascript
function loadKnowledgePack() {
  var projectId = $("packProjectSelect").value;
      if (!projectId) { $("packActiveCategories").innerHTML = '<p style="color:var(--muted);">请先选择项目</p>'; return; }
      currentPackProjectId = projectId;

      // Load project pack
      var result = await api("/api/tool", { tool: "kb.pack.get", arguments: { project_id: projectId } });
      if (result && result.error) {
        $("packActiveCategories").innerHTML = '<p style="color:var(--muted);">该项目暂无知识包，请先创建</p>';
        $("packInactiveCatego...
}
```

---

## loadKnowledgeStats

- **用途**: Load knowledge statistics
- **Async**: ✅
- **参数**: `()`
- **行数**: 22
- **调用**: t
- **被调用**: loadKnowledgeModule, init

```javascript
function loadKnowledgeStats() {
  setStatus(t("status.running"));
      const result = await api("/api/tool", { tool: "knowledge.stats", arguments: {} });
      if (result.ok && result.result) {
        const stats = result.result;
        $("kbTotalItems").textContent = stats.total_items || 0;
        $("kbActiveItems").textContent = stats.active_items || 0;
        $("kbOpencodeItems").textContent = stats.opencode_items || 0;
        $("kbTotalViews").textContent = stats.total_views || 0;
        const categories = stats.categ...
}
```

---

## loadLocalChapters

- **用途**: Load local chapters list
- **Async**: ✅
- **参数**: `()`
- **行数**: 24
- **调用**: api, t, escapeHtml, setStatus
- **被调用**: init, runPipeline

```javascript
function loadLocalChapters() {
  var projectId = $("chapterProjectSelect").value;
      var status = $("chapterStatusFilter").value;
      if (!projectId) { $("localChapterList").innerHTML = '<p style="color:var(--muted);padding:20px;">请先选择项目</p>'; return; }
      currentLocalProjectId = projectId;
      setStatus("加载章节...");
      var args = { project_id: projectId, limit: 100 };
      if (status) args.status = status;
      var result = await api("/api/tool", { tool: "local.chapter.list", arguments: args });
      var el = $(...
}
```

---

## loadLocalProjects

- **用途**: Load local project list
- **Async**: ✅
- **参数**: `()`
- **行数**: 21
- **调用**: api, t, escapeHtml
- **被调用**: init, registerLocalProject, scanLocalProject, scanProject

```javascript
function loadLocalProjects() {
  var result = await api("/api/tool", { tool: "local.project.list", arguments: {} });
      var el = $("localProjectList");
      if (result && result.projects && result.projects.length > 0) {
        el.innerHTML = result.projects.map(function(p) {
          return '<div class="list-item">' +
            '<div class="list-item-header">' +
              '<span style="font-weight:500;">' + escapeHtml(p.project_id) + '</span>' +
              '<span class="badge">' + (p.chapter_count || 0) + ' 章</sp...
}
```

---

## loadMarketTemplates

- **用途**: Load marketplace templates
- **Async**: ✅
- **参数**: `()`
- **行数**: 8
- **调用**: t, api
- **被调用**: init

```javascript
function loadMarketTemplates() {
  var result = await api("/api/tool", { tool: "prompt.template.list", arguments: { limit: 100 } });
        if (result && result.templates) {
          marketTemplatesCache = result.templates;
          renderMarketTemplates(marketTemplatesCache);
        } else {
          $("marketPopularList").innerHTML = '<p style="color:var(--muted);">暂无模板</p>';
          $("marketNewGrid").innerHTML = '';
        }...
}
```

---

## loadModule

- **用途**: Load module/page content
- **Async**: ✅
- **参数**: `(moduleName)`
- **行数**: 25
- **调用**: t
- **被调用**: goToPage

```javascript
function loadModule(moduleName) {
  if (loadedModules.has(moduleName)) return;

      const loadingIndicator = document.getElementById("page-" + moduleName + "-loading");
      if (loadingIndicator) {
        loadingIndicator.style.display = "block";
      }

      await new Promise(resolve => setTimeout(resolve, 50));

      loadedModules.add(moduleName);

      if (loadingIndicator) {
        loadingIndicator.style.display = "none";
      }

      // Handle knowledge base pages
      if (moduleName.startsWith("knowledge-") || mo...
}
```

---

## loadMoreKnowledgeList

- **用途**: Load more knowledge items
- **Async**: ✅
- **参数**: `()`
- **行数**: 15
- **调用**: t, renderKnowledgeList
- **被调用**: renderKnowledgeListPagination

```javascript
function loadMoreKnowledgeList() {
  kbListOffset += kbListLimit;
      const category = $("kbListCategory").value;
      const source = $("kbListSource").value;
      const level = $("kbListLevel").value;
      const args = { limit: kbListLimit, offset: kbListOffset };
      if (category) args.category_slug = category;
      if (source) args.source = source;
      if (level) args.level = level;
      setStatus(t("status.running"));
      const result = await api("/api/tool", { tool: "knowledge.item.list", arguments: args });
     ...
}
```

---

## loadPipelineStatus

- **用途**: Load pipeline status
- **Async**: ✅
- **参数**: `()`
- **行数**: 16
- **调用**: t, api, baseProjectArgs
- **被调用**: init, createPipelinePlan

```javascript
function loadPipelineStatus() {
  if (!currentPlanId) return;
      var result = await api("/api/tool", {
        tool: "pipeline.get_plan",
        arguments: Object.assign(baseProjectArgs(), { plan_id: currentPlanId })
      });
      if (result && result.passes) {
        var passes = result.passes;
        ["pipelinePass1", "pipelinePass2", "pipelinePass3"].forEach(function(id, i) {
          var el = $(id);
          var pass = passes[i];
          if (pass) {
            el.className = "badge badge-" + (pass.status === "co...
}
```

---

## loadProjects

- **用途**: Load project list from API
- **Async**: ✅
- **参数**: `()`
- **行数**: 28
- **调用**: t, api, setStatus
- **被调用**: loadWorkspaces, init

```javascript
function loadProjects() {
  const workspace = $("workspaceSelect").value || $("workspace")?.value;
      if (!workspace) {
        setStatus(t("status.error") + ": workspace required");
        return;
      }
      setStatus(t("status.running"));
      try {
        const result = await api("/api/tool", {
          tool: "project.list",
          arguments: { workspace }
        });
        if (result.ok && Array.isArray(result.result)) {
          allProjects = result.result;
          const sel = $("projectSelect");
   ...
}
```

---

## loadReviewList

- **用途**: Load review list
- **Async**: ✅
- **参数**: `()`
- **行数**: 8
- **调用**: t
- **被调用**: loadKnowledgeModule, approveReview, rejectReview

```javascript
function loadReviewList() {
  const status = $("kbReviewStatus").value;
      const args = { limit: 50 };
      if (status) args.review_status = status;
      
      const result = await api("/api/tool", { tool: "knowledge.review.list", arguments: args });
      if (result.ok && Array.isArray(result.result)) {
        renderReviewList(result.result);
      }...
}
```

---

## loadSkillList

- **用途**: Load skill management list
- **Async**: ✅
- **参数**: `()`
- **行数**: 20
- **调用**: api, t, escapeHtml
- **被调用**: init_skill_manage_fn, selectSkill, saveSkill, deleteSkillExecute

```javascript
function loadSkillList() {
  console.log("[Skill] loadSkillList called");
      const container = $("skillList");
      container.innerHTML = `<p style="padding:12px;color:var(--muted);">${t("status.loading")}</p>`;
      const result = await api("/api/tool", { tool: "skill.list", arguments: { active_only: false } });
      if (!result.ok || !Array.isArray(result.result)) {
        container.innerHTML = `<p style="padding:12px;color:var(--danger);">Failed to load skills</p>`;
        return;
      }
      if (result.result....
}
```

---

## loadState

- **用途**: Load entity state data
- **Async**: ❌
- **参数**: `()`
- **行数**: 5
- **调用**: t
- **被调用**: init

```javascript
function loadState() {
  for (const key of stateKeys) {
        const saved = localStorage.getItem("novel_os_" + key);
        const el = $(key);
        if (saved && el) el.value = saved;
      }...
}
```

---

## loadSystemHealth

- **用途**: Load system health check
- **Async**: ✅
- **参数**: `()`
- **行数**: 29
- **调用**: api, t, escapeHtml, setStatus
- **被调用**: init

```javascript
function loadSystemHealth() {
  setStatus("加载系统状态...");
      var result = await api("/api/tool", { tool: "admin.health", arguments: {} });
      var cards = $("healthCards");
      if (result && !result.error) {
        cards.innerHTML =
          '<div class="panel" style="padding:16px;text-align:center;">' +
            '<div style="font-size:24px;margin-bottom:4px;">' + (result.database ? "🟢" : "🔴") + '</div>' +
            '<div style="font-size:13px;font-weight:500;">数据库</div>' +
            '<div style="font-size:12px;c...
}
```

---

## loadUkItems

- **用途**: Load UK items
- **Async**: ✅
- **参数**: `(query)`
- **行数**: 46
- **调用**: t
- **被调用**: initUkManage, saveUkEntry

```javascript
function loadUkItems(query) {
  const container = $("ukListResult");
      if (!container) return;
      container.innerHTML = `<p>${t("status.loading")}</p>`;

      let allItems = [];
      if (ukCurrentCategory) {
        const childSlugs = getAllChildSlugs(ukCurrentCategory);
        const slugsToQuery = [ukCurrentCategory, ...childSlugs];
        const promises = slugsToQuery.map(slug =>
          api("/api/tool", { tool: "kb.uk.search", arguments: { query: query || "", category_slug: slug, limit: 1000 } })
        );
   ...
}
```

---

## loadUkStats

- **用途**: Load UK statistics
- **Async**: ✅
- **参数**: `()`
- **行数**: 10
- **调用**: t
- **被调用**: initUkManage, saveCategory, confirmDeleteCategory

```javascript
function loadUkStats() {
  const result = await api("/api/tool", { tool: "kb.uk.stats", arguments: {} });
      if (result.ok && result.result && result.result.by_category) {
        ukCategoryCounts = {};
        let total = 0;
        result.result.by_category.forEach(c => {
          ukCategoryCounts[c.slug] = c.count || 0;
          total += (c.count || 0);
        });
        ukCategoryCounts["_total"] = total;
      }...
}
```

---

## loadUkTree

- **用途**: Load UK category tree
- **Async**: ✅
- **参数**: `()`
- **行数**: 30
- **调用**: t
- **被调用**: initUkManage, saveCategory, confirmDeleteCategory

```javascript
function loadUkTree() {
  console.log("### FILE VERSION: 2026-07-02-v5 ###");
      // Get ALL categories at once (including children)
      const allResult = await api("/api/tool", { tool: "kb.category.tree", arguments: {} });
      if (!allResult.ok || !Array.isArray(allResult.result)) return;
      ukAllCategories = allResult.result;

      // DEBUG: log what we received
      console.log("=== loadUkTree DEBUG ===");
      console.log("Total categories:", ukAllCategories.length);
      ukAllCategories.forEach(c => {
 ...
}
```

---

## loadWorkspaces

- **用途**: Load workspace list from API
- **Async**: ✅
- **参数**: `()`
- **行数**: 23
- **调用**: t, api
- **被调用**: init

```javascript
function loadWorkspaces() {
  try {
        const result = await api("/api/tool", {
          tool: "workspace.list",
          arguments: {}
        });
        if (result.ok && Array.isArray(result.result)) {
          allWorkspaces = result.result;
          const sel = $("workspaceSelect");
          sel.innerHTML = '<option value="">-- Select --</option>';
          result.result.forEach(w => {
            const opt = document.createElement("option");
            opt.value = w.slug;
            opt.textContent = (w.name...
}
```

---

## openCatManage

- **用途**: Open category management modal
- **Async**: ✅
- **参数**: `()`
- **行数**: 13
- **调用**: t
- **被调用**: initUkManage

```javascript
function openCatManage() {
  const modal = $("ukCatModal");
      const parentSelect = $("ukCatParent");
      // Build parent options from current categories
      const rootCats = ukAllCategories.filter(c => !c.parent_id);
      parentSelect.innerHTML = `<option value="">— ${t("uk.topLevel")} —</option>` +
        rootCats.map(c => `<option value="${c.id}">${c.name || c.slug}</option>`).join("");
      // Clear form
      $("ukCatEditId").value = "";
      $("ukCatName").value = "";
      $("ukCatSlug").value = "";
      ...
}
```

---

## openForeshadowingDetail

- **用途**: Open foreshadowing detail view
- **Async**: ❌
- **参数**: `(key)`
- **行数**: 16
- **调用**: renderForeshadowingDetail, getActiveProjectArgs, api, t, setStatus
- **被调用**: init, renderForeshadowingKanban

```javascript
function openForeshadowingDetail(key) {
  const base = getActiveProjectArgs();
        if (!base) return;
        setStatus(t("status.running"));
        api("/api/tool", { tool: "plot.list_foreshadowing", arguments: { ...base, statuses: [] } })
          .then(result => {
            if (result.ok && Array.isArray(result.result)) {
              const item = result.result.find(i => i.key === key);
              if (item) {
                currentForeshadowing = item;
                renderForeshadowingDetail(item);
                setS...
}
```

---

## openSkillEdit

- **用途**: Open skill editor modal
- **Async**: ✅
- **参数**: `(id)`
- **行数**: 32
- **调用**: t, api
- **被调用**: init_skill_manage_fn

```javascript
function openSkillEdit(id) {
  const modal = $("skillEditModal");
      $("skillEditId").value = "";
      $("skillEditName").value = "";
      $("skillEditDesc").value = "";
      $("skillEditTriggers").value = "";
      $("skillEditTools").value = "";
      $("skillEditSort").value = "0";
      $("skillEditActive").checked = true;
      $("skillEditContent").value = "";
      $("skillStepList").innerHTML = "";

      if (id) {
        $("skillEditTitle").textContent = t("skill.editSkill");
        const result = await api("...
}
```

---

## openStepEdit

- **用途**: Open skill step editor
- **Async**: ❌
- **参数**: `(index)`
- **行数**: 26
- **调用**: t
- **被调用**: init_skill_manage_fn, renderStepList

```javascript
function openStepEdit(index) {
  const modal = $("skillStepModal");
      $("skillStepId").value = "";
      $("skillStepSkillId").value = skillCurrentId || "";
      $("skillStepOrder").value = skillCurrentSteps.length + 1;
      $("skillStepName").value = "";
      $("skillStepTool").value = "";
      $("skillStepDesc").value = "";
      $("skillStepParams").value = "{}";
      $("skillStepOptional").checked = false;
      $("skillStepCondition").value = "";

      if (index !== null && skillCurrentSteps[index]) {
        $("...
}
```

---

## openUkEdit

- **用途**: Open UK item editor
- **Async**: ✅
- **参数**: `(item)`
- **行数**: 33
- **调用**: t
- **被调用**: initUkManage, loadUkItems

```javascript
function openUkEdit(item) {
  const modal = $("ukEditModal");
      const catSelect = $("ukEditCategory");
      const buildOptions = (cats, depth = 0) => {
        return cats.map(c => {
          const prefix = "\u00A0\u00A0".repeat(depth);
          return `<option value="${c.slug}">${prefix}${c.name || c.slug}</option>`;
        }).join("");
      };
      const rootCats = ukAllCategories.filter(c => !c.parent_id);
      catSelect.innerHTML = `<option value="">—</option>` + buildOptions(rootCats);

      if (item) {
    ...
}
```

---

## parseCsv

- **用途**: Parse CSV string
- **Async**: ❌
- **参数**: `(str)`
- **行数**: 2
- **调用**: t
- **被调用**: init

```javascript
function parseCsv(str) {
  if (!str || !str.trim()) return null;
      return str.split(",").map(s => s.trim()).filter(s => s.length > 0);...
}
```

---

## parseJson

- **用途**: Parse JSON safely
- **Async**: ❌
- **参数**: `(str, fallback)`
- **行数**: 6
- **调用**: t
- **被调用**: init

```javascript
function parseJson(str, fallback) {
  if (!str || !str.trim()) return fallback;
      try {
        return JSON.parse(str);
      } catch (e) {
        return fallback;
      }...
}
```

---

## readChapterContent

- **用途**: Read chapter content from local
- **Async**: ✅
- **参数**: `(chapterNo, version)`
- **行数**: 15
- **调用**: api, t, escapeHtml, setStatus
- **被调用**: init, viewChapterDetail

```javascript
function readChapterContent(chapterNo, version) {
  if (!currentLocalProjectId) return;
      setStatus("读取章节内容...");
      var result = await api("/api/tool", {
        tool: "local.chapter.read",
        arguments: { project_id: currentLocalProjectId, chapter_no: chapterNo, version: version }
      });
      var el = $("chapterContentPreview");
      if (result && result.content) {
        el.style.display = "block";
        el.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">' +
       ...
}
```

---

## refreshAuth

- **用途**: Check auth state and update UI
- **Async**: ✅
- **参数**: `()`
- **行数**: 15
- **调用**: t, api, show, updateTokenState
- **被调用**: init

```javascript
function refreshAuth() {
  const me = await api("/api/me");
      if ($("setupMcpUrl")) $("setupMcpUrl").value = me.default_mcp_url || "http://novel-os-mcp:8787/mcp";
      if (me.authenticated) {
        if ($("accountMcpUrl")) $("accountMcpUrl").value = me.mcp_url || me.default_mcp_url || "";
        window.__hasMcpToken = !!me.has_mcp_token;
        updateTokenState(window.__hasMcpToken);
        if (me.username) {
          const avatar = $("userBtn");
          if (avatar) avatar.textContent = me.username.charAt(0).t...
}
```

---

## registerLocalProject

- **用途**: Register local project binding
- **Async**: ✅
- **参数**: `()`
- **行数**: 12
- **调用**: showToast, loadLocalProjects, api, t, setStatus, show
- **被调用**: init

```javascript
function registerLocalProject() {
  var projectId = $("localProjectId").value.trim();
      var localPath = $("localProjectPath").value.trim();
      if (!projectId || !localPath) { showToast("warning", "请填写项目 ID 和目录路径"); return; }
      setStatus("注册项目...");
      var result = await api("/api/tool", {
        tool: "local.project.register",
        arguments: { project_id: projectId, local_root: localPath }
      });
      if (result && !result.error) {
        showToast("success", "项目已注册", localPath);
        loadLocalProjects()...
}
```

---

## rejectReview

- **用途**: Reject review submission
- **Async**: ✅
- **参数**: `(reviewId)`
- **行数**: 9
- **调用**: t, loadReviewList, selectReviewItem
- **被调用**: renderReviewDetail

```javascript
function rejectReview(reviewId) {
  const comment = prompt("Enter rejection reason:");
      if (!comment) return;
      
      const result = await api("/api/tool", { tool: "knowledge.review.reject", arguments: { review_id: reviewId, comment } });
      if (result.ok) {
        showToast("success", "Rejected successfully");
        await loadReviewList();
        selectReviewItem(reviewId);
      }...
}
```

---

## removeCustomCategory

- **用途**: Remove custom category from pack
- **Async**: ✅
- **参数**: `(name)`
- **行数**: 6
- **调用**: showToast, loadKnowledgePack, api, t, show
- **被调用**: init, loadKnowledgePack

```javascript
function removeCustomCategory(name) {
  if (!confirm("确定要删除自定义分类 \"" + name + "\" 吗？")) return;
      var result = await api("/api/tool", { tool: "kb.pack.custom.remove", arguments: { project_id: currentPackProjectId, name: name } });
      if (result && !result.error) {
        showToast("success", "自定义分类已删除");
        loadKnowledgePack();
      }...
}
```

---

## removeStep

- **用途**: Remove skill step
- **Async**: ❌
- **参数**: `(index)`
- **行数**: 2
- **调用**: t, renderStepList
- **被调用**: renderStepList

```javascript
function removeStep(index) {
  skillCurrentSteps.splice(index, 1);
      renderStepList();...
}
```

---

## renderCacheList

- **用途**: Render cache statistics list
- **Async**: ❌
- **参数**: `()`
- **行数**: 18
- **调用**: api, t, escapeHtml
- **被调用**: init

```javascript
function renderCacheList() {
  // Show local project stats
        api("/api/tool", { tool: "local.project.list", arguments: {} }).then(function(result) {
          var projects = (result && result.projects) ? result.projects : [];
          if (projects.length > 0) {
            $("offlineCacheList").innerHTML = projects.map(function(p) {
              return '<div class="list-item">' +
                '<div class="list-item-header">' +
                  '<span>' + escapeHtml(p.project_id) + '</span>' +
                  '<s...
}
```

---

## renderCanonList

- **用途**: Render canon document list
- **Async**: ❌
- **参数**: `(docs)`
- **行数**: 28
- **调用**: t
- **被调用**: init

```javascript
function renderCanonList(docs) {
  const container = $("canonListResult");
      if (!docs || docs.length === 0) {
        container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No documents found</p>';
        return;
      }
      container.innerHTML = docs.map(doc => `
        <div class="list-item" onclick="selectCanonDoc('${doc.key}')">
          <div class="list-item-header">
            <span>${doc.title || doc.key}</span>
            <div style="display:flex;gap:6px;align-items:center;">
    ...
}
```

---

## renderCategoryTree

- **用途**: Render category tree in sidebar
- **Async**: ✅
- **参数**: `()`
- **行数**: 72
- **调用**: t, buildTree
- **被调用**: loadKnowledgeMaintain

```javascript
function renderCategoryTree() {
  const result = await api("/api/tool", { tool: "knowledge.category.list", arguments: { include_inactive: false } });
      if (result.ok && Array.isArray(result.result)) {
        const categories = result.result;
        const parentMap = {};
        categories.forEach(cat => {
          const parentKey = cat.parent_id === null || cat.parent_id === 'null' || cat.parent_id === '' ? 'root' : cat.parent_id;
          if (!parentMap[parentKey]) parentMap[parentKey] = [];
          parentMap[parentKe...
}
```

---

## renderChapterPlans

- **用途**: Render chapter plans
- **Async**: ❌
- **参数**: `(plans)`
- **行数**: 21
- **调用**: t
- **被调用**: init

```javascript
function renderChapterPlans(plans) {
  const container = $("chapterPlansResult");
        const countBadge = $("chapterPlansCount");
        if (!plans || plans.length === 0) {
          container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No chapter plans</p>';
          countBadge.textContent = "0";
          return;
        }
        countBadge.textContent = plans.length;
        container.innerHTML = plans.map(p => `
          <div class="list-item" onclick="selectChapterPlan('${p.id}')">
         ...
}
```

---

## renderCouncilConfigs

- **用途**: Render review council configs
- **Async**: ❌
- **参数**: `(configs)`
- **行数**: 16
- **调用**: t
- **被调用**: init

```javascript
function renderCouncilConfigs(configs) {
  const container = $("councilConfigsResult");
        if (!configs || configs.length === 0) {
          container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No council configs</p>';
          return;
        }
        container.innerHTML = configs.map(c => `
          <div class="list-item" onclick="selectCouncilConfig('${c.id}')">
            <div class="list-item-header">
              <span>${c.name}</span>
              ${c.is_active ? '<span class="badge badge...
}
```

---

## renderEntityList

- **用途**: Render entity list
- **Async**: ❌
- **参数**: `(entities)`
- **行数**: 17
- **调用**: t
- **被调用**: init

```javascript
function renderEntityList(entities) {
  const container = $("entityListResult");
      if (!entities || entities.length === 0) {
        container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No entities found</p>';
        return;
      }
      container.innerHTML = entities.map(entity => `
        <div class="list-item" onclick="selectEntity('${entity.id}', '${entity.entity_type}', '${entity.name}')">
          <div class="list-item-header">
            <span>${entity.name}</span>
            <span clas...
}
```

---

## renderForeshadowingDetail

- **用途**: Render foreshadowing detail
- **Async**: ❌
- **参数**: `(item)`
- **行数**: 64
- **调用**: t, escapeHtml
- **被调用**: init, openForeshadowingDetail

```javascript
function renderForeshadowingDetail(item) {
  const content = $("foreshadowingDetailContent");
        content.innerHTML = `
          <div class="form-row">
            <div class="form-group">
              <label class="form-label" data-i18n="field.key">Key</label>
              <input class="form-input" id="fsDetailKey" value="${escapeHtml(item.key)}" readonly>
            </div>
            <div class="form-group">
              <label class="form-label" data-i18n="field.title">Title</label>
              <input class="form-input" id="...
}
```

---

## renderForeshadowingKanban

- **用途**: Render foreshadowing kanban board
- **Async**: ❌
- **参数**: `(items)`
- **行数**: 45
- **调用**: t, escapeHtml
- **被调用**: init

```javascript
function renderForeshadowingKanban(items) {
  const board = $("foreshadowingKanban");
        const statusGroups = {};
        foreshadowingStatuses.forEach(s => statusGroups[s.value] = []);
        items.forEach(item => {
          if (statusGroups[item.status]) {
            statusGroups[item.status].push(item);
          } else {
            statusGroups["planted"].push(item);
          }
        });

        let html = '<div class="kanban-columns">';
        foreshadowingStatuses.forEach(status => {
          const itemsInStatus = statu...
}
```

---

## renderGraph

- **用途**: Render relationship graph
- **Async**: ❌
- **参数**: `(nodes, links)`
- **行数**: 60
- **调用**: t, escapeHtml
- **被调用**: init

```javascript
function renderGraph(nodes, links) {
  const svg = $("graphSvg");
        const width = svg.parentElement.clientWidth;
        const height = 450;
        svg.setAttribute("width", width);
        svg.setAttribute("height", height);

        const padding = 50;
        const nodeRadius = 25;
        const colors = {
          character: "#3b82f6",
          faction: "#10b981",
          location: "#f59e0b"
        };

        let html = '<defs>';
        Object.keys(colors).forEach(type => {
          html += `<marker id="arrowhead-$...
}
```

---

## renderKnowledgeEditor

- **用途**: Render knowledge item editor
- **Async**: ❌
- **参数**: `(item, source)`
- **行数**: 38
- **调用**: t
- **被调用**: selectKnowledgeItemEdit

```javascript
function renderKnowledgeEditor(item, source) {
  const isUser = source === "user";
      const canSubmit = isUser && item.status !== 'submitted';
      
      $("kbEditorContent").innerHTML = `
        <div class="form-group">
          <label class="form-label">${t("knowledge.code")}</label>
          <input type="text" class="form-input" id="kbEditCode" value="${item.code || ''}" placeholder="Code">
        </div>
        <div class="form-group">
          <label class="form-label">${t("knowledge.title")}</label>
          <input type="text"...
}
```

---

## renderKnowledgeItemDetail

- **用途**: Render knowledge item detail
- **Async**: ❌
- **参数**: `(item)`
- **行数**: 13
- **调用**: t
- **被调用**: init

```javascript
function renderKnowledgeItemDetail(item) {
  return `
          <div style="padding: 12px; background: var(--bg); border-radius: 6px;">
            <div style="margin-bottom: 8px;"><strong>Code:</strong> ${item.code}</div>
            <div style="margin-bottom: 8px;"><strong>Category:</strong> ${item.category_name || item.category_slug || 'N/A'}</div>
            <div style="margin-bottom: 8px;"><strong>Level:</strong> ${item.level || 'N/A'}</div>
            <div style="margin-bottom: 8px;"><strong>Source:</strong> ${item.source || 'N/A'}...
}
```

---

## renderKnowledgeItemList

- **用途**: Render knowledge item list
- **Async**: ❌
- **参数**: `(items, source)`
- **行数**: 40
- **调用**: t
- **被调用**: loadKnowledgeItems

```javascript
function renderKnowledgeItemList(items, source) {
  const container = $("kbItemList");
      container.innerHTML = '';
      
      if (!items || items.length === 0) {
        container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No items found</p>';
        return;
      }
      
      items.forEach(item => {
        const isUser = source === "user";
        const reviewBadge = isUser && item.review_status === 'pending' ? 
          '<span class="badge badge-warning">Pending Review</span>' : 
          isUser && it...
}
```

---

## renderKnowledgeList

- **用途**: Render knowledge list
- **Async**: ❌
- **参数**: `(items)`
- **行数**: 25
- **调用**: t
- **被调用**: loadKnowledgeList, loadMoreKnowledgeList

```javascript
function renderKnowledgeList(items) {
  const container = $("knowledgeListResult");
      if (!items || items.length === 0) {
        container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No items found</p>';
        return;
      }
      container.innerHTML = items.map(item => `
        <div class="list-item" onclick="selectKnowledgeItem('${item.id}', '${item.code}')" style="cursor: pointer;">
          <div class="list-item-header">
            <span style="font-weight: 600;">${item.title || item.code}...
}
```

---

## renderKnowledgeListPagination

- **用途**: Render knowledge list pagination
- **Async**: ❌
- **参数**: `(totalCount)`
- **行数**: 9
- **调用**: t
- **被调用**: loadKnowledgeList

```javascript
function renderKnowledgeListPagination(totalCount) {
  const container = $("knowledgeListPagination");
      const totalPages = Math.ceil(totalCount / kbListLimit);
      if (totalPages <= 1) {
        container.innerHTML = '';
        return;
      }
      container.innerHTML = `
        <button class="btn btn-sm" onclick="loadMoreKnowledgeList()" ${kbListOffset >= totalCount - kbListLimit ? 'disabled' : ''}>Load More</button>
      `;...
}
```

---

## renderMarkdown

- **用途**: Simple markdown to HTML
- **Async**: ❌
- **参数**: `(text)`
- **行数**: 11
- **调用**: t, escapeHtml
- **被调用**: init_skill_manage_fn

```javascript
function renderMarkdown(text) {
  if (!text) return "";
      return escapeHtml(text)
        .replace(/^### (.+)$/gm, '<h3 style="margin:12px 0 6px;">$1</h3>')
        .replace(/^## (.+)$/gm, '<h2 style="margin:14px 0 8px;">$1</h2>')
        .replace(/^# (.+)$/gm, '<h1 style="margin:16px 0 10px;">$1</h1>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.+?)`/g, '<code style="background:var(--bg);padding:1px 4px;border-radius:3px;">$1</code>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        ....
}
```

---

## renderMarketTemplates

- **用途**: Render prompt template marketplace
- **Async**: ❌
- **参数**: `(templates)`
- **行数**: 23
- **调用**: t, escapeHtml
- **被调用**: init, loadMarketTemplates

```javascript
function renderMarketTemplates(templates) {
  $("marketPopularList").innerHTML = templates.slice(0, 3).map(function(t) {
          return '<div class="market-card" onclick="openMarketDetail(\'' + (t.key || t.id) + '\')">' +
            '<div class="market-card-header">' +
              '<span class="market-card-name">' + escapeHtml(t.name || t.key) + '</span>' +
            '</div>' +
            '<div class="market-card-desc">' + escapeHtml(t.description || "") + '</div>' +
            '<div class="market-card-meta">' +
              '<spa...
}
```

---

## renderModelProfiles

- **用途**: Render model profile list
- **Async**: ❌
- **参数**: `(profiles)`
- **行数**: 20
- **调用**: t
- **被调用**: init

```javascript
function renderModelProfiles(profiles) {
  const container = $("modelProfilesResult");
        if (!profiles || profiles.length === 0) {
          container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No model profiles</p>';
          return;
        }
        container.innerHTML = profiles.map(p => `
          <div class="list-item" onclick="selectModelProfile('${p.profile_key}')">
            <div class="list-item-header">
              <span>${p.display_name}</span>
              <div style="display:flex...
}
```

---

## renderOfflineQueue

- **用途**: Render offline sync queue
- **Async**: ❌
- **参数**: `()`
- **行数**: 19
- **调用**: api, t, escapeHtml
- **被调用**: init

```javascript
function renderOfflineQueue() {
  // Show local projects that need sync
        api("/api/tool", { tool: "local.project.list", arguments: {} }).then(function(result) {
          var projects = (result && result.projects) ? result.projects : [];
          $("offlineQueueCount").textContent = projects.length;
          if (projects.length > 0) {
            $("offlineQueueList").innerHTML = projects.map(function(p) {
              return '<div class="offline-queue-item">' +
                '<div class="offline-queue-header">' +
  ...
}
```

---

## renderPagination

- **用途**: Render pagination controls
- **Async**: ❌
- **参数**: `(containerId, currentPage, totalPages, loadFn)`
- **行数**: 13
- **调用**: t
- **被调用**: init

```javascript
function renderPagination(containerId, currentPage, totalPages, loadFn) {
  var container = $(containerId);
        if (!container || totalPages <= 1) { if (container) container.innerHTML = ""; return; }
        var html = '<button class="pagination-btn" ' + (currentPage <= 1 ? 'disabled' : '') + ' onclick="' + loadFn + '(' + (currentPage - 1) + ')">‹</button>';
        var start = Math.max(1, currentPage - 2);
        var end = Math.min(totalPages, currentPage + 2);
        if (start > 1) { html += '<button class="pagination-btn" onclick="' + loadFn + '(1)">1</button>'...
}
```

---

## renderRelationList

- **用途**: Render relationship list
- **Async**: ❌
- **参数**: `(relations)`
- **行数**: 19
- **调用**: t
- **被调用**: init

```javascript
function renderRelationList(relations) {
  const container = $("relationListResult");
      if (!relations || relations.length === 0) {
        container.innerHTML = '<p style="color:var(--muted);">No relationships found</p>';
        return;
      }
      container.innerHTML = relations.map(rel => `
        <div class="result-item">
          <strong>${rel.source_name || rel.source_entity_id}</strong>
          <span style="color:var(--muted);"> → ${rel.relation_type} → </span>
          <strong>${rel.target_name || rel.target_entity_id...
}
```

---

## renderReviewDetail

- **用途**: Render review detail panel
- **Async**: ❌
- **参数**: `(item)`
- **行数**: 39
- **调用**: t
- **被调用**: selectReviewItem

```javascript
function renderReviewDetail(item) {
  $("kbReviewDetail").innerHTML = `
        <div style="margin-bottom: 16px;">
          <h3 style="margin-bottom: 8px;">${item.title || item.code}</h3>
          <div style="display:flex;gap:8px;margin-bottom:12px;">
            <span class="badge ${item.review_status === 'pending' ? 'badge-warning' : item.review_status === 'approved' ? 'badge-success' : 'badge-danger'}">
              ${item.review_status}
            </span>
            <span class="badge" style="background: var(--accent-light)...
}
```

---

## renderReviewList

- **用途**: Render review list
- **Async**: ❌
- **参数**: `(items)`
- **行数**: 24
- **调用**: t
- **被调用**: loadReviewList

```javascript
function renderReviewList(items) {
  const container = $("kbReviewList");
      if (!items || items.length === 0) {
        container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No review items found</p>';
        return;
      }
      container.innerHTML = items.map(item => `
        <div class="list-item" onclick="selectReviewItem('${item.review_id}')" style="cursor: pointer;">
          <div class="list-item-header">
            <span style="font-weight: 600;">${item.title || item.code}</span>
    ...
}
```

---

## renderRevisionTasks

- **用途**: Render revision tasks
- **Async**: ❌
- **参数**: `(tasks)`
- **行数**: 27
- **调用**: t, escapeHtml
- **被调用**: init

```javascript
function renderRevisionTasks(tasks) {
  const container = $("revisionTasksResult");
        const countBadge = $("revisionTasksCount");
        if (!tasks || tasks.length === 0) {
          container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No revision tasks</p>';
          countBadge.textContent = "0";
          return;
        }
        countBadge.textContent = tasks.length;
        const criticalCount = tasks.filter(t => t.severity === "critical").length;
        if (criticalCount > 0) {
          ...
}
```

---

## renderRuleProposals

- **用途**: Render rule proposals list
- **Async**: ❌
- **参数**: `(proposals)`
- **行数**: 19
- **调用**: t
- **被调用**: init

```javascript
function renderRuleProposals(proposals) {
  const container = $("ruleProposalsResult");
        if (!proposals || proposals.length === 0) {
          container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No rule proposals</p>';
          return;
        }
        container.innerHTML = proposals.map(p => `
          <div class="list-item" onclick="selectRuleProposal('${p.id}')">
            <div class="list-item-header">
              <span>${p.rule_key || p.title}</span>
              <div style="display:fle...
}
```

---

## renderRulesResult

- **用途**: Render rules search result
- **Async**: ❌
- **参数**: `(data, title, containerId)`
- **行数**: 22
- **调用**: t
- **被调用**: init

```javascript
function renderRulesResult(data, title, containerId) {
  const container = $(containerId);
      if (!container) return;
      if (!data || (Array.isArray(data) && data.length === 0)) {
        container.innerHTML = `<p style="color:var(--muted);">${title || 'No results'}</p>`;
        return;
      }
      if (Array.isArray(data)) {
        container.innerHTML = data.map(item => `
          <div class="result-item">
            <strong>${item.title || item.key || item.rule_key || item.id || 'Rule'}</strong>
            ${item.status ? `<span class="b...
}
```

---

## renderSnapshotList

- **用途**: Render state snapshot list
- **Async**: ❌
- **参数**: `(snapshots)`
- **行数**: 14
- **调用**: t
- **被调用**: init

```javascript
function renderSnapshotList(snapshots) {
  const container = $("snapshotListResult");
      if (!snapshots || snapshots.length === 0) {
        container.innerHTML = '<p style="color:var(--muted);">No snapshots found</p>';
        return;
      }
      container.innerHTML = snapshots.map(snap => `
        <div class="result-item">
          <strong>Chapter ${snap.chapter_no || 'N/A'}</strong>
          ${snap.is_current ? '<span class="badge badge-success">current</span>' : ''}
          <span class="badge badge-warning">${snap.duration_...
}
```

---

## renderStepList

- **用途**: Render skill step list
- **Async**: ❌
- **参数**: `()`
- **行数**: 13
- **调用**: t, escapeHtml
- **被调用**: openSkillEdit, removeStep, saveStep

```javascript
function renderStepList() {
  const container = $("skillStepList");
      if (skillCurrentSteps.length === 0) {
        container.innerHTML = `<p style="color:var(--muted);font-size:12px;">No steps</p>`;
        return;
      }
      container.innerHTML = skillCurrentSteps.map((step, i) => `
        <div style="padding:6px 8px;background:var(--bg);border-radius:4px;margin-bottom:4px;display:flex;align-items:center;gap:8px;font-size:12px;">
          <span style="font-weight:500;">${step.step_order}.</span>
          <span st...
}
```

---

## renderTemplates

- **用途**: Render template list
- **Async**: ❌
- **参数**: `(templates)`
- **行数**: 19
- **调用**: t, escapeHtml
- **被调用**: init

```javascript
function renderTemplates(templates) {
  const container = $("templateListResult");
        if (!templates || templates.length === 0) {
          container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No templates</p>';
          return;
        }
        container.innerHTML = templates.map(t => `
          <div class="template-card" onclick="selectTemplate('${t.id}')">
            <div class="template-card-header">
              <span class="template-card-name">${escapeHtml(t.name)}</span>
              <...
}
```

---

## renderThreads

- **用途**: Render plot threads
- **Async**: ❌
- **参数**: `(threads)`
- **行数**: 22
- **调用**: t
- **被调用**: init

```javascript
function renderThreads(threads) {
  const container = $("threadsResult");
        const countBadge = $("threadsCount");
        if (!threads || threads.length === 0) {
          container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No threads</p>';
          countBadge.textContent = "0";
          return;
        }
        countBadge.textContent = threads.length;
        container.innerHTML = threads.map(t => `
          <div class="list-item" onclick="selectThread('${t.key}')">
            <div clas...
}
```

---

## renderTreeNode

- **用途**: Render single tree node
- **Async**: ❌
- **参数**: `(slug, depth)`
- **行数**: 26
- **调用**: t
- **被调用**: renderUkTree

```javascript
function renderTreeNode(slug, depth) {
  const node = ukTreeData[slug];
      if (!node) return "";
      const hasChildren = node.children && node.children.length > 0;
      const isExpanded = ukExpandedNodes.has(slug);
      const isSelected = ukCurrentCategory === slug;
      const indent = depth * 16;
      const icon = hasChildren ? (isExpanded ? "▾" : "▸") : "·";
      const itemCount = getNodeCount(slug);

      let html = `<div class="uk-tree-item" style="cursor:pointer;padding:6px 12px 6px ${12 + indent}px;display:flex;align-i...
}
```

---

## renderUkTree

- **用途**: Render UK tree view
- **Async**: ❌
- **参数**: `()`
- **行数**: 24
- **调用**: t
- **被调用**: initUkManage, loadUkTree

```javascript
function renderUkTree() {
  console.log(">>> renderUkTree CALLED <<<");
      const container = $("ukCatTree");
      console.log("container:", container);
      if (!container) {
        console.log("renderUkTree: container is NULL, returning early");
        return;
      }

      const totalItems = ukCategoryCounts["_total"] || 0;
      let html = `<div class="uk-tree-item" style="cursor:pointer;padding:8px 12px;font-weight:600;${!ukCurrentCategory ? 'background:var(--accent-light);border-radius:4px;' : ''}" onclick="se...
}
```

---

## renderVolumes

- **用途**: Render volumes list
- **Async**: ❌
- **参数**: `(volumes)`
- **行数**: 17
- **调用**: t, escapeHtml
- **被调用**: init

```javascript
function renderVolumes(volumes) {
  const container = $("volumesResult");
        if (!volumes || volumes.length === 0) {
          container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No volumes</p>';
          return;
        }
        container.innerHTML = volumes.map(v => `
          <div class="list-item" onclick="selectVolume(${v.volume_no})">
            <div class="list-item-header">
              <span>Vol. ${v.volume_no}: ${v.title || 'Untitled'}</span>
              <span class="badge ${v...
}
```

---

## resetKnowledgeList

- **用途**: Reset knowledge list to default
- **Async**: ❌
- **参数**: `()`
- **行数**: 5
- **调用**: t, loadKnowledgeList
- **被调用**: 无

```javascript
function resetKnowledgeList() {
  $("kbListCategory").value = "";
      $("kbListSource").value = "";
      $("kbListLevel").value = "";
      kbListOffset = 0;
      loadKnowledgeList();...
}
```

---

## runPipeline

- **用途**: Run generation pipeline
- **Async**: ✅
- **参数**: `()`
- **行数**: 50
- **调用**: showToast, baseProjectArgs, api, loadLocalChapters, t, setStatus, show
- **被调用**: init

```javascript
function runPipeline() {
  var projectId = $("pipelineProjectSelect").value;
      var chapterNo = parseInt($("pipelineChapterNo").value);
      var targetWords = parseInt($("pipelineTargetWords").value);
      var purpose = $("pipelinePurpose").value;
      if (!projectId) { showToast("warning", "请先选择项目"); return; }
      if (!chapterNo) { showToast("warning", "请输入章节号"); return; }

      $("pipelineStatus").style.display = "none";
      $("pipelineResult").style.display = "block";
      $("pipelinePassStatus").textConten...
}
```

---

## saveBackupSchedule

- **用途**: Save backup schedule
- **Async**: ✅
- **参数**: `()`
- **行数**: 6
- **调用**: showToast, baseProjectArgs, api, t, show
- **被调用**: init

```javascript
function saveBackupSchedule() {
  var interval = parseInt($("backupInterval").value);
      if (!interval || interval < 1) { showToast("warning", "请输入有效间隔"); return; }
      var result = await api("/api/tool", { tool: "backup.schedule.upsert", arguments: Object.assign(baseProjectArgs(), { interval_hours: interval, enabled: true }) });
      if (result && !result.error) {
        showToast("success", "备份计划已保存");
      }...
}
```

---

## saveCategory

- **用途**: Save category changes
- **Async**: ✅
- **参数**: `()`
- **行数**: 19
- **调用**: t
- **被调用**: initUkManage

```javascript
function saveCategory() {
  const id = $("ukCatEditId").value;
      const name = $("ukCatName").value.trim();
      const slug = $("ukCatSlug").value.trim();
      const parentId = $("ukCatParent").value || null;
      const desc = $("ukCatDesc").value.trim();
      if (!name || !slug) { setStatus(t("uk.nameAndSlugRequired")); return; }
      if (id) {
        const result = await api("/api/tool", { tool: "kb.category.update", arguments: {
          category_id: id, name, slug, description: desc || null, parent_id: parent...
}
```

---

## saveKnowledgeEditor

- **用途**: Save knowledge item from editor
- **Async**: ✅
- **参数**: `(source, itemId)`
- **行数**: 33
- **调用**: t, loadKnowledgeItems
- **被调用**: renderKnowledgeEditor

```javascript
function saveKnowledgeEditor(source, itemId) {
  const code = $("kbEditCode").value;
      const title = $("kbEditTitle").value;
      const content = $("kbEditContent").value;
      const summary = $("kbEditSummary").value;
      const examples = $("kbEditExamples").value;
      const counterExamples = $("kbEditCounterExamples").value;
      
      if (!title || !content) {
        showToast("warning", "Title and Content are required");
        return;
      }
      
      const toolName = source === "user" ? "knowledge.user.upsert" : "knowle...
}
```

---

## saveKnowledgePack

- **用途**: Save knowledge pack config
- **Async**: ✅
- **参数**: `()`
- **行数**: 6
- **调用**: showToast, api, t, setStatus, show
- **被调用**: init

```javascript
function saveKnowledgePack() {
  if (!currentPackProjectId) { showToast("warning", "请先选择项目"); return; }
      setStatus("保存知识包配置...");
      var result = await api("/api/tool", { tool: "kb.pack.update", arguments: { project_id: currentPackProjectId, active_categories: currentPackActive } });
      if (result && !result.error) {
        showToast("success", "知识包配置已保存");
      }...
}
```

---

## saveNewKnowledgeItem

- **用途**: Save new knowledge item
- **Async**: ✅
- **参数**: `()`
- **行数**: 20
- **调用**: t, loadKnowledgeItems
- **被调用**: createNewKnowledgeItem

```javascript
function saveNewKnowledgeItem() {
  const title = $("kbNewTitle").value;
      const content = $("kbNewContent").value;
      const summary = $("kbNewSummary").value;
      
      if (!title || !content) {
        showToast("warning", "Title and Content are required");
        return;
      }
      
      const args = { title, content, summary };
      if (selectedCategorySlug) {
        args.category_slug = selectedCategorySlug;
      }
      
      const result = await api("/api/tool", { tool: "knowledge.user.upsert", arguments:...
}
```

---

## saveSkill

- **用途**: Save skill changes
- **Async**: ✅
- **参数**: `()`
- **行数**: 41
- **调用**: selectSkill, api, loadSkillList, t, setStatus
- **被调用**: init_skill_manage_fn

```javascript
function saveSkill() {
  const id = $("skillEditId").value;
      const name = $("skillEditName").value.trim();
      if (!name) { setStatus("Name required"); return; }
      const desc = $("skillEditDesc").value.trim() || null;
      const triggers = $("skillEditTriggers").value.split(",").map(s => s.trim()).filter(Boolean);
      const tools = $("skillEditTools").value.split(",").map(s => s.trim()).filter(Boolean);
      const sort = parseInt($("skillEditSort").value) || 0;
      const active = $("skillEditActive").ch...
}
```

---

## saveState

- **用途**: Save entity state changes
- **Async**: ❌
- **参数**: `()`
- **行数**: 4
- **调用**: t
- **被调用**: init

```javascript
function saveState() {
  for (const key of stateKeys) {
        const el = $(key);
        if (el) localStorage.setItem("novel_os_" + key, el.value);
      }...
}
```

---

## saveStep

- **用途**: Save skill step
- **Async**: ❌
- **参数**: `()`
- **行数**: 26
- **调用**: t, renderStepList
- **被调用**: init_skill_manage_fn

```javascript
function saveStep() {
  const name = $("skillStepName").value.trim();
      const order = parseInt($("skillStepOrder").value);
      if (!name || !order) return;

      let params = {};
      try { params = JSON.parse($("skillStepParams").value || "{}"); } catch(e) {}

      const stepData = {
        step_order: order,
        step_name: name,
        tool_name: $("skillStepTool").value.trim() || null,
        description: $("skillStepDesc").value.trim() || null,
        parameters: params,
        optional: $("skillS...
}
```

---

## saveUkEntry

- **用途**: Save UK entry
- **Async**: ✅
- **参数**: `()`
- **行数**: 21
- **调用**: t, loadUkItems
- **被调用**: initUkManage

```javascript
function saveUkEntry() {
  const id = $("ukEditId").value;
      const topic = $("ukEditTopic").value.trim();
      if (!topic) { setStatus(t("uk.topic") + " " + t("status.error")); return; }
      const catSlug = $("ukEditCategory").value;
      const tags = $("ukEditTags").value.split(",").map(s => s.trim()).filter(Boolean);
      if (id) {
        const result = await api("/api/tool", { tool: "kb.uk.update", arguments: {
          entry_id: id, topic, summary: $("ukEditSummary").value, content: $("ukEditContent").value...
}
```

---

## scanLocalProject

- **用途**: Scan local project directory
- **Async**: ✅
- **参数**: `()`
- **行数**: 12
- **调用**: showToast, loadLocalProjects, api, t, setStatus, show
- **被调用**: init

```javascript
function scanLocalProject() {
  var projectId = $("localProjectId").value.trim();
      var localPath = $("localProjectPath").value.trim();
      if (!projectId || !localPath) { showToast("warning", "请填写项目 ID 和目录路径"); return; }
      setStatus("扫描项目目录...");
      var result = await api("/api/tool", {
        tool: "local.project.scan",
        arguments: { project_id: projectId, local_root: localPath }
      });
      if (result && !result.error) {
        showToast("success", "扫描完成", result.chapters.length + " 章节, " + result....
}
```

---

## scanProject

- **用途**: Scan project files
- **Async**: ✅
- **参数**: `(projectId, localPath)`
- **行数**: 9
- **调用**: showToast, loadLocalProjects, api, t, setStatus, show
- **被调用**: init, loadLocalProjects

```javascript
function scanProject(projectId, localPath) {
  setStatus("扫描 " + projectId + "...");
      var result = await api("/api/tool", {
        tool: "local.project.scan",
        arguments: { project_id: projectId, local_root: localPath }
      });
      if (result && !result.error) {
        showToast("success", "扫描完成", result.chapters.length + " 章节");
        loadLocalProjects();
      }...
}
```

---

## selectCategory

- **用途**: Select category in tree
- **Async**: ✅
- **参数**: `(slug, name)`
- **行数**: 3
- **调用**: t
- **被调用**: buildTree, renderCategoryTree

```javascript
function selectCategory(slug, name) {
  selectedCategorySlug = slug;
      $("kbItemListTitle").textContent = name ? `${name} (${slug})` : "Items";
      await loadKnowledgeItems();...
}
```

---

## selectKnowledgeItemEdit

- **用途**: Select item for editing
- **Async**: ✅
- **参数**: `(itemId, code, source)`
- **行数**: 19
- **调用**: t
- **被调用**: renderKnowledgeItemList

```javascript
function selectKnowledgeItemEdit(itemId, code, source) {
  selectedItemId = itemId;
      selectedItemType = source;
      $("kbEditorCloseBtn").style.display = "block";
      
      const toolName = source === "user" ? "knowledge.user.get" : "knowledge.item.get";
      const args = source === "user" ? { item_id: itemId } : { item_id: itemId };
      
      console.log("selectKnowledgeItemEdit called:", { toolName, args });
      
      const result = await api("/api/tool", { tool: toolName, arguments: args });
      
      console.log("API result:", re...
}
```

---

## selectReviewItem

- **用途**: Select review item to view
- **Async**: ✅
- **参数**: `(reviewId)`
- **行数**: 4
- **调用**: t
- **被调用**: renderReviewList, approveReview, rejectReview

```javascript
function selectReviewItem(reviewId) {
  const result = await api("/api/tool", { tool: "knowledge.review.get", arguments: { review_id: reviewId } });
      if (result.ok && result.result) {
        renderReviewDetail(result.result);
      }...
}
```

---

## selectSkill

- **用途**: Select skill to view/edit
- **Async**: ✅
- **参数**: `(id)`
- **行数**: 44
- **调用**: api, t, escapeHtml, loadSkillList
- **被调用**: loadSkillList, saveSkill, deleteSkillExecute

```javascript
function selectSkill(id) {
  skillCurrentId = id;
      $("skillDetailActions").style.display = "";
      $("skillDetailTitle").textContent = t("status.loading");
      $("skillDetailContent").innerHTML = "";
      const result = await api("/api/tool", { tool: "skill.get", arguments: { skill_id: id } });
      if (!result.ok || !result.result) {
        $("skillDetailTitle").textContent = "Skill not found";
        return;
      }
      const skill = result.result;
      skillCurrentSteps = skill.steps || [];
      $("skill...
}
```

---

## setStatus

- **用途**: Status bar message update
- **Async**: ❌
- **参数**: `(text)`
- **行数**: 2
- **调用**: t, show, showToast
- **被调用**: init_auto_search, saveCategory, confirmDeleteCategory, saveUkEntry, loadKnowledgeStats, loadKnowledgeList, loadMoreKnowledgeList, callTool, loadProjects, getActiveProjectArgs

```javascript
function setStatus(text) {
  console.log("Status:", text);
      showToast("info", text);...
}
```

---

## setupDropdown

- **用途**: Setup dropdown menu behavior
- **Async**: ❌
- **参数**: `(btnId, menuId)`
- **行数**: 10
- **调用**: t, closeAllDropdowns
- **被调用**: init

```javascript
function setupDropdown(btnId, menuId) {
  const btn = $(btnId);
      const menu = $(menuId);
      if (!btn || !menu) return;
      
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = menu.classList.contains("show");
        closeAllDropdowns();
        if (!isOpen) menu.classList.add("show");
      });...
}
```

---

## setupMenuGroups

- **用途**: Setup menu accordion groups
- **Async**: ❌
- **参数**: `()`
- **行数**: 66
- **调用**: t, goToPage
- **被调用**: init

```javascript
function setupMenuGroups() {
  // Menu section toggle (Level 1)
      document.querySelectorAll(".menu-section-header").forEach(header => {
        header.addEventListener("click", () => {
          const section = header.closest(".menu-section");
          if (!section) return;
          section.classList.toggle("collapsed");
          // Update ARIA
          header.setAttribute("aria-expanded", !section.classList.contains("collapsed"));
          // Save state to localStorage
          localStorage.setItem(`menu-section-${...
}
```

---

## show

- **用途**: Toggle element visibility
- **Async**: ❌
- **参数**: `(view)`
- **行数**: 3
- **调用**: t
- **被调用**: selectKnowledgeItemEdit, saveKnowledgeEditor, deleteKnowledgeItemEdit, submitKnowledgeForReview, createPrivateCopy, saveNewKnowledgeItem, approveReview, rejectReview, closeAllDropdowns, setupDropdown

```javascript
function show(view) {
  $("setupView").classList.toggle("hidden", view !== "setup");
      $("loginView").classList.toggle("hidden", view !== "login");
      $("appView").classList.toggle("hidden", view !== "app");...
}
```

---

## showToast

- **用途**: Toast notification display
- **Async**: ❌
- **参数**: `(type, title, msg, duration)`
- **行数**: 11
- **调用**: t, escapeHtml
- **被调用**: selectKnowledgeItemEdit, saveKnowledgeEditor, deleteKnowledgeItemEdit, submitKnowledgeForReview, createPrivateCopy, saveNewKnowledgeItem, approveReview, rejectReview, api, setStatus

```javascript
function showToast(type, title, msg, duration) {
  duration = duration || 4000;
      var container = $("toastContainer");
      var icons = { success: "✓", error: "✕", warning: "⚠", info: "ℹ" };
      var el = document.createElement("div");
      el.className = "toast " + type;
      el.innerHTML = '<span class="toast-icon">' + (icons[type] || "ℹ") + '</span>' +
        '<div class="toast-body"><div class="toast-title">' + escapeHtml(title) + '</div>' +
        (msg ? '<div class="toast-msg">' + escapeHtml(msg) + '</div>' : '') + '</div>' +
   ...
}
```

---

## submitKnowledgeForReview

- **用途**: Submit knowledge for admin review
- **Async**: ✅
- **参数**: `(itemId)`
- **行数**: 8
- **调用**: t, loadKnowledgeItems
- **被调用**: renderKnowledgeEditor

```javascript
function submitKnowledgeForReview(itemId) {
  const reason = prompt("Enter reason for review submission:");
      if (!reason) return;
      
      const result = await api("/api/tool", { tool: "knowledge.user.submit_review", arguments: { item_id: itemId, reason } });
      if (result.ok) {
        showToast("success", "Submitted for review successfully");
        await loadKnowledgeItems();
      }...
}
```

---

## t

- **用途**: Internationalization lookup
- **Async**: ❌
- **参数**: `(key)`
- **行数**: 1
- **调用**: 无
- **被调用**: escapeHtml, updateTokenState, applyLanguage, loadModule, loadKnowledgeModule, init_auto_search, init_knowledge_graph, loadKnowledgeGraphCategory, init_knowledge_expiry, initUkManage

```javascript
function t(key) {
  return translations[currentLanguage][key] || translations.en[key] || key;...
}
```

---

## toggleCategory

- **用途**: Toggle category enabled/disabled
- **Async**: ❌
- **参数**: `(cat)`
- **行数**: 17
- **调用**: t, escapeHtml, toggleCategory
- **被调用**: buildTree, renderCategoryTree, init, loadKnowledgePack

```javascript
function toggleCategory(cat) {
  var idx = currentPackActive.indexOf(cat);
      if (idx >= 0) {
        currentPackActive.splice(idx, 1);
      } else {
        currentPackActive.push(cat);
      }
      // Re-render
      var activeHtml = currentPackActive.map(function(c) {
        return '<span class="badge badge-success" style="cursor:pointer;padding:8px 12px;" onclick="toggleCategory(\'' + c + '\')">' + escapeHtml(c) + ' ✕</span>';
      }).join("");
      $("packActiveCategories").innerHTML = activeHtml;

      var inacti...
}
```

---

## toggleSidebar

- **用途**: Toggle sidebar collapse
- **Async**: ❌
- **参数**: `()`
- **行数**: 3
- **调用**: t
- **被调用**: init

```javascript
function toggleSidebar() {
  sidebarCollapsed = !sidebarCollapsed;
      $("sidebar").classList.toggle("collapsed", sidebarCollapsed);
      $("mainContent").classList.toggle("expanded", sidebarCollapsed);...
}
```

---

## updateConnectionStatus

- **用途**: Update online/offline status
- **Async**: ❌
- **参数**: `()`
- **行数**: 20
- **调用**: t
- **被调用**: init

```javascript
function updateConnectionStatus() {
  const label = $("connectionStatusLabel");
        const dot = $("connectionStatusDot");
        const detail = $("connectionStatusDetail");

        const isOnline = navigator.onLine;
        if (isOnline) {
          label.textContent = t("offline.online");
          dot.className = "offline-status-dot offline-status-online";
          detail.innerHTML = `
            <div class="offline-status-item">Network: Available</div>
            <div class="offline-status-item">Last Sync: ${new Date().t...
}
```

---

## updateProjectDropdowns

- **用途**: Update all project select dropdowns
- **Async**: ❌
- **参数**: `(projects)`
- **行数**: 9
- **调用**: t, escapeHtml
- **被调用**: init, loadLocalProjects

```javascript
function updateProjectDropdowns(projects) {
  var selects = ["chapterProjectSelect", "pipelineProjectSelect"];
      selects.forEach(function(id) {
        var el = $(id);
        if (!el) return;
        var current = el.value;
        el.innerHTML = '<option value="">选择项目</option>' +
          projects.map(function(p) { return '<option value="' + p.project_id + '">' + escapeHtml(p.project_id) + ' — ' + escapeHtml(p.local_root || "") + '</option>'; }).join("");
        if (current) el.value = current;
      });...
}
```

---

## updateTokenState

- **用途**: Update token state UI
- **Async**: ❌
- **参数**: `(hasToken)`
- **行数**: 2
- **调用**: t
- **被调用**: applyLanguage, refreshAuth, init

```javascript
function updateTokenState(hasToken) {
  const el = $("tokenState");
      if (el) el.textContent = hasToken ? t("status.tokenStored") : t("status.tokenMissing");...
}
```

---

## viewChapterDetail

- **用途**: View chapter detail
- **Async**: ✅
- **参数**: `(chapterNo)`
- **行数**: 23
- **调用**: api, t, escapeHtml, setStatus
- **被调用**: init, loadLocalChapters

```javascript
function viewChapterDetail(chapterNo) {
  if (!currentLocalProjectId) return;
      setStatus("加载章节详情...");
      var result = await api("/api/tool", {
        tool: "local.chapter.get",
        arguments: { project_id: currentLocalProjectId, chapter_no: chapterNo }
      });
      var el = $("localChapterDetail");
      if (result && !result.error) {
        el.style.display = "block";
        el.innerHTML = '<h3 style="font-size:14px;font-weight:600;margin-bottom:12px;">第 ' + chapterNo + ' 章</h3>' +
          '<div style="display:grid...
}
```

---

## viewProjectStats

- **用途**: View project statistics
- **Async**: ✅
- **参数**: `(projectId)`
- **行数**: 5
- **调用**: showToast, api, t, setStatus, show
- **被调用**: init, loadLocalProjects

```javascript
function viewProjectStats(projectId) {
  setStatus("加载统计...");
      var result = await api("/api/tool", { tool: "local.stats", arguments: { project_id: projectId } });
      if (result && !result.error) {
        showToast("info", projectId + " 统计", result.chapter_count + " 章, " + result.total_words + " 字");
      }...
}
```

---

## warmCache

- **用途**: Warm up cache
- **Async**: ✅
- **参数**: `()`
- **行数**: 6
- **调用**: t, api, show, showToast
- **被调用**: init

```javascript
function warmCache() {
  var key = $("cacheWarmKey").value.trim();
      if (!key) { showToast("warning", "请输入缓存键"); return; }
      var result = await api("/api/tool", { tool: "system.cache.warm", arguments: { key: key } });
      if (result && !result.error) {
        showToast("success", "缓存已预热");
      }...
}
```

---

