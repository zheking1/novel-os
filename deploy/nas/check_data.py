import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    kb_count = await pool.fetchval("SELECT COUNT(*) FROM knowledge_base")
    cat_count = await pool.fetchval("SELECT COUNT(*) FROM categories")
    
    print(f"knowledge_base: {kb_count} 条")
    print(f"categories: {cat_count} 条")
    
    rows = await pool.fetch('''
        SELECT source, COUNT(*) as count
        FROM knowledge_base
        GROUP BY source
    ''')
    for row in rows:
        print(f"  source={row['source']}: {row['count']} 条")
    
    rows = await pool.fetch('''
        SELECT c.slug, c.name, COUNT(k.id) as count
        FROM categories c
        LEFT JOIN knowledge_base k ON k.category_id = c.id
        GROUP BY c.id, c.slug, c.name
        ORDER BY count DESC
        LIMIT 20
    ''')
    print("\n分类数据分布:")
    for row in rows:
        print(f"  {row['slug']:30} ({row['name']}): {row['count']:4} 条")
    
    await pool.close()

asyncio.run(main())