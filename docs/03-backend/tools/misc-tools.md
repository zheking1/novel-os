# Miscellaneous Tools — 多样工具集合 (Part 1)

> Sources: `tools/setting.py`, `tools/prompt.py`, `tools/skill.py`, `tools/graph.py`, `tools/evolution.py`, `tools/reference.py`, `tools/global_rules.py`, `tools/vector.py`, `tools/sync.py`, `tools/local.py`, `tools/archive.py`, `tools/novel_wizard.py`, `tools/novel_gen.py`

---

## Setting Tools — 设定管理

> Source: `tools/setting.py` | Service: `global_settings_service`

### setting.category.list

```python
async def setting_category_list(workspace: str, is_active: bool | None = True) -> list[dict[str, Any]]
```

### setting.category.get

```python
async def setting_category_get(workspace: str, category_id: str | None = None, slug: str | None = None) -> dict[str, Any]
```

### setting.category.upsert

```python
async def setting_category_upsert(
    workspace: str, slug: str, name: str,
    description: str | None = None, icon: str = "book", sort_order: int = 0,
    is_standard: bool = False, metadata: dict | None = None,
) -> dict[str, Any]
```

### setting.category.delete

```python
async def setting_category_delete(workspace: str, category_id: str) -> dict[str, Any]
```

### setting.item.list

```python
async def setting_item_list(
    workspace: str, category_id: str | None = None,
    is_global: bool | None = None, level: str | None = None,
    tags: list[str] | None = None, limit: int = 100, offset: int = 0,
) -> list[dict[str, Any]]
```

### setting.item.get

```python
async def setting_item_get(workspace: str, item_id: str | None = None, item_code: str | None = None) -> dict[str, Any]
```

### setting.item.upsert

```python
async def setting_item_upsert(
    workspace: str, category_id: str, core_summary: str,
    item_code: str | None = None, keywords: list[str] | None = None,
    intent_synonyms: list[str] | None = None,
    detailed_expansion: str | None = None, ai_instruction: str | None = None,
    poison_points: list[str] | None = None, level: str = "knowledge",
    applicable_skills: list[str] | None = None,
    applicable_genres: list[str] | None = None,
    data: dict | None = None, tags: list[str] | None = None,
    is_global: bool = False, sort_order: int = 0,
    metadata: dict | None = None,
) -> dict[str, Any]
```

**Level options:** `knowledge` / `system` / `world` / `writing_tip` / `advanced`

### setting.item.bulk_upsert / .delete / .search

```python
async def setting_item_bulk_upsert(workspace: str, category_id: str, items: list[dict]) -> dict[str, Any]
async def setting_item_delete(workspace: str, item_id: str) -> dict[str, Any]
async def setting_search(workspace: str, query: str, category_id: str | None = None, level: str | None = None, skill: str | None = None, genre: str | None = None, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]
```

### setting.genre — 题材

```python
async def setting_genre_list() -> list[dict[str, Any]]
async def setting_genre_resolve(input_text: str) -> dict[str, Any]
async def setting_genre_delete(slug: str) -> dict[str, Any]
```

### setting.csv

```python
async def setting_csv_import(workspace: str, category_id: str, csv_content: str) -> dict[str, Any]
async def setting_csv_export(workspace: str, category_id: str | None = None) -> str
```

**DB Tables:** `setting_categories`, `setting_items`

---

## Prompt Tools — 模板、权重、素材等

> Source: `tools/prompt.py`

### prompt.template.upsert

```python
async def prompt_template_upsert(
    workspace: str, project: str, template_key: str, name: str,
    template_content: str, description: str | None = None,
    template_type: str = "system", variables: list[dict] | None = None,
    genre: str | None = None, scene: str | None = None,
) -> dict[str, Any]
```

### prompt.template — get / list / render / delete

```python
async def prompt_template_get(workspace: str, project: str, template_key: str) -> dict[str, Any] | None
async def prompt_template_list(workspace: str, project: str | None = None, genre: str | None = None, scene: str | None = None, template_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]
async def prompt_template_render(workspace: str, project: str, template_key: str, variables: dict) -> dict[str, Any]
async def prompt_template_delete(workspace: str, project: str, template_key: str) -> dict[str, Any]
```

