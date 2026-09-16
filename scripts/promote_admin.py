import sqlite3

db='hardware_inventory.db'
conn = sqlite3.connect(db)
c = conn.cursor()
try:
    c.execute("UPDATE users SET role='admin' WHERE username = 'Admin'")
    conn.commit()
    c.execute('SELECT id, username, email, role, locked FROM users')
    rows = c.fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print('Error:', e)
finally:
    conn.close()
