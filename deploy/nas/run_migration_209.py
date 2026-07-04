import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}', timeout=10)

# Run migration 209
with open(r'D:\Project\novels codex\deploy\nas\postgres\migrations\209_fix_child_category_parent_id.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

stdin, stdout, stderr = ssh.exec_command(
    "docker exec -i novel-postgres psql -U novel_os -d novel_os",
    timeout=30
)
stdin.write(sql)
stdin.channel.shutdown_write()
out = stdout.read().decode()
err = stderr.read().decode()
print("=== Migration 209 ===")
print(out)
if err and "NOTICE" not in err:
    print("=== Error ===")
    print(err)

# Verify all child categories have correct parent_id
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT c.slug, c.name, c.parent_id::text, p.slug as parent_slug FROM ref_categories c LEFT JOIN ref_categories p ON c.parent_id = p.id WHERE c.parent_id IS NOT NULL ORDER BY p.slug, c.sort_order;\"",
    timeout=15
)
print("=== All child categories with parent ===")
print(stdout.read().decode())

# Check for any categories with NULL parent_id that should have one
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT slug, name, parent_id::text FROM ref_categories WHERE slug IN ('char_template', 'char_personality', 'naming_rules', 'plot_trope', 'structure_template', 'geography', 'scene_template', 'style_guide', 'cultivation_level', 'special_item', 'weapon_template', 'armor_template', 'consumable', 'material_resource', 'intelligent_race', 'beast_monster', 'plant_ecology', 'ecology_rules', 'faction_org', 'social_system', 'culture_custom', 'skill_technique', 'array_mechanism', 'rule_restriction', 'historical_event', 'legend_myth', 'biography', 'civilization_evolution', 'foreshadowing_tech', 'pacing_ref', 'forbidden_words', 'poetry_couplet', 'terminology', 'economy_currency') ORDER BY slug;\"",
    timeout=15
)
print("=== Child category parent check ===")
print(stdout.read().decode())

ssh.close()