**DB Tables:** `prompt_templates` | **Service:** `prompt_template_service`

---

### context.weight — 上下文权重

```python
async def context_weight_upsert(workspace: str, project: str, config_name: str, weights: dict, profile: str | None = None, max_total_tokens: int | None = None, priority_order: list[str] | None = None) -> dict[str, Any]
async def context_weight_get(workspace: str, project: str, config_name: str, profile: str | None = None) -> dict[str, Any]
async def context_weight_list(workspace: str, project: str, profile: str | None = None) -> list[dict[str, Any]]
```

**DB Tables:** `context_weight_configs` | **Service:** `context_weight_service`

---

### material — 参考素材

```python
async def material_upsert(workspace: str, project: str, material_key: str, title: str, material_type: str, content: str | None = None, category: str | None = None, tags: list[str] | None = None, source_url: str | None = None) -> dict[str, Any]
async def material_get(workspace: str, project: str, material_key: str) -> dict[str, Any]
async def material_list(workspace: str, project: str, material_type: str | None = None, category: str | None = None, tags: list[str] | None = None, favorite: bool | None = None, search: str | None = None, limit: int = 50) -> list[dict[str, Any]]
async def material_favorite(workspace: str, project: str, material_key: str) -> dict[str, Any]
```

**DB Tables:** `reference_materials` | **Service:** `reference_material_service`

---

### expectation — 读者期待 (已废弃)

**IMPORTANT:** 已废弃，请使用 `plot.upsert_foreshadowing` 代替。

```python
async def expectation_upsert(workspace: str, project: str, expectation_key: str, title: str, expectation_type: str, description: str | None = None, chapter_no: int | None = None, importance: str = "medium", tags: list[str] | None = None) -> dict[str, Any]
async def expectation_list(workspace: str, project: str, status: str | None = None, expectation_type: str | None = None, importance: str | None = None, limit: int = 50) -> list[dict[str, Any]]
async def expectation_fulfill(workspace: str, project: str, expectation_key: str, payoff_chapter_no: int) -> dict[str, Any]
```

---

### annotation — 章节批注

```python
async def annotation_create(workspace: str, project: str, chapter_id: str, chapter_no: int, annotation_type: str, content: str, anchor_start: int | None = None, anchor_end: int | None = None, parent_id: str | None = None) -> dict[str, Any]
async def annotation_list(workspace: str, project: str, chapter_id: str | None = None, annotation_type: str | None = None, resolve_status: str | None = None) -> list[dict[str, Any]]
async def annotation_resolve(workspace: str, project: str, annotation_id: str) -> dict[str, Any]
```

**DB Tables:** `chapter_annotations` | **Service:** `chapter_annotation_service`

---

### noun — 专有名词

```python
async def noun_upsert(workspace: str, project: str, noun_key: str, noun_value: str, noun_type: str, aliases: list[str] | None = None, description: str | None = None, locked: bool = False, first_chapter_no: int | None = None) -> dict[str, Any]
async def noun_list(workspace: str, project: str, noun_type: str | None = None, locked: bool | None = None, search: str | None = None) -> list[dict[str, Any]]
async def noun_check(workspace: str, project: str, text: str) -> dict[str, Any]
```

**DB Tables:** `proper_nouns` | **Service:** `proper_noun_service`

---

### search.fulltext / .index

```python
async def search_fulltext(workspace: str, project: str, query: str, source_types: list[str] | None = None, limit: int = 20) -> list[dict[str, Any]]
async def search_index(workspace: str, project: str, source_type: str, source_id: str, title: str, content: str, source_key: str | None = None) -> dict[str, Any]
```

**Source types:** `chapter` / `knowledge` / `entity` / `rule` / `setting`

**DB Tables:** `fulltext_index` | **Service:** `fulltext_search_service`

---

## Graph Tools — 实体关系图

> Source: `tools/graph.py`

