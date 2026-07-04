import psycopg2

conn = psycopg2.connect(
    host='${NAS_HOST}',
    port=5432,
    database='novel_os',
    user='novel_os',
    password='novel_os_password'
)

cur = conn.cursor()
cur.execute("SELECT id, slug, name, parent_id, level FROM categories ORDER BY level, sort_order;")
rows = cur.fetchall()

print("=== 分类层级结构 ===")
for row in rows:
    indent = "  " * row[4]
    print(f"{indent}id={row[0]}, slug={row[1]}, name={row[2]}, parent_id={row[3]}, level={row[4]}")

cur.close()
conn.close()