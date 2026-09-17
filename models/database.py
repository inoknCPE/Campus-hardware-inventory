import sqlite3
from logger import logger

def init_db(db_name="hardware_inventory.db"):
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                locked INTEGER DEFAULT 0,
                role TEXT DEFAULT 'user'
            )
            """
        )

        # Ensure persistent 'locked' column exists for user lock state (0 or 1)
        cursor.execute("PRAGMA table_info(users)")
        cols = [r[1] for r in cursor.fetchall()]
        if 'locked' not in cols:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN locked INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                # If alter fails for some reason, ignore; table may not exist yet or column may already be present
                pass
        if 'role' not in cols:
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            except sqlite3.OperationalError:
                pass

        # Table for admin-approved password reset requests
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                new_password_hash TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hardware (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                status TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS borrow_records (
                borrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                student_id TEXT NOT NULL,
                borrow_date TEXT NOT NULL,
                class_name TEXT NOT NULL,
                schedule TEXT NOT NULL,
                room TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Borrowed',
                returned_at TEXT
            )
            """
        )
        cursor.execute("PRAGMA table_info(borrow_records)")
        record_columns = [row[1] for row in cursor.fetchall()]
        if "requested_by" not in record_columns:
            cursor.execute("ALTER TABLE borrow_records ADD COLUMN requested_by TEXT NOT NULL DEFAULT ''")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS borrow_items (
                borrow_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                borrow_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY(borrow_id) REFERENCES borrow_records(borrow_id),
                FOREIGN KEY(item_id) REFERENCES hardware(item_id)
            )
            """
        )

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database setup error: {e}")