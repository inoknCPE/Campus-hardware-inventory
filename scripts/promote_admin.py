import argparse
import os

import psycopg


parser = argparse.ArgumentParser(description="Promote a user in PostgreSQL.")
parser.add_argument("username")
args = parser.parse_args()

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE users SET role = 'ADMIN' WHERE username = %s RETURNING username",
            (args.username,),
        )
        updated = cursor.fetchone()

if updated:
    print(f"Promoted {updated[0]} to ADMIN.")
else:
    print(f"No user found for username: {args.username}")
