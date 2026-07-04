import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    columns = [
        ('project_members', 'user_id'),
        ('review_queue', 'reviewed_by'),
        ('review_queue', 'user_id'),
        ('workspaces', 'owner_user_id'),
        ('api_tokens', 'user_id'),
    ]
    
    print("=== 检查所有引用 users(id) 的列类型 ===")
    for table, column in columns:
        rows = await pool.fetch(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{column}';")
        if rows:
            print(f"  {table}.{column}: {rows[0]['data_type']}")
    
    print("\n=== 检查 api_tokens.workspace_id 类型 ===")
    rows = await pool.fetch("SELECT data_type FROM information_schema.columns WHERE table_name = 'api_tokens' AND column_name = 'workspace_id';")
    if rows:
        print(f"  api_tokens.workspace_id: {rows[0]['data_type']}")
    
    await pool.close()

asyncio.run(main())