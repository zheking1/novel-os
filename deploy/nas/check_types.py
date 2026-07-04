import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== categories 表结构 ===")
    rows = await pool.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'categories' ORDER BY ordinal_position;")
    for row in rows:
        print(f"  {row['column_name']}: {row['data_type']}")
    
    print("\n=== knowledge_base 表结构 ===")
    rows = await pool.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'knowledge_base' ORDER BY ordinal_position;")
    for row in rows:
        print(f"  {row['column_name']}: {row['data_type']}")
    
    print("\n=== users 表结构 ===")
    rows = await pool.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position;")
    for row in rows:
        print(f"  {row['column_name']}: {row['data_type']}")
    
    print("\n=== categories level=0 前3条 ===")
    rows = await pool.fetch("SELECT id, slug, name, parent_id FROM categories WHERE level = 0 LIMIT 3;")
    for row in rows:
        print(f"  id={row['id']}, slug={row['slug']}, name={row['name']}, parent_id={row['parent_id']}")
    
    print("\n=== knowledge_base 前3条 ===")
    rows = await pool.fetch("SELECT id, code, title, category_id FROM knowledge_base LIMIT 3;")
    for row in rows:
        print(f"  id={row['id']}, code={row['code']}, title={row['title']}, category_id={row['category_id']}")
    
    await pool.close()

asyncio.run(main())