import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

sql = """
-- GLM-4-9B (Primary)
INSERT INTO model_profiles (project_id, profile_key, display_name, provider, model_name, task_types, tier, default_params, cost_config, is_default, status, user_id) 
VALUES ((SELECT id FROM projects WHERE slug = 'default'), 'completion-glm4-9b', 'GLM-4-9B (Primary)', 'siliconflow', 'THUDM/GLM-4-9B-0414', ARRAY['completion','draft','outline','revision'], 'standard', '{"api_url":"https://api.siliconflow.cn","api_key":"sk-hpadhczqmozktlndxvrgweqsyjcvljacbdwrehwijrgzifyb","temperature":0.7,"max_tokens":4096}'::jsonb, '{"input_per_1k":0,"output_per_1k":0}'::jsonb, true, 'active', 'admin')
ON CONFLICT (project_id, profile_key) DO UPDATE SET display_name = EXCLUDED.display_name, model_name = EXCLUDED.model_name, task_types = EXCLUDED.task_types, default_params = EXCLUDED.default_params, is_default = EXCLUDED.is_default, status = 'active', updated_at = NOW();

-- DeepSeek-R1-Qwen3-8B (Reasoning)
INSERT INTO model_profiles (project_id, profile_key, display_name, provider, model_name, task_types, tier, default_params, cost_config, is_default, status, user_id) 
VALUES ((SELECT id FROM projects WHERE slug = 'default'), 'completion-deepseek-r1-8b', 'DeepSeek-R1-Qwen3-8B (Reasoning)', 'siliconflow', 'deepseek-ai/DeepSeek-R1-0528-Qwen3-8B', ARRAY['completion','draft','outline','reasoning'], 'standard', '{"api_url":"https://api.siliconflow.cn","api_key":"sk-hpadhczqmozktlndxvrgweqsyjcvljacbdwrehwijrgzifyb","temperature":0.7,"max_tokens":4096}'::jsonb, '{"input_per_1k":0,"output_per_1k":0}'::jsonb, false, 'active', 'admin')
ON CONFLICT (project_id, profile_key) DO UPDATE SET display_name = EXCLUDED.display_name, model_name = EXCLUDED.model_name, task_types = EXCLUDED.task_types, default_params = EXCLUDED.default_params, is_default = EXCLUDED.is_default, status = 'active', updated_at = NOW();

-- Qwen2.5-7B-Instruct (Balanced)
INSERT INTO model_profiles (project_id, profile_key, display_name, provider, model_name, task_types, tier, default_params, cost_config, is_default, status, user_id) 
VALUES ((SELECT id FROM projects WHERE slug = 'default'), 'completion-qwen2.5-7b', 'Qwen2.5-7B-Instruct (Balanced)', 'siliconflow', 'Qwen/Qwen2.5-7B-Instruct', ARRAY['completion','draft','revision'], 'standard', '{"api_url":"https://api.siliconflow.cn","api_key":"sk-hpadhczqmozktlndxvrgweqsyjcvljacbdwrehwijrgzifyb","temperature":0.7,"max_tokens":4096}'::jsonb, '{"input_per_1k":0,"output_per_1k":0}'::jsonb, false, 'active', 'admin')
ON CONFLICT (project_id, profile_key) DO UPDATE SET display_name = EXCLUDED.display_name, model_name = EXCLUDED.model_name, task_types = EXCLUDED.task_types, default_params = EXCLUDED.default_params, is_default = EXCLUDED.is_default, status = 'active', updated_at = NOW();

-- Qwen3-8B (Fast)
INSERT INTO model_profiles (project_id, profile_key, display_name, provider, model_name, task_types, tier, default_params, cost_config, is_default, status, user_id) 
VALUES ((SELECT id FROM projects WHERE slug = 'default'), 'completion-qwen3-8b', 'Qwen3-8B (Fast)', 'siliconflow', 'Qwen/Qwen3-8B', ARRAY['completion','draft','outline'], 'standard', '{"api_url":"https://api.siliconflow.cn","api_key":"sk-hpadhczqmozktlndxvrgweqsyjcvljacbdwrehwijrgzifyb","temperature":0.7,"max_tokens":4096}'::jsonb, '{"input_per_1k":0,"output_per_1k":0}'::jsonb, false, 'active', 'admin')
ON CONFLICT (project_id, profile_key) DO UPDATE SET display_name = EXCLUDED.display_name, model_name = EXCLUDED.model_name, task_types = EXCLUDED.task_types, default_params = EXCLUDED.default_params, is_default = EXCLUDED.is_default, status = 'active', updated_at = NOW();

-- GLM-Z1-9B (Reasoning)
INSERT INTO model_profiles (project_id, profile_key, display_name, provider, model_name, task_types, tier, default_params, cost_config, is_default, status, user_id) 
VALUES ((SELECT id FROM projects WHERE slug = 'default'), 'completion-glm-z1-9b', 'GLM-Z1-9B (Reasoning)', 'siliconflow', 'THUDM/GLM-Z1-9B-0414', ARRAY['completion','draft','outline','reasoning'], 'standard', '{"api_url":"https://api.siliconflow.cn","api_key":"sk-hpadhczqmozktlndxvrgweqsyjcvljacbdwrehwijrgzifyb","temperature":0.7,"max_tokens":4096}'::jsonb, '{"input_per_1k":0,"output_per_1k":0}'::jsonb, false, 'active', 'admin')
ON CONFLICT (project_id, profile_key) DO UPDATE SET display_name = EXCLUDED.display_name, model_name = EXCLUDED.model_name, task_types = EXCLUDED.task_types, default_params = EXCLUDED.default_params, is_default = EXCLUDED.is_default, status = 'active', updated_at = NOW();

-- Qwen3.5-4B (Light)
INSERT INTO model_profiles (project_id, profile_key, display_name, provider, model_name, task_types, tier, default_params, cost_config, is_default, status, user_id) 
VALUES ((SELECT id FROM projects WHERE slug = 'default'), 'completion-qwen3.5-4b', 'Qwen3.5-4B (Light)', 'siliconflow', 'Qwen/Qwen3.5-4B', ARRAY['completion','draft'], 'standard', '{"api_url":"https://api.siliconflow.cn","api_key":"sk-hpadhczqmozktlndxvrgweqsyjcvljacbdwrehwijrgzifyb","temperature":0.7,"max_tokens":4096}'::jsonb, '{"input_per_1k":0,"output_per_1k":0}'::jsonb, false, 'active', 'admin')
ON CONFLICT (project_id, profile_key) DO UPDATE SET display_name = EXCLUDED.display_name, model_name = EXCLUDED.model_name, task_types = EXCLUDED.task_types, default_params = EXCLUDED.default_params, is_default = EXCLUDED.is_default, status = 'active', updated_at = NOW();

-- Hunyuan-MT-7B (Translation)
INSERT INTO model_profiles (project_id, profile_key, display_name, provider, model_name, task_types, tier, default_params, cost_config, is_default, status, user_id) 
VALUES ((SELECT id FROM projects WHERE slug = 'default'), 'completion-hunyuan-7b', 'Hunyuan-MT-7B (Translation)', 'siliconflow', 'tencent/Hunyuan-MT-7B', ARRAY['completion','translation'], 'standard', '{"api_url":"https://api.siliconflow.cn","api_key":"sk-hpadhczqmozktlndxvrgweqsyjcvljacbdwrehwijrgzifyb","temperature":0.7,"max_tokens":4096}'::jsonb, '{"input_per_1k":0,"output_per_1k":0}'::jsonb, false, 'active', 'admin')
ON CONFLICT (project_id, profile_key) DO UPDATE SET display_name = EXCLUDED.display_name, model_name = EXCLUDED.model_name, task_types = EXCLUDED.task_types, default_params = EXCLUDED.default_params, is_default = EXCLUDED.is_default, status = 'active', updated_at = NOW();

-- Deactivate old models
UPDATE model_profiles SET status = 'inactive', updated_at = NOW() WHERE profile_key IN ('completion-glm4-flash', 'completion-internlm-7b', 'completion-qwen15-7b') AND provider = 'siliconflow';

-- Show result
SELECT profile_key, display_name, status, is_default FROM model_profiles WHERE status = 'active' ORDER BY is_default DESC, profile_key;
"""

# Write SQL to temp file on NAS
stdin, stdout, stderr = ssh.exec_command('cat > /tmp/add_free_models.sql << \'ENDOFSCRIPT\'\n' + sql + '\nENDOFSCRIPT')
print("SQL written to /tmp/add_free_models.sql")

# Execute
stdin, stdout, stderr = ssh.exec_command('docker cp /tmp/add_free_models.sql novel-postgres:/tmp/ && docker exec novel-postgres psql -U novel_os -d novel_os -f /tmp/add_free_models.sql')
print("=== Result ===")
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
print("Done!")
