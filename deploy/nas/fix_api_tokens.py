import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== 修复 api_tokens.user_id 类型不匹配 ===")
    
    print("\n1. 获取 admin 用户 ID...")
    row = await pool.fetchrow("SELECT id FROM users WHERE username = 'admin';")
    admin_id = row['id']
    print(f"   admin 用户 ID: {admin_id}")
    
    print("\n2. 删除旧的 api_tokens 记录（指向不存在的用户）...")
    await pool.execute("DELETE FROM api_tokens;")
    print("   ✅ 删除成功")
    
    print("\n3. 修改 api_tokens.user_id 类型为 INTEGER...")
    await pool.execute("ALTER TABLE api_tokens ALTER COLUMN user_id TYPE INTEGER USING 0;")
    print("   ✅ 修改成功")
    
    print("\n4. 添加外键约束...")
    try:
        await pool.execute("ALTER TABLE api_tokens ADD CONSTRAINT fk_api_tokens_user_id FOREIGN KEY (user_id) REFERENCES users(id);")
        print("   ✅ 外键约束添加成功")
    except Exception as e:
        print(f"   ⚠️ 外键可能已存在: {e}")
    
    print("\n5. 创建新的 admin token...")
    import secrets
    token = "nos_" + secrets.token_urlsafe(32)
    import hashlib
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    
    await pool.execute('''
        INSERT INTO api_tokens (user_id, name, token_hash, scopes)
        VALUES ($1, 'web-console-admin', $2, ARRAY['admin','read','write']::TEXT[])
    ''', admin_id, token_hash)
    
    print(f"   ✅ 创建成功")
    
    print("\n6. 更新 web 用户配置...")
    import json
    web_users_path = "/opt/novel-os/data/web/users.json"
    try:
        with open(web_users_path, 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        if users:
            username = next(iter(users))
            users[username]["mcp_token"] = token
            with open(web_users_path, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            print(f"   ✅ 更新 web 用户 '{username}' 成功")
    except Exception as e:
        print(f"   ⚠️ 更新 web 用户失败: {e}")
        print(f"   Token: {token}")
        print(f"   请手动更新 {web_users_path} 中的 mcp_token")
    
    print("\n7. 验证修复...")
    rows = await pool.fetch("SELECT id, user_id, name, scopes FROM api_tokens;")
    for row in rows:
        print(f"  {row}")
    
    await pool.close()
    print("\n✅ 修复完成！")

asyncio.run(main())