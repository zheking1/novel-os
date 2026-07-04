import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== 检查所有外键关系 ===")
    rows = await pool.fetch('''
        SELECT 
            tc.table_name, 
            kcu.column_name, 
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
        ORDER BY 
            tc.table_name, kcu.column_name
    ''')
    
    for row in rows:
        print(f"  {row['table_name']}.{row['column_name']} -> {row['foreign_table_name']}.{row['foreign_column_name']}")
    
    print("\n=== 检查所有引用 users(id) 的列 ===")
    rows = await pool.fetch('''
        SELECT 
            tc.table_name, 
            kcu.column_name,
            kcu.ordinal_position
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
    
    for row in rows:
        print(f"  {row['table_name']}.{row['column_name']}")
    
    print("\n=== 检查 workspaces 表结构 ===")
    rows = await pool.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'workspaces' ORDER BY ordinal_position;")
    for row in rows:
        print(f"  {row['column_name']}: {row['data_type']}")
    
    await pool.close()

asyncio.run(main())