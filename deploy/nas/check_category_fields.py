import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== is_active 统计 ===")
    rows = await pool.fetch('''
        SELECT is_active, COUNT(*) as count 
        FROM categories 
        GROUP BY is_active
    ''')
    for row in rows:
        print(f"is_active={row['is_active']}: {row['count']} 条")
    
    print("\n=== 一级分类 (is_active=false) ===")
    rows = await pool.fetch('''
        SELECT slug, name, is_active 
        FROM categories 
        WHERE level = 0 AND is_active = false
        ORDER BY sort_order
    ''')
    for row in rows:
        print(f"slug={row['slug']}, name={row['name']}, is_active={row['is_active']}")
    
    print("\n=== knowledge_base status 统计 ===")
    rows = await pool.fetch('''
        SELECT status, COUNT(*) as count 
        FROM knowledge_base 
        GROUP BY status
    ''')
    for row in rows:
        print(f"status={row['status']}: {row['count']} 条")
    
    await pool.close()

asyncio.run(main())