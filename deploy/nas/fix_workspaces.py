import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== 修复 workspaces.owner_user_id 类型不匹配 ===")
    
    print("\n1. 查看 workspaces 数据...")
    rows = await pool.fetch("SELECT id, slug, name, owner_user_id FROM workspaces;")
    for row in rows:
        print(f"  id={row['id']}, slug={row['slug']}, owner_user_id={row['owner_user_id']}")
    
    print("\n2. 获取 admin 用户 ID...")
    row = await pool.fetchrow("SELECT id FROM users WHERE username = 'admin';")
    admin_id = row['id']
    print(f"   admin 用户 ID: {admin_id}")
    
    print("\n3. 修改 workspaces.owner_user_id 类型为 INTEGER...")
    await pool.execute("ALTER TABLE workspaces ALTER COLUMN owner_user_id TYPE INTEGER USING 0;")
    print("   ✅ 修改成功")
    
    print("\n4. 更新 workspaces.owner_user_id 为 admin...")
    await pool.execute("UPDATE workspaces SET owner_user_id = $1 WHERE owner_user_id = 0;", admin_id)
    print("   ✅ 更新成功")
    
    print("\n5. 验证修复...")
    rows = await pool.fetch("SELECT id, slug, name, owner_user_id FROM workspaces;")
    for row in rows:
        print(f"  id={row['id']}, slug={row['slug']}, owner_user_id={row['owner_user_id']}")
    
    await pool.close()
    print("\n✅ 修复完成！")

asyncio.run(main())