```python
async def graph_get_data(workspace: str, project: str, entity_types: list[str] | None = None, depth: int = 2) -> dict[str, Any]
async def graph_get_subgraph(workspace: str, project: str, center_entity: str, depth: int = 1) -> dict[str, Any]
async def graph_get_timeline(workspace: str, project: str, entity_name: str) -> list[dict[str, Any]]
```

**DB Tables:** `state_entities`, `entity_relationships`

---

## Skill Tools — 技能管理

> Source: `tools/skill.py`

```python
async def skill_list(active_only: bool = True) -> list[dict[str, Any]]
async def skill_get(skill_id: str) -> dict[str, Any] | None
async def skill_get_by_name(name: str) -> dict[str, Any] | None
async def skill_create(name: str, description: str | None = None, content: str | None = None, trigger_words: list[str] | None = None, tool_hints: list[str] | None = None, sort_order: int = 0) -> dict[str, Any]
async def skill_update(skill_id: str, name: str | None = None, description: str | None = None, content: str | None = None, trigger_words: list[str] | None = None, tool_hints: list[str] | None = None, is_active: bool | None = None, sort_order: int | None = None) -> dict[str, Any]
async def skill_delete(skill_id: str) -> dict[str, Any]

async def skill_step_list(skill_id: str) -> list[dict[str, Any]]
async def skill_step_add(skill_id: str, step_order: int, action_type: str, params: dict | None = None, description: str | None = None, required: bool = True) -> dict[str, Any]
async def skill_step_update(step_id: str, step_order: int | None = None, action_type: str | None = None, params: dict | None = None, description: str | None = None, required: bool | None = None) -> dict[str, Any]
async def skill_step_delete(step_id: str) -> dict[str, Any]
```

**Action types:** `tool_call` / `api_call` / `agent_evaluate` / `user_confirm` / `file_read` / `file_write` / `wait_for_async`

**DB Tables:** `skills`, `skill_steps`

---

## Evolution Tools — 进化日志

> Source: `tools/evolution.py`

```python
async def evolution_logs(source_type: str | None = None, risk_level: str | None = None, target_table: str | None = None, limit: int = 50) -> list[dict[str, Any]]
async def evolution_rollback(log_id: str) -> dict[str, Any]  # admin only
async def evolution_stats() -> dict[str, Any]
```

**DB Tables:** `evolution_logs` | **Service:** `gatekeeper_service`

---

## Global Rules — 全局规则

> Source: `tools/global_rules.py`

```python
async def global_rules_list(rule_type: str | None = None, status: str = "active", limit: int = 100) -> list[dict[str, Any]]
async def global_rules_upsert(rule_key: str, rule_type: str, title: str, content: str, severity: str = "warning", status: str = "active", metadata: dict | None = None) -> dict[str, Any]
async def global_rules_delete(rule_key: str) -> dict[str, Any]
async def global_rules_promote(workspace: str, project: str, rule_key: str) -> dict[str, Any]
```

**Rule types:** `creative` / `compliance` / `polish`

**DB Tables:** `global_rules` | **Service:** `rules_service`

---

## Reference Tools — 参考资料

> Source: `tools/reference.py`

```python
async def reference_source_create(workspace: str | None, project: str | None, source_type: str, name: str, source_uri: str | None = None, license: str | None = None, metadata: dict | None = None) -> dict[str, Any]
async def reference_item_add(source_id: str, workspace: str | None, project: str | None, item_type: str, key: str, content: str, title: str | None = None, metadata: dict | None = None) -> dict[str, Any]
async def reference_search(workspace: str | None, project: str | None, query: str, item_type: str | None = None, limit: int = 20) -> list[dict[str, Any]]
```

**DB Tables:** `reference_sources`, `reference_items` | **Service:** `reference_service`

---

## Vector Tools — 向量索引

> Source: `tools/vector.py`

