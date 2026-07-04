import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== 修复 users.id 和 api_tokens.user_id 类型不匹配 ===")
    
    print("\n1. 查看当前 users 表结构...")
    rows = await pool.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position;")
    for row in rows:
        print(f"  {row['column_name']}: {row['data_type']}")
    
    print("\n2. 查看当前 api_tokens 表结构...")
    rows = await pool.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'api_tokens' ORDER BY ordinal_position;")
    for row in rows:
        print(f"  {row['column_name']}: {row['data_type']}")
    
    print("\n3. 修改 api_tokens.user_id 类型为 INTEGER...")
    await pool.execute("ALTER TABLE api_tokens ALTER COLUMN user_id TYPE INTEGER USING user_id::TEXT::INTEGER;")
    print("   ✅ 修改成功")
    
    print("\n4. 添加外键约束...")
    await pool.execute("ALTER TABLE api_tokens ADD CONSTRAINT fk_api_tokens_user_id FOREIGN KEY (user_id) REFERENCES users(id);")
    print("   ✅ 外键约束添加成功")
    
    print("\n5. 验证修复...")
    rows = await pool.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'api_tokens' ORDER BY ordinal_position;")
    for row in rows:
        print(f"  {row['column_name']}: {row['data_type']}")
    
    print("\n6. 验证数据...")
    rows = await pool.fetch("SELECT id, user_id, name, scopes FROM api_tokens LIMIT 3;")
    for row in rows:
        print(f"  id={row['id']}, user_id={row['user_id']}, name={row['name']}")
    
    await pool.close()
    print("\n✅ 修复完成！")

asyncio.run(main())