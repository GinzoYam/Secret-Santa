import sqlite3
import random
import string
from contextlib import contextmanager

DB_NAME = 'santa.db'


class RoomNotFoundError(Exception):
    pass


class DuplicateError(Exception):
    pass


def generate_room_code(length=6):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


@contextmanager
def db_cursor():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db_cursor() as cursor:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                room_code TEXT NOT NULL UNIQUE,
                admin_code TEXT
            )
        ''')
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


def create_room(title):
    room_code = generate_room_code()
    try:
        with db_cursor() as cursor:
            cursor.execute(
                'INSERT INTO rooms (title, room_code) VALUES (?, ?)',
                (title, room_code)
            )
            new_id = cursor.lastrowid
        return {"id": new_id, "title": title, "room_code": room_code}
    except sqlite3.IntegrityError:
        raise DuplicateError("Комната с таким кодом уже существует")


def get_room(room_id):
    with db_cursor() as cursor:
        cursor.execute('SELECT * FROM rooms WHERE id = ?', (room_id,))
        row = cursor.fetchone()
    if row is None:
        raise RoomNotFoundError(room_id)
    return dict(row)


def add_participant(room_id, name, email, wish):
    try:
        with db_cursor() as cursor:
            cursor.execute('SELECT id FROM rooms WHERE id = ?', (room_id,))
            if cursor.fetchone() is None:
                raise RoomNotFoundError(room_id)
            cursor.execute(
                'INSERT INTO participants (room_id, name, email, wish) VALUES (?, ?, ?, ?)',
                (room_id, name, email, wish)
            )
            new_id = cursor.lastrowid
        return {"id": new_id, "room_id": room_id, "name": name, "email": email}
    except sqlite3.IntegrityError:
        raise DuplicateError("Участник с таким email уже есть в этой комнате")


def get_participants(room_id):
    with db_cursor() as cursor:
        cursor.execute('SELECT id FROM rooms WHERE id = ?', (room_id,))
        if cursor.fetchone() is None:
            raise RoomNotFoundError(room_id)
        cursor.execute(
            'SELECT * FROM participants WHERE room_id = ? ORDER BY id',
            (room_id,)
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


if __name__ == '__main__':
    init_db()
