import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Migration script: update category_id based on old slug → new slug mapping
migration_sql = """
-- Get new category IDs
WITH new_cats AS (
    SELECT slug, id FROM ref_categories WHERE parent_id IS NOT NULL
),
old_cats AS (
    SELECT slug, id FROM ref_categories WHERE parent_id IS NULL OR slug LIKE 'kb_%'
)
-- Update items based on old category slug
UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'cultivation_level'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug = 'kb_skill');

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'char_template'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug IN ('kb_character', 'kb_male_protagonist', 'kb_female_protagonist', 'kb_antagonist', 'kb_genre', 'kb_era_setting'));

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'scene_template'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug IN ('kb_scene', 'kb_scene_template'));

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'plot_trope'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug IN ('kb_plot_templates', 'kb_plot_archetype', 'kb_core_conflict', 'kb_ending_types'));

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'structure_template'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug IN ('kb_narrative', 'kb_pacing', 'kb_story_complexity', 'kb_title_structure'));

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'style_guide'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug IN ('kb_style', 'kb_language', 'kb_world_tone', 'kb_emotion', 'kb_platform_style', 'kb_theme', 'kb_reader_groups'));

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'geography'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug = 'kb_setting_background');

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'naming_rules'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug = 'kb_naming');

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'special_item'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug = 'kb_cheat_types');

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'char_personality'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug = 'kb_identity');

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'historical_event'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug IN ('historical_figure', 'historical_event', 'historical_process', 'historical_geo'));

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'social_system'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug IN ('politics', 'economy', 'society'));

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'culture_custom'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug = 'culture');

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'terminology'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug = 'technology');

-- Genre templates → plot_trope
UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'plot_trope'
) WHERE category_id IN (SELECT id FROM ref_categories WHERE slug IN ('xianxia', 'xuanhuan', 'scifi', 'horror', 'post_apocalyptic', 'game', 'urban'));

-- Items still in old top-level categories
UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'writing_ref'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'writing');

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'history_culture'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'history');

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'social_system'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'era');

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'plot_trope'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'genre');

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'terminology'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'professional');
"""

stdin, stdout, stderr = ssh.exec_command(
    "docker exec -i novel-postgres psql -U novel_os -d novel_os",
    timeout=30
)
stdin.write(migration_sql)
stdin.channel.shutdown_write()
out = stdout.read().decode()
err = stderr.read().decode()
print("=== Migration result ===")
print(out)
if err and "NOTICE" not in err:
    print("=== Error ===")
    print(err)

# Verify
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT rc.slug, COUNT(uk.id) as items FROM ref_categories rc LEFT JOIN universal_knowledge uk ON uk.category_id = rc.id WHERE rc.parent_id IS NOT NULL GROUP BY rc.id, rc.slug ORDER BY items DESC;\"",
    timeout=15
)
print("=== New category distribution ===")
print(stdout.read().decode())

ssh.close()
