import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== 修复分类层级 ===")
    
    print("\n1. 查找有 parent_id 但 level=0 的分类...")
    rows = await pool.fetch("SELECT id::text, slug, name, parent_id::text, level FROM categories WHERE parent_id IS NOT NULL AND level = 0 ORDER BY slug;")
    print(f"   发现 {len(rows)} 个有问题的分类")
    for row in rows:
        print(f"     {row['slug']} ({row['name']}): level={row['level']}")
    
    print("\n2. 更新这些分类的 level...")
    count = 0
    for row in rows:
        parent_row = await pool.fetchrow("SELECT level FROM categories WHERE id = $1;", row['parent_id'])
        if parent_row:
            new_level = parent_row['level'] + 1
            await pool.execute("UPDATE categories SET level = $1 WHERE id = $2;", new_level, row['id'])
            count += 1
    print(f"   ✅ 更新了 {count} 个分类")
    
    print("\n3. 验证修复...")
    rows = await pool.fetch("SELECT id::text, slug, name, level FROM categories WHERE parent_id IS NOT NULL AND level = 0 ORDER BY slug;")
    if len(rows) == 0:
        print("   ✅ 没有发现有问题的分类")
    else:
        print(f"   ❌ 仍然有 {len(rows)} 个有问题的分类")
    
    print("\n4. 检查一级分类...")
    rows = await pool.fetch("SELECT slug, name, level FROM categories WHERE level = 0 ORDER BY sort_order LIMIT 10;")
    for row in rows:
        print(f"     {row['slug']} ({row['name']}): level={row['level']}")
    
    await pool.close()
    print("\n✅ 修复完成！")

asyncio.run(main())