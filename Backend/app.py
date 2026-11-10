import traceback

from flask import Flask, jsonify, request
from flask_cors import CORS

from db import (init_db, create_room, get_room, add_participant,
                get_participants, perform_shuffle, get_assignments,
                RoomNotFoundError, DuplicateError, PermissionError)

app = Flask(__name__)
CORS(app)

# Бизнес-смысл: это бэкенд приложения «Тайный Санта».
# Пользователь создаёт комнату, приглашённые участники присоединяются к ней,
# и каждому участнику потом назначается получатель подарка.
#
# init_db() вызывается при ИМПОРТЕ модуля, а не только в __main__.
# Благодаря CREATE TABLE IF NOT EXISTS повторный вызов безопасен.
# Плюс: тесты (и любой другой запуск сервера) получают готовую базу
# без необходимости лезть в код — принцип чёрного ящика.
init_db()


def error_response(message, status):
    """Единый формат ошибок для всего API: {'success': False, 'error': текст}.
    Фронтенд всегда знает, где искать текст ошибки, — единый контракт."""
    return jsonify({"success": False, "error": message}), status


@app.route('/')
def home():
    """Проверка живости сервера (health-check): фронт или разработчик
    могут убедиться, что бэкенд запущен, не трогая базу данных."""
    try:
        return "Backend is working!"
    except Exception:
        # Сюда теоретически попасть сложно, но по единому стандарту
        # каждый эндпоинт должен уметь отчитаться об ошибке в консоль
        traceback.print_exc()
        return error_response("Внутренняя ошибка", 500)


# ---------- Комнаты ----------
# Бизнес-логика: комната — это «сессия Тайного Санты». У неё есть название
# для людей и уникальный код (room_code), по которому участники найдут её.

@app.route('/api/rooms', methods=['POST'])
def create_room_endpoint():
    """Создание комнаты. Аналог кнопки «Создать комнату» в интерфейсе."""
    data = request.get_json() or {}
    title = data.get('title')
    show_pairs = data.get('show_pairs', False)

    # Быстрая проверка на уровне эндпоинта: отсекаем явный мусор до похода в базу,
    # чтобы не тратить ресурсы на заведомо невалидный запрос
    if not isinstance(title, str) or not title.strip():
        return error_response("Название комнаты обязательно и не может быть пустым", 400)
    if not isinstance(show_pairs, bool):
        return error_response("Поле show_pairs должно быть булевым (true/false)", 400)

    try:
        room = create_room(title, show_pairs)
        # 201 Created — REST-конвенция: «ресурс успешно создан»
        return jsonify({
            "success": True,
            "data": room,
            "message": "Комната создана"
        }), 201
    except ValueError as e:      # ошибка валидации -> 400 Bad Request
        return error_response(str(e), 400)
    except DuplicateError:       # конфликт уникальности -> 409 Conflict
        # Случай, когда сгенерированный код совпал с существующей комнатой
        return error_response(
            "Конфликт уникального кода (попробуйте создать комнату ещё раз)", 409)
    except Exception:
        # ВАЖНО: логируем ошибку, а не глотаем её.
        # Пользователь видит нейтральное сообщение, а разработчик — traceback в консоли
        traceback.print_exc()
        return error_response("Внутренняя ошибка", 500)


@app.route('/api/rooms/<int:room_id>', methods=['GET'])
def get_room_endpoint(room_id):
    """Получение информации о комнате по её id.
    Используется, когда участник открыл комнату и нужно показать её название/код."""
    try:
        room = get_room(room_id)
        return jsonify({"success": True, "data": room})
    except RoomNotFoundError:    # 404, а не 500 — это ожидаемая ситуация,
        return error_response("Комната не найдена", 404)   # а не поломка сервера
    except Exception:
        traceback.print_exc()
        return error_response("Внутренняя ошибка", 500)


# ---------- Участники ----------
# Бизнес-логика: участник — человек, присоединившийся к комнате. Он указывает
# имя, email (идентификатор — один email = один вход в комнату) и пожелание
# к подарку, которое увидит его Тайный Санта.

