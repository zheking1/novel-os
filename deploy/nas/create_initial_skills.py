import paramiko
import json
import uuid
import textwrap

SSH_HOST = '${NAS_HOST}'
SSH_USER = 'root'
SSH_PASS = '${NAS_SSH_PASSWORD}'

SKILLS = [
    {
        "name": "novel-init",
        "description": "Initialize a new novel project with local directory, volumes, and basic settings",
        "tags": ["initialize project", "new novel", "start writing", "初始化项目", "新建小说"],
        "content": textwrap.dedent("""\
        # Novel Project Initialization

        ## Trigger
        User says "initialize project", "new novel", "start writing"

        ## Steps

        1. Register Project
           - Tool: local.project.register
           - Params: project_id, local_root
           - Description: Register the local directory as a novel project

        2. Scan Directory
           - Tool: local.project.scan
           - Params: project_id, local_root
           - Description: Scan existing files and build index

        3. Create Volume
           - Tool: volume.upsert
           - Params: volume_no, title, outline
           - Description: Create the first volume with outline

        4. Set Writing Rules
           - Tool: rules.upsert
           - Params: rule_type, content
           - Description: Define writing constraints and style rules

        ## Notes
        - Ensure project_id is unique
        - Use UUID format for project_id if possible
        - Scan will auto-detect existing chapters"""),
        "steps": [
            {"step_order": 1, "step_name": "Register Project", "tool_name": "local.project.register", "description": "Register local directory as novel project"},
            {"step_order": 2, "step_name": "Scan Directory", "tool_name": "local.project.scan", "description": "Scan and index existing files"},
            {"step_order": 3, "step_name": "Create Volume", "tool_name": "volume.upsert", "description": "Create first volume"},
            {"step_order": 4, "step_name": "Set Rules", "tool_name": "rules.upsert", "description": "Define writing rules"},
        ],
    },
    {
        "name": "novel-write",
        "description": "Generate a single chapter with full workflow (context -> generate -> record -> review)",
        "tags": ["write chapter", "generate chapter", "写第X章", "生成章节", "写小说"],
        "content": textwrap.dedent("""\
        # Novel Chapter Generation

        ## Trigger
        User says "write chapter X", "generate chapter X"

        ## Workflow

        ### Phase 1: Context Preparation
        1. Call workflow.prepare_chapter_context with chapter_no, purpose="generation"
        2. Call workflow.preflight_generation to validate context pack
        3. Review context pack for completeness

        ### Phase 2: Generation (Agent executes)
        1. Use context pack to generate chapter content
        2. Follow style rules and character profiles
        3. Maintain consistency with previous chapters

        ### Phase 3: Record Results
        1. Call pipeline.record_pass for each pass:
           - Pass 1 (Planning): chapter outline
           - Pass 2 (Drafting): initial draft
           - Pass 3 (Polishing): refined text
           - Pass 4 (Verification): continuity check

        ### Phase 4: Persistence
        1. Call local.chapter.write to save final version
        2. Call local.chapter.write_outline to save outline

        ### Phase 5: Post-Generation Tracking
        1. Call arc.record_emotion for character emotions
        2. Call arc.record_relationship for relationship changes
        3. Call causality.record for cause-effect chains
        4. Call pacing.record_emotion for pacing data

        ## Notes
        - Always check token budget before generation
        - Use segment context for long chapters
        - Record ALL tracking data for future consistency"""),
        "steps": [
            {"step_order": 1, "step_name": "Prepare Context", "tool_name": "workflow.prepare_chapter_context", "description": "Assemble context pack for generation"},
            {"step_order": 2, "step_name": "Preflight Check", "tool_name": "workflow.preflight_generation", "description": "Validate context pack completeness"},
            {"step_order": 3, "step_name": "Record Planning Pass", "tool_name": "pipeline.record_pass", "description": "Record chapter outline"},
            {"step_order": 4, "step_name": "Write Chapter", "tool_name": "local.chapter.write", "description": "Save final chapter to file"},
            {"step_order": 5, "step_name": "Record Emotions", "tool_name": "arc.record_emotion", "description": "Record character emotions"},
            {"step_order": 6, "step_name": "Record Causality", "tool_name": "causality.record", "description": "Record cause-effect chains"},
        ],
    },
    {
        "name": "novel-batch",
        "description": "Generate multiple chapters in sequence with breakpoint resume",
        "tags": ["batch generate", "write multiple chapters", "批量生成", "连续写", "批量写"],
        "content": textwrap.dedent("""\
        # Batch Chapter Generation

        ## Trigger
        User says "batch generate", "write 10 chapters", "批量生成"

        ## Workflow

        ### Pre-Flight
        1. Determine chapter range (start_chapter to end_chapter)
        2. Check existing chapters to avoid duplicates
        3. Set breakpoint tracking

        ### Per-Chapter Loop
        For each chapter in range:
        1. Call workflow.prepare_chapter_context
        2. Generate content (agent)
        3. Call pipeline.record_pass for all passes
        4. Call local.chapter.write to save
        5. Call tracking tools (arc, causality, pacing)
        6. Save breakpoint state

        ### Breakpoint Resume
        - If interrupted, read last saved breakpoint
        - Resume from next chapter
        - Skip already completed chapters

        ### Completion Report
        - List all generated chapters
        - Summary of word counts
        - Any issues encountered

        ## Notes
        - Each chapter gets full workflow (no shortcuts)
        - Breakpoint auto-saves every chapter
        - Can resume from any breakpoint"""),
        "steps": [
            {"step_order": 1, "step_name": "Check Range", "tool_name": "local.chapter.read", "description": "Verify chapter range and existing files"},
            {"step_order": 2, "step_name": "Generate Chapter", "tool_name": "workflow.prepare_chapter_context", "description": "Loop through chapters with full workflow"},
            {"step_order": 3, "step_name": "Save Breakpoint", "tool_name": None, "description": "Save progress after each chapter"},
        ],
    },
    {
        "name": "novel-review",
        "description": "Review chapter quality with 13-dimension structured review",
        "tags": ["review chapter", "check quality", "审查章节", "检查质量", "审稿"],
        "content": textwrap.dedent("""\
        # Chapter Review

        ## Trigger
        User says "review chapter X", "check quality"

        ## Review Dimensions
        1. Setting Consistency
        2. Character OOC Check
        3. Plot Continuity
        4. Pacing Rhythm
        5. Dialogue Quality
        6. Description Richness
        7. Emotional Impact
        8. Suspense Building
        9. Foreshadowing Payoff
        10. World-building Logic
        11. Readability Score
        12. Anti-AI Detection
        13. Genre Convention Compliance

        ## Workflow

        ### Phase 1: Preparation
        1. Call local.chapter.read to get chapter content
        2. Load recent summaries for context

        ### Phase 2: Review
        1. Call review.start_job with chapter data
        2. Wait for review completion
        3. Review all dimension results

        ### Phase 3: Learning
        1. Call workflow.learn_from_review to extract insights
        2. Update writing rules if needed
        3. Record lessons learned

        ### Phase 4: Report
        1. Generate review summary
        2. Highlight critical issues
        3. Suggest improvements

        ## Notes
        - Review quality depends on context completeness
        - Critical issues block publication
        - Warnings are advisory"""),
        "steps": [
            {"step_order": 1, "step_name": "Read Chapter", "tool_name": "local.chapter.read", "description": "Load chapter content"},
            {"step_order": 2, "step_name": "Start Review", "tool_name": "review.start_job", "description": "Initiate 13-dimension review"},
            {"step_order": 3, "step_name": "Learn from Review", "tool_name": "workflow.learn_from_review", "description": "Extract insights and update rules"},
        ],
    },
    {
        "name": "novel-kb",
        "description": "Manage knowledge base - add characters, factions, locations, and relationships",
        "tags": ["add character", "import knowledge", "add entity", "添加角色", "导入知识", "添加势力"],
        "content": textwrap.dedent("""\
        # Knowledge Base Management

        ## Trigger
        User says "add character", "import knowledge", "add entity"

        ## Entity Types
        - character: Individual characters with profiles
        - faction: Organizations, groups, sects
        - location: Places, cities, realms
        - item: Objects, weapons, treasures
        - concept: Systems, rules, techniques

        ## Workflow

        ### Add Character
        1. Call kb.entity.create with entity_type="character"
        2. Include: name, aliases, profile, importance
        3. Add relationships with kb.relation.create

        ### Add Faction
        1. Call kb.entity.create with entity_type="faction"
        2. Include: name, description, power_level
        3. Add member relationships

        ### Add Location
        1. Call kb.entity.create with entity_type="location"
        2. Include: name, description, geography
        3. Add associated entities

        ### Add Knowledge
        1. Call kb.uk.create for general knowledge
        2. Include: topic, content, category
        3. Add tags for retrieval

        ## Notes
        - Use consistent naming conventions
        - Always add relationships for context
        - Update world state after major changes"""),
        "steps": [
            {"step_order": 1, "step_name": "Create Entity", "tool_name": "kb.entity.create", "description": "Create new entity"},
            {"step_order": 2, "step_name": "Add Relations", "tool_name": "kb.relation.create", "description": "Add relationships"},
            {"step_order": 3, "step_name": "Update World State", "tool_name": "kb.world.update", "description": "Update world state snapshot"},
        ],
    },
    {
        "name": "novel-setting",
        "description": "Set up world rules, canon documents, and writing constraints",
        "tags": ["set world rules", "configure world", "设置世界观", "配置规则", "编写设定"],
        "content": textwrap.dedent("""\
        # World Setting Configuration

        ## Trigger
        User says "set world rules", "configure world"

        ## Setting Components

        ### 1. Writing Rules
        - Call rules.upsert with rule_type
        - Categories: style, pacing, dialogue, description

        ### 2. Canon Documents
        - Call canon.doc.upsert for world bible
        - Types: worldbuilding, magic_system, power_system, history

        ### 3. Genre Conventions
        - Configure genre-specific rules
        - Set platform requirements

        ## Workflow

        ### Set Core Rules
        1. Define narrative style (POV, tense, tone)
        2. Set pacing constraints (words per chapter, scene length)
        3. Configure dialogue rules

        ### Create World Bible
        1. Create main setting document
        2. Add magic/power system rules
        3. Add history and lore
        4. Add faction descriptions

        ### Configure Compliance
        1. Set content restrictions
        2. Configure platform rules
        3. Add review criteria

        ## Notes
        - Rules are enforced during review
        - Canon documents provide context
        - Keep rules concise and clear"""),
        "steps": [
            {"step_order": 1, "step_name": "Set Writing Rules", "tool_name": "rules.upsert", "description": "Define writing constraints"},
            {"step_order": 2, "step_name": "Create Canon Doc", "tool_name": "canon.doc.upsert", "description": "Create world bible document"},
            {"step_order": 3, "step_name": "List Rules", "tool_name": "canon.rule.list", "description": "Verify rule configuration"},
        ],
    },
    {
        "name": "novel-style",
        "description": "Configure and analyze writing style profile",
        "tags": ["set style", "configure writing style", "设置文风", "调整风格", "文风配置"],
        "content": textwrap.dedent("""\
        # Writing Style Configuration

        ## Trigger
        User says "set style", "configure writing style"

        ## Style Components

        ### 1. Profile Creation
        - POV (1st/3rd limited/3rd omniscient)
        - Tense (past/present)
        - Tone (light/dark/neutral)
        - Target metrics (sentence length, vocabulary)

        ### 2. Analysis
        - Call style.analyze on existing chapters
        - Get style fingerprint
        - Compare with target profile

        ### 3. Drift Detection
        - Call style.detect_drift during writing
        - Alert on style deviation
        - Suggest corrections

        ## Workflow

        ### Create Profile
        1. Define POV and tense
        2. Set tone and atmosphere
        3. Configure target metrics

        ### Analyze Existing
        1. Call style.analyze on sample chapters
        2. Compare with target
        3. Identify gaps

        ### Monitor Drift
        1. During generation, check style consistency
        2. Use style.detect_drift for real-time monitoring
        3. Apply corrections as needed

        ## Notes
        - Style profile affects all generation
        - Drift detection requires baseline
        - Update profile as style evolves"""),
        "steps": [
            {"step_order": 1, "step_name": "Create Profile", "tool_name": "style.create_profile", "description": "Define style parameters"},
            {"step_order": 2, "step_name": "Analyze Style", "tool_name": "style.analyze", "description": "Analyze existing chapters"},
            {"step_order": 3, "step_name": "Detect Drift", "tool_name": "style.detect_drift", "description": "Check for style deviation"},
        ],
    },
    {
        "name": "novel-foreshadow",
        "description": "Plant and manage foreshadowing elements",
        "tags": ["plant foreshadowing", "add foreshadowing", "埋伏笔", "设置伏笔", "伏笔管理"],
        "content": textwrap.dedent("""\
        # Foreshadowing Management

        ## Trigger
        User says "plant foreshadowing", "add foreshadowing"

        ## Foreshadowing Types
        - hint: Subtle suggestion
        - seed: Direct setup for future payoff
        - red_herring: Misleading direction
        - callback: Reference to past event

        ## Workflow

        ### Plant Foreshadowing
        1. Call plot.upsert_foreshadowing
        2. Define type and description
        3. Set target chapter for payoff
        4. Link to relevant entities

        ### Track Foreshadowing
        1. Call plot.list_foreshadowing to see all active
        2. Check for overdue items
        3. Monitor debt tracker

        ### Payoff Foreshadowing
        1. When writing payoff chapter
        2. Call foreshadowing.payoff
        3. Link to original seed
        4. Update status

        ## Notes
        - Active foreshadowing creates reader engagement
        - Overdue items need attention
        - Debt tracker blocks generation if too many active"""),
        "steps": [
            {"step_order": 1, "step_name": "Plant Foreshadowing", "tool_name": "plot.upsert_foreshadowing", "description": "Create new foreshadowing"},
            {"step_order": 2, "step_name": "List Active", "tool_name": "plot.list_foreshadowing", "description": "Check active foreshadowing"},
            {"step_order": 3, "step_name": "Payoff", "tool_name": "foreshadowing.payoff", "description": "Resolve foreshadowing"},
        ],
    },
    {
        "name": "novel-arc",
        "description": "Track character arcs - emotions, relationships, power progression",
        "tags": ["record character change", "track arc", "记录角色变化", "角色弧光", "追踪角色"],
        "content": textwrap.dedent("""\
        # Character Arc Management

        ## Trigger
        User says "record character change", "track arc"

        ## Arc Components

        ### 1. Emotions
        - Record emotional state per chapter
        - Track emotional progression
        - Use for consistency checks

        ### 2. Relationships
        - Track relationship changes
        - Map character connections
        - Detect conflicts

        ### 3. Power Progression
        - Track power level changes
        - Record new abilities
        - Monitor growth curve

        ### 4. Personality
        - Track personality shifts
        - Detect OOC (Out of Character)
        - Maintain consistency

        ## Workflow

        ### Record Changes
        1. After each chapter, call arc.record_* tools
        2. Link to chapter number
        3. Add context and reasoning

        ### Get Context
        1. Before generation, call arc.get_summary_for_context
        2. Load character states
        3. Check for conflicts

        ### Monitor Progression
        1. Call arc.get_emotion_timeline
        2. Call arc.get_power_progression
        3. Review relationship evolution

        ## Notes
        - Record ALL significant changes
        - Use for consistency during review
        - Timeline helps pacing decisions"""),
        "steps": [
            {"step_order": 1, "step_name": "Record Emotion", "tool_name": "arc.record_emotion", "description": "Record character emotional state"},
            {"step_order": 2, "step_name": "Record Relationship", "tool_name": "arc.record_relationship", "description": "Track relationship changes"},
            {"step_order": 3, "step_name": "Record Power", "tool_name": "arc.record_power", "description": "Track power progression"},
            {"step_order": 4, "step_name": "Get Summary", "tool_name": "arc.get_summary_for_context", "description": "Get character state for context"},
        ],
    },
    {
        "name": "novel-pacing",
        "description": "Manage pacing rhythm - tension curves, breathing room, climax timing",
        "tags": ["set pacing", "adjust rhythm", "设置节奏", "调整节奏", "节奏控制"],
        "content": textwrap.dedent("""\
        # Pacing Control

        ## Trigger
        User says "set pacing", "adjust rhythm"

        ## Pacing Components

        ### 1. Blueprint
        - Define tension curve for volume
        - Set climax points
        - Plan breathing room

        ### 2. Emotion Tracking
        - Record emotion per scene
        - Track tension level
        - Monitor reader engagement

        ### 3. Health Check
        - Detect pacing issues
        - Alert on flat sections
        - Suggest improvements

        ## Workflow

        ### Create Blueprint
        1. Call pacing.create_blueprint
        2. Define tension curve (0-10 scale)
        3. Set climax timing
        4. Plan scene transitions

        ### Record Progress
        1. After each scene, call pacing.record_emotion
        2. Track actual vs planned curve
        3. Adjust if needed

        ### Monitor Health
        1. Call pacing.check_health regularly
        2. Get curve visualization
        3. Compare with blueprint

        ## Notes
        - Good pacing maintains reader interest
        - Breathing room prevents fatigue
        - Climax timing affects satisfaction"""),
        "steps": [
            {"step_order": 1, "step_name": "Create Blueprint", "tool_name": "pacing.create_blueprint", "description": "Define tension curve"},
            {"step_order": 2, "step_name": "Record Emotion", "tool_name": "pacing.record_emotion", "description": "Record scene emotion"},
            {"step_order": 3, "step_name": "Check Health", "tool_name": "pacing.check_health", "description": "Verify pacing balance"},
            {"step_order": 4, "step_name": "Get Curve", "tool_name": "pacing.get_curve", "description": "Visualize pacing curve"},
        ],
    },
]

