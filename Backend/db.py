import sqlite3
import random
import string
from contextlib import contextmanager

DB_NAME = 'santa.db'  # файл базы создаётся рядом с местом запуска


# ---------- Исключения ----------
# Свои исключения — это «сигналы бизнес-ситуаций», а не технических сбоев.
# app.py ловит их и переводит в правильные HTTP-коды:
#   RoomNotFoundError -> 404 (человек ошибся ссылкой/кодом комнаты)
#   DuplicateError    -> 409 (дубль: уже существует, повторное действие)
# Всё остальное считается реальной поломкой -> 500

class RoomNotFoundError(Exception):
    """Бизнес-ситуация: комнаты с таким id не существует."""
    pass


class DuplicateError(Exception):
    """Бизнес-ситуация: нарушение уникальности (дубль room_code или email)."""
    pass


class PermissionError(Exception):
    """Бизнес-ситуация: доступ к данным запрещён настройками комнаты
    (например, пары скрыты от ведущего галочкой show_pairs)."""
    pass


# ---------- Контекстный менеджер с откатом транзакций ----------
# Бизнес-смысл: данные в базе всегда должны быть в «честном» состоянии.
# Если операция не выполнена целиком — ничего не должно измениться.
# Заменяет ручные conn.commit() / conn.close() в каждой функции.
# Гарантии:
#   1) успех  -> conn.commit() (изменения зафиксированы)
#   2) ошибка -> conn.rollback() (частично изменённые данные откатываются,
#                соединение не остаётся с незавершённой транзакцией)
#   3) в любом случае -> conn.close() (нет «зависших» соединений,
#                которые могли бы заблокировать базу для других запросов)

@contextmanager
def db_cursor():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # строки можно читать по имени колонки
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()      # всё прошло хорошо — фиксируем изменения
    except Exception:
        conn.rollback()    # ошибка — откатываем незавершённые изменения
        raise              # пробрасываем исключение дальше (Flask его обработает)
    finally:
        conn.close()       # соединение закрывается при любом исходе


# ---------- Утилиты ----------

def get_db_connection():
    """Простое подключение (нужно для init_db; в остальном коде используем db_cursor)."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def generate_room_code(length=6):
    """Код комнаты: случайные заглавные буквы и цифры, например 'K3M9XQ'.
    Бизнес-смысл: участники вводят этот код, чтобы найти комнату организатора,
    поэтому код должен быть коротким, читаемым и сложноугадываемым."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


# ---------- Инициализация базы ----------
# Структура данных «Тайного Санты»:
#   rooms        — комнаты (одна игра = одна комната)
#   participants — участники, привязанные к комнате
#   assignments  — пары «кто дарит -> кому дарит» (результат жеребьёвки)