```python
async def vector_index_enqueue(workspace: str, project: str, chunk_ids: list[str], collection: str = "memories", priority: int = 0) -> dict[str, Any]
async def vector_index_queue_stats(workspace: str, project: str | None = None) -> dict[str, Any]
async def vector_index_pending_tasks(workspace: str, project: str | None = None, collection: str | None = None, limit: int = 100) -> list[dict[str, Any]]
async def embedding_embed_text(workspace: str, text: str) -> dict[str, Any]
async def embedding_embed_batch(workspace: str, texts: list[str]) -> dict[str, Any]
async def rerank_rerank(workspace: str, query: str, documents: list[str], top_k: int | None = None) -> dict[str, Any]
async def rag_retrieve_knowledge(workspace: str, project: str, query: str, top_k: int = 10) -> dict[str, Any]
async def rag_retrieve_events(workspace: str, project: str, query: str, limit: int = 20) -> dict[str, Any]
```

**Collections:** `memories` / `knowledge` / `events`
**Service:** `vector_index_service`, `embedding_service`, `rerank_service`

---

## Sync Tools — 文件同步

> Source: `tools/sync.py`

```python
async def sync_manifest_import(workspace: str, project: str, manifest_url: str, auto_process: bool = True) -> dict[str, Any]
async def sync_submit_hashes(workspace: str, project: str, file_data: list[dict]) -> dict[str, Any]
async def sync_resolve_conflicts(workspace: str, project: str, resolution: str, conflict_ids: list[str] | None = None) -> dict[str, Any]
async def sync_pack_export(workspace: str, project: str, include_chapternos: list[int] | None = None) -> dict[str, Any]
async def sync_get_pack(workspace: str, project: str, pack_id: str) -> dict[str, Any]
async def sync_stats(workspace: str, project: str) -> dict[str, Any]
```

**DB Tables:** `sync_files`, `sync_conflicts` | **Service:** `sync_service`

---

## Local Tools — 本地文件管理

> Source: `tools/local.py`

```python
async def local_project_register(workspace: str, project: str, project_id: str, local_root: str) -> dict[str, Any]
async def local_project_list() -> dict[str, Any]
async def local_project_scan(workspace: str, project: str, project_id: str, local_root: str) -> dict[str, Any]
async def local_chapter_list(workspace: str, project: str, status: str | None = None, limit: int = 100, offset: int = 0) -> dict[str, Any]
async def local_chapter_get(workspace: str, project: str, chapter_no: int) -> dict[str, Any]
async def local_chapter_read(workspace: str, project: str, chapter_no: int) -> dict[str, Any]
async def local_chapter_write(workspace: str, project: str, chapter_no: int, content: str) -> dict[str, Any]
async def local_chapter_write_outline(workspace: str, project: str, chapter_no: int, outline: str) -> dict[str, Any]
async def local_review_write(workspace: str, project: str, review_type: str, chapter_no: int, content: str) -> dict[str, Any]
async def local_review_list(workspace: str, project: str, review_type: str | None = None, limit: int = 50) -> dict[str, Any]
async def local_review_read(workspace: str, project: str, review_type: str, chapter_no: int) -> dict[str, Any]
async def local_setting_list(workspace: str, project: str) -> dict[str, Any]
async def local_setting_read(workspace: str, project: str, setting_key: str) -> dict[str, Any]
async def local_stats(workspace: str, project: str) -> dict[str, Any]
```

**DB Tables:** `chapter_index`, `setting_index`, `review_index`

---

## Archive & Compression — 归档与压缩

> Source: `tools/archive.py`

