import sqlite3
import random
import string

DB_NAME = 'santa.db'

def generate_room_code(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            room_code TEXT NOT NULL UNIQUE,
            admin_code TEXT
        )
    ''')
    conn.commit()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            wish TEXT,
            UNIQUE (room_id, email),
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        )
    ''')
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()

