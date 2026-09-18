import os

import psycopg


with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, username, email, role, locked FROM users ORDER BY id")
        rows = cursor.fetchall()

if not rows:
    print("No users in users table")
else:
    for row in rows:
        print(row)
