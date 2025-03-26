import sqlite3

def get_connection():
    return sqlite3.connect("sleep_bot.db", check_same_thread=False)

def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sleep_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                sleep_time DATETIME,
                wake_time DATETIME,
                sleep_quality INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                sleep_record_id INTEGER,
                FOREIGN KEY(sleep_record_id) REFERENCES sleep_records(id)
            )
        """)
        conn.commit()
