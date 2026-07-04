import asyncio
import asyncpg

async def main():
    pool = await asyncpg.create_pool("postgresql://novel_os:${POSTGRES_PASSWORD}@localhost:5432/novel_os")
    
    print("=== users 表数据 ===")
    rows = await pool.fetch("SELECT id, username, password_hash, role, is_active FROM users;")
    for row in rows:
        print(f"  id={row['id']}, username={row['username']}, password_hash={row['password_hash']}, role={row['role']}, is_active={row['is_active']}")
    
    await pool.close()

asyncio.run(main())