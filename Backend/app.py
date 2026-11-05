from flask import Flask, jsonify, request
from flask_cors import CORS
from db import (init_db, create_room, get_room, add_participant,
                get_participants, RoomNotFoundError, DuplicateError)

app = Flask(__name__)
CORS(app)


def error_response(message, status):
    return jsonify({"success": False, "error": message}), status


@app.route('/')
def home():
    return "Backend is working!"



@app.route('/api/rooms', methods=['POST'])
def create_room_endpoint():
    data = request.get_json() or {}
    title = data.get('title')

    if not title:
        return error_response("Поле title обязательно", 400)

    try:
        room = create_room(title)
        return jsonify({
            "success": True,
            "data": room,
            "message": "Комната создана"
        }), 201
    except DuplicateError:
        return error_response(
            "Конфликт уникального кода (попробуйте создать комнату ещё раз)", 409)
    except Exception as e:
        return error_response("Внутренняя ошибка", 500)


@app.route('/api/rooms/<int:room_id>', methods=['GET'])
def get_room_endpoint(room_id):
    try:
        room = get_room(room_id)
        return jsonify({"success": True, "data": room})
    except RoomNotFoundError:
        return error_response("Комната не найдена", 404)
    except Exception:
        return error_response("Внутренняя ошибка", 500)


@app.route('/api/rooms/<int:room_id>/users', methods=['POST'])
def add_participant_endpoint(room_id):
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    wish = data.get('wish')

    if not name or not email:
        return error_response("Поля name и email обязательны", 400)

    try:
        participant = add_participant(room_id, name, email, wish)
        return jsonify({
            "success": True,
            "data": participant,
            "message": "Участник добавлен"
        }), 201
    except RoomNotFoundError:
        return error_response("Комната не найдена", 404)
    except DuplicateError as e:
        return error_response(str(e), 409)
    except Exception:
        return error_response("Внутренняя ошибка", 500)


@app.route('/api/rooms/<int:room_id>/users', methods=['GET'])
def get_participants_endpoint(room_id):
    try:
        participants = get_participants(room_id)
        return jsonify({"success": True, "data": participants})
    except RoomNotFoundError:
        return error_response("Комната не найдена", 404)
    except Exception:
        return error_response("Внутренняя ошибка", 500)


if __name__ == '__main__':
    init_db()
    app.run(debug=True, use_reloader=False, port=5000)