```python
async def archive_volume(workspace: str, project: str, volume_no: int, to_tier: str = "archive") -> dict[str, Any]
async def archive_restore(workspace: str, project: str, volume_no: int, to_tier: str = "active") -> dict[str, Any]
async def archive_volume_status(workspace: str, project: str, tier: str | None = None) -> list[dict[str, Any]]
async def archive_history(workspace: str, project: str, table_name: str | None = None, limit: int = 100) -> list[dict[str, Any]]
async def archive_schedule_create(workspace: str | None = None, project: str | None = None, schedule_name: str = "default", schedule_type: str = "monthly", tier_target: str = "archive", tables_to_archive: list[str] | None = None, retention_days: int = 365, enabled: bool = True) -> dict[str, Any]
async def archive_schedule_list(workspace: str, project: str) -> list[dict[str, Any]]
async def archive_tier_config_get(workspace: str, project: str) -> dict[str, Any]
async def archive_auto_archive(workspace: str, project: str, current_volume_no: int, current_chapter_no: int | None = None) -> dict[str, Any]
async def archive_get_stats(workspace: str, project: str) -> dict[str, Any]

async def context_compression_compress_chapters(workspace: str, project: str, chapter_nos: list[int], target_time: str | None = None, strategy: str | None = None) -> dict[str, Any]
async def context_compression_compress_arc(workspace: str, project: str, from_chapter: int, to_chapter: int, title: str | None = None) -> dict[str, Any]
async def context_compression_compress_volume(workspace: str, project: str, volume_no: int, title: str | None = None) -> dict[str, Any]
async def context_compression_compress_series(workspace: str, project: str, title: str | None = None) -> dict[str, Any]
async def context_compression_get_compressed(workspace: str, project: str, target_type: str | None = None, target_id: str | None = None, level: str | None = None) -> dict[str, Any]
async def context_compression_auto_compress(workspace: str, project: str, chapter_no: int, strategy: str | None = None) -> dict[str, Any]
async def context_compression_list(workspace: str, project: str, target_type: str | None = None, level: str | None = None, limit: int = 100) -> list[dict[str, Any]]
```

**Tiers:** `active` / `warm` / `archive` | **DB Tables:** `archive_jobs`, `compressed_contexts`

---

## Novel Wizard — 小说创建向导

> Source: `tools/novel_wizard.py` (~1954 lines)

```python
async def novel_wizard_start() -> dict[str, Any]
async def novel_wizard_submit(wizard_id: str, answers: dict) -> dict[str, Any]
async def novel_wizard_status(wizard_id: str) -> dict[str, Any]
```

**Purpose:** 交互式小说创建。`start` 返回问题列表（含 workspace 选择），`submit` 提交答案后自动创建 workspace/project/volume，生成 canon 文档和角色设定。

**Default questions:** title, genre, target_audience, premise, world_setting, protagonist, power_system, tone_style, estimated_length

---

## Novel Gen Tools — 多 Pass 生成引擎

> Source: `tools/novel_gen.py` (~1582 lines)

### arc — 角色弧光

```python
async def arc_record_emotion(workspace, project, project_id, character_name, chapter_no, emotion, intensity, cause?) -> dict
async def arc_record_relationship(workspace, project, project_id, character_name, chapter_no, target_name, old_relation, new_relation, cause?) -> dict
async def arc_record_power(workspace, project, project_id, character_name, chapter_no, old_level, new_level, method?, note?) -> dict
async def arc_record_personality(workspace, project, project_id, character_name, chapter_no, trait, old_value, new_value, reason?) -> dict
async def arc_record_point(workspace, project, project_id, character_name, chapter_no, point_type, description, intensity?) -> dict
async def arc_get_character(workspace, project, character_name) -> dict
async def arc_get_latest_state(workspace, project, character_name) -> dict
async def arc_get_emotion_timeline(workspace, project, character_name, limit?) -> list
async def arc_get_power_progression(workspace, project, character_name) -> list
async def arc_get_relationship_evolution(workspace, project, character_name, target_name) -> list
async def arc_get_summary_for_context(workspace, project, character_name, current_chapter_no?) -> dict
```

**Point types:** `turning_point` / `achievement` / `loss` / `revelation` / `betrayal` / `redemption`
**DB Tables:** `character_arcs` | **Service:** `character_arc_service`

### causality — 因果链

```python
async def causality_record(workspace, project, project_id, cause_chapter_no, effect_chapter_no, description, cause_type?, effect_type?, strength?, tags?) -> dict
async def causality_record_chain(workspace, project, project_id, chain_id, chapters, summaries, chain_type?, tags?) -> dict
async def causality_get_forward(workspace, project, chapter_no, limit?) -> list
async def causality_get_backward(workspace, project, chapter_no, limit?) -> list
async def causality_get_in_range(workspace, project, from_chapter, to_chapter, limit?) -> list
async def causality_find_unresolved(workspace, project, limit?) -> list
async def causality_find_dangling(workspace, project, limit?) -> list
async def causality_get_summary(workspace, project, chapter_no) -> dict
```

