import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== 检查 users 表结构 ===")
    rows = await pool.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position;")
    for row in rows:
        print(f"  {row['column_name']}: {row['data_type']}")
    
    print("\n=== 添加 status 字段 ===")
    try:
        await pool.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';")
        print("  ✅ status 字段添加成功")
    except Exception as e:
        print(f"  ❌ 错误: {e}")
    
    print("\n=== 更新所有用户状态 ===")
    await pool.execute("UPDATE users SET status = 'active' WHERE status IS NULL;")
    print("  ✅ 更新成功")
    
    print("\n=== 验证 ===")
    rows = await pool.fetch("SELECT id, username, status FROM users;")
    for row in rows:
        print(f"  id={row['id']}, username={row['username']}, status={row['status']}")
    
    await pool.close()
    print("\n✅ 修复完成！")

asyncio.run(main())