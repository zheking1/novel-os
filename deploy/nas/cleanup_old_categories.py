import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Delete empty old categories (no items, no children with items)
delete_sql = """
-- Delete old child categories that have no items and no children
DELETE FROM ref_categories WHERE slug IN (
    'kb_writing_technique', 'kb_ending_types', 'kb_core_conflict',
    'kb_scene_template', 'kb_platform_style', 'kb_pacing',
    'kb_reader_groups', 'historical_process', 'kb_genre',
    'kb_cheat_types', 'culture', 'historical_figure',
    'kb_narrative', 'kb_plot_templates', 'kb_language',
    'historical_geo', 'economy', 'kb_title_structure',
    'kb_character', 'kb_plot_archetype', 'kb_era_setting',
    'politics', 'kb_male_protagonist', 'kb_world_tone',
    'historical_event', 'kb_setting_background', 'kb_theme',
    'kb_story_complexity', 'xuanhuan', 'game',
    'kb_skill', 'kb_emotion', 'kb_antagonist',
    'kb_scene', 'kb_female_protagonist', 'technology',
    'kb_style', 'kb_identity', 'kb_naming',
    'society', 'urban', 'xianxia', 'scifi', 'horror',
    'post_apocalyptic'
) AND NOT EXISTS (SELECT 1 FROM universal_knowledge WHERE category_id = ref_categories.id);

-- Delete old top-level categories that have no items
DELETE FROM ref_categories WHERE slug IN ('writing', 'history', 'era', 'genre', 'professional')
AND NOT EXISTS (SELECT 1 FROM universal_knowledge WHERE category_id = ref_categories.id);
"""

stdin, stdout, stderr = ssh.exec_command(
    "docker exec -i novel-postgres psql -U novel_os -d novel_os",
    timeout=15
)
stdin.write(delete_sql)
stdin.channel.shutdown_write()
out = stdout.read().decode()
err = stderr.read().decode()
print("=== Delete result ===")
print(out)
if err and "NOTICE" not in err:
    print("=== Error ===")
    print(err)

# Verify final structure
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT c.slug, c.name, COUNT(uk.id) as items FROM ref_categories c LEFT JOIN universal_knowledge uk ON uk.category_id = c.id WHERE c.parent_id IS NULL GROUP BY c.id, c.slug, c.name ORDER BY c.sort_order;\"",
    timeout=15
)
print("=== Final top-level categories ===")
print(stdout.read().decode())

ssh.close()