**Cause/effect types:** `direct` / `indirect` / `butterfly` / `chain`
**DB Tables:** `causality_chains` | **Service:** `causality_service`

### novelty — 新颖度检测

```python
async def novelty_check_scene(workspace, project, content, context?) -> dict
async def novelty_check_description(workspace, project, content, context?) -> dict
async def novelty_check_dialogue(workspace, project, content, context?) -> dict
async def novelty_check_plot_beats(workspace, project, content, context?) -> dict
async def novelty_full_check(workspace, project, content, chapter_no?) -> dict
```

**Service:** `novelty_service`

### pacing — 节奏管理

```python
async def pacing_create_blueprint(workspace, project, project_id, blueprint, title?, description?) -> dict
async def pacing_get_blueprint(workspace, project, project_id, blueprint_id?) -> dict
async def pacing_list_blueprints(workspace, project, project_id) -> list
async def pacing_record_emotion(workspace, project, project_id, chapter_no, tension, emotion, emotion_intensity?, pacing_type?) -> dict
async def pacing_get_emotion(workspace, project, chapter_no?, limit?) -> list
async def pacing_get_curve(workspace, project, from_chapter?, to_chapter?) -> list
async def pacing_analyze_rhythm(workspace, project, chapter_no, content) -> dict
async def pacing_check_health(workspace, project, current_chapter_no?) -> dict
async def pacing_compare_blueprint(workspace, project, project_id, blueprint_id, current_chapter_no?) -> dict
async def pacing_predict_engagement(workspace, project, from_chapter?, to_chapter?) -> dict
async def pacing_get_summary(workspace, project, chapter_no) -> dict
```

**DB Tables:** `chapter_emotions`, `pacing_blueprints` | **Service:** `pacing_service`

### style — 风格指纹

```python
async def style_create_profile(workspace, project, project_id, profile_name, base_chapters?, style_params?) -> dict
async def style_get_profile(workspace, project, project_id?, profile_name?) -> dict
async def style_analyze_chapter(workspace, project, project_id?, chapter_no, content, profile_name?) -> dict
async def style_get_chapter(workspace, project, chapter_no) -> dict
async def style_detect_drift(workspace, project, project_id?, chapter_no, content, profile_name?, threshold?) -> dict
async def style_batch_analyze(workspace, project, project_id?, chapter_nos, profile_name?) -> dict
async def style_get_trend(workspace, project, project_id?, from_chapter?, to_chapter?) -> dict
async def style_get_summary(workspace, project, project_id?, profile_name?) -> dict
```

**DB Tables:** `chapter_style_metrics`, `style_profiles` | **Service:** `style_fingerprint_service`

### pipeline — 生成流水线

```python
async def pipeline_create_plan(workspace, project, chapter_no, plan) -> dict
async def pipeline_get_plan(workspace, project, chapter_no) -> dict
async def pipeline_record_pass(workspace, project, chapter_no, pass_type, pass_number, model_key?, input_tokens?, output_tokens?, metadata?) -> dict
async def pipeline_get_passes(workspace, project, chapter_no, pass_type?) -> list
async def pipeline_check_continuity(workspace, project, from_chapter, to_chapter) -> dict
async def pipeline_run_full(workspace, project, chapter_no, plan?, draft_content?, polish_content?, review_notes?) -> dict
async def pipeline_status(workspace, project, chapter_no) -> dict
async def pipeline_multi_review(workspace, project, chapter_no, models, content, dimensions?) -> dict
async def pipeline_generate(workspace, project, chapter_no, task_type, content?, model_key?, user_prompt?, system_prompt?, temperature?, max_tokens?) -> dict
```

**DB Tables:** `generation_passes`, `generation_plans` | **Service:** `multipass_service`