@app.route('/api/rooms/<int:room_id>/users', methods=['POST'])
def add_participant_endpoint(room_id):
    """Регистрация участника в комнате — аналог формы «Присоединиться»."""
    data = request.get_json() or {}
    name = data.get('name')
    email = data.get('email')
    wish = data.get('wish')

    # Валидация на уровне эндпоинта (дублирует db.py — это нормально:
    # эндпоинт отсеивает мусор до похода в базу, db.py — последняя инстанция)
    if not isinstance(name, str) or not name.strip():
        return error_response("Поле name обязательно и не может быть пустым", 400)
    if not isinstance(email, str) or '@' not in email or '.' not in email.split('@', 1)[1]:
        return error_response("Укажите корректный email", 400)

    try:
        participant = add_participant(room_id, name, email, wish)
        return jsonify({
            "success": True,
            "data": participant,
            "message": "Участник добавлен"
        }), 201
    except ValueError as e:          # невалидные данные -> 400
        return error_response(str(e), 400)
    except RoomNotFoundError:        # человек присоединяется к несуществующей комнате
        return error_response("Комната не найдена", 404)
    except DuplicateError as e:      # этот email уже участвует в комнате -> 409
        return error_response(str(e), 409)
    except Exception:
        traceback.print_exc()
        return error_response("Внутренняя ошибка", 500)


@app.route('/api/rooms/<int:room_id>/users', methods=['GET'])
def get_participants_endpoint(room_id):
    """Список участников комнаты — экран «Кто уже в игре».
    Нужен организатору, чтобы видеть, сколько человек присоединилось."""
    try:
        participants = get_participants(room_id)
        return jsonify({"success": True, "data": participants})
    except RoomNotFoundError:
        return error_response("Комната не найдена", 404)
    except Exception:
        traceback.print_exc()
        return error_response("Внутренняя ошибка", 500)


# ---------- Жеребьёвка ----------
# Бизнес-логика: жеребьёвка проводится один раз по кнопке организатора.
# После неё каждый участник — Тайный Санта ровно одного человека.
# Повторное перемешивание запрещено, чтобы не ломать уже разосланные роли.

@app.route('/api/rooms/<int:room_id>/shuffle', methods=['POST'])
def shuffle_endpoint(room_id):
    """Проведение жеребьёвки — аналог кнопки «Провести жеребьёвку».
    Пары в ответе НЕ отдаём: они секретны. Ведущий может посмотреть
    их отдельным запросом, только если включена галочка show_pairs."""
    try:
        count = perform_shuffle(room_id)
        return jsonify({
            "success": True,
            "message": "Жеребьёвка проведена",
            "pairs_count": count
        })
    except RoomNotFoundError:        # жеребьёвка в несуществующей комнате
        return error_response("Комната не найдена", 404)
    except DuplicateError:           # повторная жеребьёвка -> 409 Conflict
        return error_response("Жеребьёвка уже была проведена — перемешивать нельзя", 409)
    except ValueError as e:          # меньше 3 участников -> 400
        return error_response(str(e), 400)
    except Exception:
        traceback.print_exc()
        return error_response("Внутренняя ошибка", 500)


@app.route('/api/rooms/<int:room_id>/assignments', methods=['GET'])
def get_assignments_endpoint(room_id):
    """Список всех пар комнаты для ведущего. Доступен только если
    при создании комнаты была включена галочка «показывать пары ведущему»."""
    try:
        assignments = get_assignments(room_id)
        return jsonify({"success": True, "data": assignments})
    except RoomNotFoundError:
        return error_response("Комната не найдена", 404)
    except PermissionError as e:     # галочка выключена -> 403 Forbidden
        return error_response(str(e), 403)
    except ValueError as e:          # жеребьёвка ещё не проводилась -> 400
        return error_response(str(e), 400)
    except Exception:
        traceback.print_exc()
        return error_response("Внутренняя ошибка", 500)


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)
