import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== 完整 users 数据 ===")
    rows = await pool.fetch("SELECT * FROM users;")
    for row in rows:
        print(f"  {row}")
    
    print("\n=== 完整 api_tokens 数据 ===")
    rows = await pool.fetch("SELECT id, user_id, name, scopes FROM api_tokens;")
    for row in rows:
        print(f"  {row}")
    
    print("\n=== 检查是否有其他 schema ===")
    rows = await pool.fetch("SELECT schema_name FROM information_schema.schemata;")
    for row in rows:
        print(f"  schema: {row['schema_name']}")
    
    print("\n=== 检查所有 users 表 ===")
    rows = await pool.fetch("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = 'users';")
    for row in rows:
        print(f"  {row['table_schema']}.{row['table_name']}")
    
    await pool.close()

asyncio.run(main())