def init_db():
    """Создаёт все таблицы, если их ещё нет. Безопасно запускать многократно."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            room_code TEXT NOT NULL UNIQUE,
            admin_code TEXT,
            show_pairs INTEGER NOT NULL DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            wish TEXT,
            UNIQUE (room_id, email),   -- бизнес-правило: один email не может войти в комнату дважды
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            giver_id INTEGER NOT NULL,      -- кто дарит
            receiver_id INTEGER NOT NULL,   -- кому дарит
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE (room_id, giver_id),     -- бизнес-правило: у каждого дарителя ровно один получатель
            CHECK (giver_id <> receiver_id), -- бизнес-правило: нельзя дарить самому себе
            FOREIGN KEY (room_id) REFERENCES rooms (id),
            FOREIGN KEY (giver_id) REFERENCES participants (id),
            FOREIGN KEY (receiver_id) REFERENCES participants (id)
        )
    ''')

    # --- Миграция для баз, созданных до появления show_pairs ---
    # SQLite не поддерживает ADD COLUMN IF NOT EXISTS, поэтому проверяем
    # фактическую структуру таблицы через PRAGMA table_info
    cursor.execute('PRAGMA table_info(rooms)')
    columns = {row[1] for row in cursor.fetchall()}
    if 'show_pairs' not in columns:
        # 0 = пары скрыты от ведущего (безопасное значение по умолчанию)
        cursor.execute('ALTER TABLE rooms ADD COLUMN show_pairs INTEGER NOT NULL DEFAULT 0')

    conn.commit()
    conn.close()


# ---------- Комнаты ----------

def create_room(title, show_pairs=False):
    """Создаёт комнату. Бросает ValueError при пустом названии,
    DuplicateError при конфликте уникального room_code.

    show_pairs — галочка «показывать все пары ведущему»:
    True  -> ведущий сможет посмотреть полный список пар,
    False -> пары скрыты (по умолчанию), смотрите только участники индивидуально."""
    # Валидация: сначала тип, потом содержимое (строка из пробелов тоже «пустая»)
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Название комнаты обязательно и не может быть пустым")

    # Приводим галочку к булеву типу: на вход может прийти что угодно из JSON
    show_pairs = bool(show_pairs)
    title = title.strip()          # сохраняем без лишних пробелов по краям
    room_code = generate_room_code()

    with db_cursor() as cursor:
        try:
            cursor.execute(
                'INSERT INTO rooms (title, room_code, show_pairs) VALUES (?, ?, ?)',
                (title, room_code, 1 if show_pairs else 0)
            )
        except sqlite3.IntegrityError:
            # Столкновение сгенерированного кода с существующим (очень редкий случай:
            # 36^6 вариантов). Клиент просто повторит попытку и получит новый код
            raise DuplicateError("Комната с таким кодом уже существует")
        new_id = cursor.lastrowid

    return {"id": new_id, "title": title, "room_code": room_code, "show_pairs": show_pairs}


def get_room(room_id):
    """Возвращает комнату по id или бросает RoomNotFoundError."""
    with db_cursor() as cursor:
        cursor.execute('SELECT * FROM rooms WHERE id = ?', (room_id,))
        row = cursor.fetchone()
    if row is None:
        raise RoomNotFoundError(f"Комната {room_id} не найдена")
    return dict(row)


# ---------- Участники ----------

def add_participant(room_id, name, email, wish):
    """Добавляет участника в комнату.
    Бросает ValueError при невалидных данных,
    RoomNotFoundError если комнаты нет,
    DuplicateError если email уже есть в этой комнате."""
    # --- Валидация имени: без имени Санта не сможет подписать подарок ---
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Имя обязательно и не может быть пустым")
    name = name.strip()

    # --- Валидация email (базовая: есть @ и точка в домене) ---
    # email — главный идентификатор участника, по нему исключаются дубли
    if not isinstance(email, str) or '@' not in email or '.' not in email.split('@', 1)[1]:
        raise ValueError("Укажите корректный email")
    email = email.strip().lower()  # нормализация: Anya@mail.ru == anya@mail.ru

    # --- Пожелание: необязательно, но если есть — строка ---
    # Санта прочитает это пожелание, чтобы выбрать подарок
    if wish is not None and not isinstance(wish, str):
        raise ValueError("Пожелание должно быть строкой")
    wish = wish.strip() if isinstance(wish, str) else None

    with db_cursor() as cursor:
        # Сначала убеждаемся, что комната существует:
        # нельзя присоединиться к игре, которой нет
        cursor.execute('SELECT id FROM rooms WHERE id = ?', (room_id,))
        if cursor.fetchone() is None:
            raise RoomNotFoundError(f"Комната {room_id} не найдена")

        # UNIQUE (room_id, email) в базе ловит дубликат, даже если два запроса
        # пришли одновременно (защита от race condition — без предварительного SELECT).
        # Бизнес-смысл: один человек не может зайти в одну игру дважды
        try:
            cursor.execute(
                'INSERT INTO participants (room_id, name, email, wish) VALUES (?, ?, ?, ?)',
                (room_id, name, email, wish)
            )
        except sqlite3.IntegrityError:
            raise DuplicateError("Участник с таким email уже есть в этой комнате")
        new_id = cursor.lastrowid

    return {"id": new_id, "room_id": room_id, "name": name, "email": email, "wish": wish}


def get_participants(room_id):
    """Возвращает список участников комнаты или бросает RoomNotFoundError."""
    with db_cursor() as cursor:
        # Проверяем существование комнаты, чтобы отличить
        # «комнаты нет» (404) от «комната есть, но пока пустая» (пустой список)
        cursor.execute('SELECT id FROM rooms WHERE id = ?', (room_id,))
        if cursor.fetchone() is None:
            raise RoomNotFoundError(f"Комната {room_id} не найдена")

        # ORDER BY id — участники отображаются в порядке присоединения к игре
        cursor.execute(
            'SELECT * FROM participants WHERE room_id = ? ORDER BY id',
            (room_id,)
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


# ---------- Жеребьёвка ----------
# Бизнес-логика: жеребьёвка проводится ОДИН раз на комнату. Каждый участник
# становится Тайным Сантой ровно одного человека. Пары замыкаются в круг:
# первый дарит второму, второй третьему, ..., последний дарит первому —
# так гарантированно нет «сам себе» и нет разорванных цепочек.

def perform_shuffle(room_id):
    """Проводит жеребьёвку в комнате и записывает пары в assignments.
    Бросает RoomNotFoundError если комнаты нет,
    DuplicateError если жеребьёвка уже проводилась (перемешивать дважды нельзя),
    ValueError если участников меньше трёх (на двух жеребьёвка теряет смысл)."""
    with db_cursor() as cursor:
        # 1. Комната должна существовать — иначе это не бизнес-ситуация, а 404
        cursor.execute('SELECT id FROM rooms WHERE id = ?', (room_id,))
        if cursor.fetchone() is None:
            raise RoomNotFoundError(f"Комната {room_id} не найдена")

        # 2. Защита от повторной жеребьёвки: если пары уже есть — нельзя.
        #    В противном случае у одного дарителя оказалось бы два получателя,
        #    что нарушает UNIQUE (room_id, giver_id)
        cursor.execute('SELECT COUNT(*) FROM assignments WHERE room_id = ?', (room_id,))
        if cursor.fetchone()[0] > 0:
            raise DuplicateError("Жеребьёвка в этой комнате уже проведена")

        # 3. Минимум 3 участника: на двух получаются пары «друг другу»,
        #    что раскрывает обоих — игра теряет смысл
        cursor.execute('SELECT id FROM participants WHERE room_id = ?', (room_id,))
        participant_ids = [row['id'] for row in cursor.fetchall()]
        if len(participant_ids) < 3:
            raise ValueError("Для жеребьёвки нужно минимум 3 участника")

        # 4. Перемешиваем и замыкаем в круг: ids[i] дарит ids[i+1],
        #    последний — первому. CHECK (giver_id <> receiver_id)
        #    в таблице не сработает никогда: у каждого ровно один сосед
        random.shuffle(participant_ids)
        pairs = [
            (participant_ids[i], participant_ids[(i + 1) % len(participant_ids)])
            for i in range(len(participant_ids))
        ]

        # 5. Все вставки в одной транзакции: либо все пары записаны,
        #    либо (при любой ошибке) откатится всё — полупустой жеребьёвки не будет
        for giver_id, receiver_id in pairs:
            cursor.execute(
                'INSERT INTO assignments (room_id, giver_id, receiver_id) VALUES (?, ?, ?)',
                (room_id, giver_id, receiver_id)
            )

    return len(pairs)


def get_assignments(room_id):
    """Возвращает все пары комнаты для ведущего (с именами и email).
    Бросает RoomNotFoundError если комнаты нет,
    ValueError если жеребьёвка ещё не проводилась,
    PermissionError если в комнате пары скрыты от ведущего (show_pairs = 0)."""
    with db_cursor() as cursor:
        cursor.execute('SELECT * FROM rooms WHERE id = ?', (room_id,))
        room = cursor.fetchone()
        if room is None:
            raise RoomNotFoundError(f"Комната {room_id} не найдена")

        # Галочка «показывать пары ведущему» ставится только при создании
        # комнаты и не меняется после — ведущий всегда знает, что увидит
        if not room['show_pairs']:
            raise PermissionError("Пары скрыты: ведущий не включал показ пар")

        cursor.execute('SELECT COUNT(*) FROM assignments WHERE room_id = ?', (room_id,))
        if cursor.fetchone()[0] == 0:
            raise ValueError("Жеребьёвка ещё не проводилась")

        # JOIN по participants дважды: отдельно для дарителя и получателя,
        # чтобы ведущий видел человеческие имена, а не голые id
        cursor.execute('''
            SELECT a.id, g.name AS giver_name, g.email AS giver_email,
                   r.name AS receiver_name, r.email AS receiver_email,
                   a.created_at
            FROM assignments a
            JOIN participants g ON g.id = a.giver_id
            JOIN participants r ON r.id = a.receiver_id
            WHERE a.room_id = ?
            ORDER BY a.id
        ''', (room_id,))
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


if __name__ == '__main__':
    # Возможность инициализировать базу отдельно: python db.py
    init_db()
    print('База данных готова.')
