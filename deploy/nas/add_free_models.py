import paramiko
import json

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('${NAS_HOST}', username='root', password='${NAS_SSH_PASSWORD}')

# Model configurations - ordered by capability (strongest first)
models = [
    # Tier 1: Strongest models (Primary)
    {
        "profile_key": "completion-glm4-9b",
        "display_name": "GLM-4-9B (Primary)",
        "model_name": "THUDM/GLM-4-9B-0414",
        "task_types": ["completion", "draft", "outline", "revision"],
        "tier": "standard",
        "is_default": True,
    },
    {
        "profile_key": "completion-deepseek-r1-8b",
        "display_name": "DeepSeek-R1-Qwen3-8B (Reasoning)",
        "model_name": "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
        "task_types": ["completion", "draft", "outline", "reasoning"],
        "tier": "standard",
        "is_default": False,
    },
    
    # Tier 2: Good balance (Secondary)
    {
        "profile_key": "completion-qwen2.5-7b",
        "display_name": "Qwen2.5-7B-Instruct (Balanced)",
        "model_name": "Qwen/Qwen2.5-7B-Instruct",
        "task_types": ["completion", "draft", "revision"],
        "tier": "standard",
        "is_default": False,
    },
    {
        "profile_key": "completion-qwen3-8b",
        "display_name": "Qwen3-8B (Fast)",
        "model_name": "Qwen/Qwen3-8B",
        "task_types": ["completion", "draft", "outline"],
        "tier": "standard",
        "is_default": False,
    },
    {
        "profile_key": "completion-glm-z1-9b",
        "display_name": "GLM-Z1-9B (Reasoning)",
        "model_name": "THUDM/GLM-Z1-9B-0414",
        "task_types": ["completion", "draft", "outline", "reasoning"],
        "tier": "standard",
        "is_default": False,
    },
    
    # Tier 3: Light/Fallback
    {
        "profile_key": "completion-qwen3.5-4b",
        "display_name": "Qwen3.5-4B (Light)",
        "model_name": "Qwen/Qwen3.5-4B",
        "task_types": ["completion", "draft"],
        "tier": "standard",
        "is_default": False,
    },
    {
        "profile_key": "completion-hunyuan-7b",
        "display_name": "Hunyuan-MT-7B (Translation)",
        "model_name": "tencent/Hunyuan-MT-7B",
        "task_types": ["completion", "translation"],
        "tier": "standard",
        "is_default": False,
    },
]

# Default params for siliconflow
default_params = {
    "api_url": "https://api.siliconflow.cn",
    "api_key": "sk-hpadhczqmozktlndxvrgweqsyjcvljacbdwrehwijrgzifyb",
    "temperature": 0.7,
    "max_tokens": 4096,
}

cost_config = {
    "input_per_1k": 0.0,
    "output_per_1k": 0.0,
}

# Generate SQL
sql_lines = []
sql_lines.append("-- Insert free models from SiliconFlow")
sql_lines.append("")

for i, m in enumerate(models):
    profile_key = m["profile_key"]
    display_name = m["display_name"]
    model_name = m["model_name"]
    task_types = "ARRAY[" + ",".join([f"'{t}'" for t in m["task_types"]]) + "]"
    tier = m["tier"]
    is_default = "true" if m["is_default"] else "false"
    
    sql = f"""
INSERT INTO model_profiles 
  (project_id, profile_key, display_name, provider, model_name, task_types, tier, default_params, cost_config, is_default, status, user_id)
VALUES 
  ((SELECT id FROM projects WHERE slug = 'default'), 
   '{profile_key}', '{display_name}', 'siliconflow', '{model_name}', 
   {task_types}, '{tier}', '{json.dumps(default_params)}', '{json.dumps(cost_config)}', 
   {is_default}, 'active', 'admin')
ON CONFLICT (project_id, profile_key) DO UPDATE
SET display_name = '{display_name}', model_name = '{model_name}', task_types = {task_types},
    default_params = '{json.dumps(default_params)}', cost_config = '{json.dumps(cost_config)}',
    is_default = {is_default}, updated_at = NOW();
"""
    sql_lines.append(sql)

# Mark old deepseek models as inactive
sql_lines.append("""
-- Deactivate old deepseek models (may not be free)
UPDATE model_profiles 
SET status = 'inactive', updated_at = NOW() 
WHERE profile_key IN ('completion-glm4-flash', 'completion-internlm-7b', 'completion-qwen15-7b')
  AND provider = 'siliconflow';
""")

full_sql = "\n".join(sql_lines)

# Write and execute
with open('/tmp/add_free_models.sql', 'w', encoding='utf-8') as f:
    f.write(full_sql)

stdin, stdout, stderr = ssh.exec_command('cat > /tmp/add_free_models.sql', full_sql)
print("SQL written")

stdin, stdout, stderr = ssh.exec_command('docker cp /tmp/add_free_models.sql novel-postgres:/tmp/')
stdin, stdout, stderr = ssh.exec_command('docker exec novel-postgres psql -U novel_os -d novel_os -f /tmp/add_free_models.sql')
print("=== Result ===")
print(stdout.read().decode())
print(stderr.read().decode())

# Verify
stdin, stdout, stderr = ssh.exec_command(
    "docker exec novel-postgres psql -U novel_os -d novel_os -c \"SELECT profile_key, display_name, status, is_default FROM model_profiles WHERE status = 'active' ORDER BY profile_key\""
)
print("=== Active Models ===")
print(stdout.read().decode())

ssh.close()
