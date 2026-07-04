import asyncio
import asyncpg

TABLES_TO_FIX = [
    'api_keys',
    'audit_logs',
    'evolutions',
    'llm_configs',
    'local_project_bindings',
    'model_usage_records',
    'operation_logs',
    'projects',
    'resolve_cache',
    'review_patterns',
    'rule_groups',
    'rules',
    'skill_groups',
    'skills',
    'user_knowledge',
    'workspace_members',
]

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== 批量修复所有 UUID 类型的 user_id 列 ===")
    
    for table_name in TABLES_TO_FIX:
        print(f"\n处理 {table_name}...")
        try:
            row = await pool.fetchrow(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table_name}' AND column_name = 'user_id';")
            if row and row['data_type'] == 'uuid':
                print(f"  修改 user_id 类型为 INTEGER...")
                await pool.execute(f"ALTER TABLE {table_name} ALTER COLUMN user_id TYPE INTEGER USING 0;")
                print(f"  ✅ {table_name}.user_id 修改成功")
            else:
                print(f"  ⚠️ {table_name}.user_id 已经是 INTEGER")
        except Exception as e:
            print(f"  ❌ {table_name} 错误: {e}")
    
    print("\n=== 验证修复 ===")
    rows = await pool.fetch('''
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE column_name LIKE '%user_id' AND data_type = 'uuid'
        ORDER BY table_name, column_name
    ''')
    
    if len(rows) == 0:
        print("  ✅ 没有发现 UUID 类型的 user_id 列")
    else:
        print(f"  ❌ 仍然有 {len(rows)} 个 UUID 类型的 user_id 列")
        for row in rows:
            print(f"    {row['table_name']}.{row['column_name']}")
    
    await pool.close()
    print("\n✅ 修复完成！")

asyncio.run(main())