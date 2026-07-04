import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("\n=== users 数据 ===")
    rows = await pool.fetch("SELECT id, username, nickname, is_active, role FROM users LIMIT 10;")
    for row in rows:
        print(f"  id={row['id']}, username={row['username']}, nickname={row['nickname']}, is_active={row['is_active']}, role={row['role']}")
    
    print("\n=== api_tokens 数据 ===")
    rows = await pool.fetch("SELECT id, user_id, name, scopes, expires_at FROM api_tokens LIMIT 10;")
    for row in rows:
        print(f"  id={row['id']}, user_id={row['user_id']}, name={row['name']}, scopes={row['scopes']}")
    
    await pool.close()

asyncio.run(main())