def create_skills():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS)
    
    # Get default user_id
    stdin, stdout, stderr = ssh.exec_command(
        "docker exec novel-postgres psql -U novel_os -d novel_os -t -c \"SELECT id::text FROM users LIMIT 1\""
    )
    user_id = stdout.read().decode('utf-8', errors='replace').strip()
    print(f"Using user_id: {user_id}")
    
    if not user_id:
        print("ERROR: No user found in database")
        ssh.close()
        return
    
    for skill in SKILLS:
        skill_id = str(uuid.uuid4())
        
        # Escape single quotes in content
        content_escaped = skill["content"].replace("'", "''")
        desc_escaped = skill["description"].replace("'", "''")
        tags_escaped = [t.replace("'", "''") for t in skill["tags"]]
        tags_array = "ARRAY[" + ",".join(["'" + t + "'" for t in tags_escaped]) + "]"
        
        # Build the SQL - check if exists first, update or insert
        check_sql = f"SELECT id::text FROM skills WHERE name = '{skill['name']}' AND user_id = '{user_id}'"
        
        # First check if exists
        tmp_check = f"/tmp/skill_check_{skill['name']}.sql"
        sftp = ssh.open_sftp()
        with sftp.open(tmp_check, 'w') as f:
            f.write(check_sql)
        sftp.close()
        
        stdin, stdout, stderr = ssh.exec_command(
            f"docker cp {tmp_check} novel-postgres:/tmp/check.sql && docker exec novel-postgres psql -U novel_os -d novel_os -f /tmp/check.sql -t && docker exec novel-postgres rm -f /tmp/check.sql"
        )
        existing = stdout.read().decode('utf-8', errors='replace').strip()
        ssh.exec_command(f"rm -f {tmp_check}")
        
        # Parse existing ID
        existing_id = None
        for line in existing.split('\n'):
            line = line.strip()
            if line and len(line) == 36 and '-' in line:
                existing_id = line
                break
        
        if existing_id:
            # Update existing
            sql = f"""UPDATE skills SET
    description = '{desc_escaped}',
    content = '{content_escaped}',
    instruction = '{content_escaped}',
    tags = {tags_array},
    updated_at = now()
WHERE id = '{existing_id}'
RETURNING id::text;"""
            skill_id = existing_id
            print(f"Updating existing skill: {skill['name']} (id: {existing_id})")
        else:
            # Insert new
            sql = f"""INSERT INTO skills (id, name, description, content, instruction, tags, scope, is_active, user_id)
VALUES ('{skill_id}', '{skill["name"]}', '{desc_escaped}', '{content_escaped}', '{content_escaped}', {tags_array}, 'public', true, '{user_id}')
RETURNING id::text;"""
        
        # Write SQL to temp file on NAS to avoid shell escaping issues
        sftp = ssh.open_sftp()
        tmp_sql = f"/tmp/skill_{skill['name']}.sql"
        with sftp.open(tmp_sql, 'w') as f:
            f.write(sql)
        sftp.close()
        
        # Execute via file
        stdin, stdout, stderr = ssh.exec_command(
            f"docker cp {tmp_sql} novel-postgres:/tmp/skill.sql && docker exec novel-postgres psql -U novel_os -d novel_os -f /tmp/skill.sql -t"
        )
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        
        # Clean up temp file
        ssh.exec_command(f"rm -f {tmp_sql} && docker exec novel-postgres rm -f /tmp/skill.sql")
        
        # Parse returned ID (may have newlines and whitespace)
        lines = [l.strip() for l in out.split('\n') if l.strip() and not l.strip().startswith('(') and 'INSERT' not in l and 'rows' not in l]
        returned_id = lines[0] if lines else None
        
        if returned_id and len(returned_id) == 36:  # UUID length
            print(f"Created skill: {skill['name']} (id: {returned_id})")
            
            # Delete existing steps
            ssh.exec_command(
                f"docker exec novel-postgres psql -U novel_os -d novel_os -c \"DELETE FROM skill_steps WHERE skill_id = '{returned_id}'\""
            )
            
            # Create steps via file too
            for step in skill.get("steps", []):
                params_json = json.dumps(step.get("parameters", {})).replace("'", "''")
                tool_name = step.get("tool_name") or ""
                desc = step.get("description", "").replace("'", "''")
                
                step_sql = f"""INSERT INTO skill_steps (skill_id, step_order, step_name, tool_name, description, parameters, optional)
VALUES ('{returned_id}', {step['step_order']}, '{step["step_name"]}', '{tool_name}', '{desc}', '{params_json}'::jsonb, {step.get("optional", False)});"""
                
                sftp = ssh.open_sftp()
                step_file = f"/tmp/step_{skill['name']}_{step['step_order']}.sql"
                with sftp.open(step_file, 'w') as f:
                    f.write(step_sql)
                sftp.close()
                
                ssh.exec_command(
                    f"docker cp {step_file} novel-postgres:/tmp/step.sql && docker exec novel-postgres psql -U novel_os -d novel_os -f /tmp/step.sql && docker exec novel-postgres rm -f /tmp/step.sql"
                )
                ssh.exec_command(f"rm -f {step_file}")
            
            print(f"  Added {len(skill.get('steps', []))} steps")
        else:
            print(f"Failed to create skill: {skill['name']}")
            if out:
                print(f"  Output: {out[:200]}")
            if err:
                print(f"  Error: {err[:200]}")
    
    ssh.close()
    print("\nDone!")

if __name__ == "__main__":
    create_skills()
