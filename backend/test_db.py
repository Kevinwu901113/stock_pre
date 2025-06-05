import sqlite3

conn = sqlite3.connect('stock.db')
cursor = conn.cursor()

# 测试JOIN查询
cursor.execute('SELECT r.*, s.name FROM recommendations r JOIN stocks s ON r.stock_code = s.code WHERE r.is_active = 1 LIMIT 2')
rows = cursor.fetchall()

print('查询结果:')
for row in rows:
    print(row)

conn.close()