import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== 测试 knowledge.category.list 查询 ===")
    rows = await pool.fetch('''
        SELECT id::text, slug, name, parent_id::text, level, is_active 
        FROM categories 
        WHERE level = 0 
        ORDER BY sort_order
        LIMIT 5
    ''')
    for row in rows:
        print(f"  {row}")
    
    print("\n=== 测试 knowledge.item.list 查询 ===")
    rows = await pool.fetch('''
        SELECT k.id::text, k.title, c.slug as category_slug
        FROM knowledge_base k
        LEFT JOIN categories c ON c.id = k.category_id
        WHERE k.status = 'active'
        LIMIT 5
    ''')
    for row in rows:
        print(f"  {row}")
    
    await pool.close()

asyncio.run(main())