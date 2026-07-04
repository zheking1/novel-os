import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Model configurations
models = [
    ("completion-glm4-9b", "GLM-4-9B (Primary)", "THUDM/GLM-4-9B-0414", "{completion,draft,outline,revision}", "true"),
    ("completion-deepseek-r1-8b", "DeepSeek-R1-Qwen3-8B (Reasoning)", "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B", "{completion,draft,outline,reasoning}", "false"),
    ("completion-qwen2.5-7b", "Qwen2.5-7B-Instruct (Balanced)", "Qwen/Qwen2.5-7B-Instruct", "{completion,draft,revision}", "false"),
    ("completion-qwen3-8b", "Qwen3-8B (Fast)", "Qwen/Qwen3-8B", "{completion,draft,outline}", "false"),
    ("completion-glm-z1-9b", "GLM-Z1-9B (Reasoning)", "THUDM/GLM-Z1-9B-0414", "{completion,draft,outline,reasoning}", "false"),
    ("completion-qwen3.5-4b", "Qwen3.5-4B (Light)", "Qwen/Qwen3.5-4B", "{completion,draft}", "false"),
    ("completion-hunyuan-7b", "Hunyuan-MT-7B (Translation)", "tencent/Hunyuan-MT-7B", "{completion,translation}", "false"),
]

default_params = '{"api_url": "https://api.siliconflow.cn", "api_key": "sk-hpadhczqmozktlndxvrgweqsyjcvljacbdwrehwijrgzifyb", "temperature": 0.7, "max_tokens": 4096}'
cost_config = '{"input_per_1k": 0.0, "output_per_1k": 0.0}'

# Build SQL
sql_parts = []
for profile_key, display_name, model_name, task_types, is_default in models:
    sql = f"""INSERT INTO model_profiles (project_id, profile_key, display_name, provider, model_name, task_types, tier, default_params, cost_config, is_default, status, user_id) VALUES ((SELECT id FROM projects WHERE slug = 'default'), '{profile_key}', '{display_name}', 'siliconflow', '{model_name}', '{task_types}'::text[], 'standard', '{default_params}'::jsonb, '{cost_config}'::jsonb, {is_default}, 'active', 'admin') ON CONFLICT (project_id, profile_key) DO UPDATE SET display_name = EXCLUDED.display_name, model_name = EXCLUDED.model_name, task_types = EXCLUDED.task_types, default_params = EXCLUDED.default_params, is_default = EXCLUDED.is_default, status = 'active', updated_at = NOW();"""
    sql_parts.append(sql)

# Deactivate old models
sql_parts.append("UPDATE model_profiles SET status = 'inactive', updated_at = NOW() WHERE profile_key IN ('completion-glm4-flash', 'completion-internlm-7b', 'completion-qwen15-7b') AND provider = 'siliconflow';")

full_sql = "\n".join(sql_parts)

# Execute via SSH
stdin, stdout, stderr = ssh.exec_command(f'psql -U novel_os -d novel_os -c "{full_sql}"')
print("=== Insert Result ===")
print(stdout.read().decode())
print(stderr.read().decode())

# Verify
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT profile_key, display_name, status, is_default FROM model_profiles WHERE status = 'active' ORDER BY is_default DESC, profile_key\""
)
print("=== Active Models ===")
print(stdout.read().decode())

ssh.close()
