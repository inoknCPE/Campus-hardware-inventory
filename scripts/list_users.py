import sqlite3
import os

db = 'hardware_inventory.db'
if not os.path.exists(db):
    print('DB not found:', db)
else:
    conn = sqlite3.connect(db)
    c = conn.cursor()
    try:
        c.execute('SELECT id, username, email, role, locked FROM users')
        rows = c.fetchall()
        if not rows:
            print('No users in users table')
        else:
            for r in rows:
                print(r)
    except Exception as e:
        print('Error querying users table:', e)
    finally:
        conn.close()
