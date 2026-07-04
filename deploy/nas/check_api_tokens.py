import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== api_tokens 表结构 ===")
    rows = await pool.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'api_tokens' ORDER BY ordinal_position;")
    for row in rows:
        print(f"  {row['column_name']}: {row['data_type']}")
    
    print("\n=== api_tokens 数据 ===")
    rows = await pool.fetch("SELECT id, user_id, name, scopes FROM api_tokens LIMIT 5;")
    for row in rows:
        print(f"  id={row['id']}, user_id={row['user_id']}, name={row['name']}, scopes={row['scopes']}")
    
    await pool.close()

asyncio.run(main())