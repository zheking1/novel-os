import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== 检查所有引用 users(id) 的列 ===")
    rows = await pool.fetch('''
        SELECT 
            tc.table_name, 
            kcu.column_name,
            kcu.table_schema,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM 
            information_schema.table_constraints tc
        JOIN 
            information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN 
            information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE 
            tc.constraint_type = 'FOREIGN KEY'
            AND ccu.table_name = 'users'
        ORDER BY 
            tc.table_name, kcu.column_name
    ''')
    
    print("外键约束:")
    for row in rows:
        col_type = await pool.fetchrow(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{row['table_name']}' AND column_name = '{row['column_name']}';")
        print(f"  {row['table_name']}.{row['column_name']}: {col_type['data_type']} -> users.id(integer)")
    
    print("\n=== 检查所有 UUID 类型的 user_id 或 user 相关列 ===")
    rows = await pool.fetch('''
        SELECT table_name, column_name, data_type 
        FROM information_schema.columns 
        WHERE column_name LIKE '%user%' AND data_type = 'uuid'
        ORDER BY table_name, column_name
    ''')
    
    for row in rows:
        print(f"  {row['table_name']}.{row['column_name']}: {row['data_type']}")
    
    await pool.close()

asyncio.run(main())