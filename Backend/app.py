from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from db import get_db_connection, generate_room_code, init_db  # импортируем функцию генерации кода

app = Flask(__name__)
CORS(app)

DB_NAME = 'santa.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return "Backend is working!"

# POST /api/rooms — создать комнату
@app.route('/api/rooms', methods=['POST'])
def create_room():
    try:
        data = request.get_json() or {}
        title = data.get('title')

        if not title:
            return jsonify({
                "success": False,
                "error": "Поле title обязательно"
            }), 400

        # Генерируем уникальный код
        room_code = generate_room_code()

        conn = get_db_connection()
        cursor = conn.cursor()

        # Вставляем в БД
        cursor.execute('''
            INSERT INTO rooms (title, room_code)
            VALUES (?, ?)
        ''', (title, room_code))

        new_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "data": {
                "id": new_id,
                "title": title,
                "room_code": room_code
            },
            "message": "Комната создана"
        }), 201

    except sqlite3.IntegrityError:
        # Если вдруг код не уникален (крайне маловероятно) — пробуем ещё раз
        # Для учебного проекта можно просто вернуть ошибку, но здесь сделаем повтор
        room_code = generate_room_code()
        # (в реальном проекте лучше зациклить или использовать UUID)
        return jsonify({
            "success": False,
            "error": "Конфликт уникального кода (попробуйте создать комнату ещё раз)"
        }), 409
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Внутренняя ошибка",
            "details": str(e)
        }), 500

# GET /api/rooms/<id> — получить одну комнату по ID
@app.route('/api/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM rooms WHERE id = ?', (room_id,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return jsonify({
                "success": False,
                "error": "Комната не найдена"
            }), 404

        room = dict(row)

        return jsonify({
            "success": True,
            "data": room
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Внутренняя ошибка",
            "details": str(e)
        }), 500

    @app.route('/api/rooms/<int:room_id>/users', methods=['POST'])
    def add_participant(room_id):
        data = request.get_json() or {}
        name = data.get('name')
        email = data.get('email')
        wish = data.get('wish')

        # Валидация ввода — 400
        if not name or not email:
            return jsonify({"success": False,
                            "error": "Поля name и email обязательны"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверяем, что комната существует — иначе 404
        cursor.execute('SELECT id FROM rooms WHERE id = ?', (room_id,))
        if cursor.fetchone() is None:
            conn.close()
            return jsonify({"success": False,
                            "error": "Комната не найдена"}), 404

        try:
            cursor.execute(
                'INSERT INTO participants (room_id, name, email, wish) VALUES (?, ?, ?, ?)',
                (room_id, name, email, wish)
            )
            conn.commit()
            new_id = cursor.lastrowid
            return jsonify({
                "success": True,
                "data": {"id": new_id, "room_id": room_id, "name": name, "email": email},
                "message": "Участник добавлен"
            }), 201
        except sqlite3.IntegrityError:
            # Сюда попадаем, если нарушен UNIQUE (room_id, email)
            return jsonify({"success": False,
                            "error": "Участник с таким email уже есть в этой комнате"}), 409
        finally:
            conn.close()

    @app.route('/api/rooms/<int:room_id>/users', methods=['GET'])
    def get_participants(room_id):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM rooms WHERE id = ?', (room_id,))
        if cursor.fetchone() is None:
            conn.close()
            return jsonify({"success": False,
                            "error": "Комната не найдена"}), 404

        cursor.execute('SELECT * FROM participants WHERE room_id = ? ORDER BY id', (room_id,))
        rows = cursor.fetchall()
        conn.close()

        participants = [dict(row) for row in rows]
        return jsonify({"success": True, "data": participants})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)
