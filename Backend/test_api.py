# -*- coding: utf-8 -*-
"""Тесты API «Тайный Санта» через реальные HTTP-запросы.

Требуется запущенный сервер: python app.py
Запуск тестов: python test_api.py

При каждом запросе выводится: метод, URL, тело запроса,
код ответа и тело ответа.
"""
import json
import os
import sys
import tempfile

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db

BASE_URL = 'http://127.0.0.1:5000'


def check_response(resp, expected_status, name):
    """Проверяет код ответа и печатает запрос/ответ."""
    print(f'\n--- {name}')
    print(f'Ответ: {resp.status_code} {format_body(resp)}')
    assert resp.status_code == expected_status, \
        f'Ожидался код {expected_status}, получен {resp.status_code}'
    try:
        return resp.json()
    except ValueError:
        return None


def format_body(resp):
    """Форматирует тело ответа: JSON — красиво, иначе — как есть."""
    try:
        return json.dumps(resp.json(), ensure_ascii=False)
    except ValueError:
        return resp.text[:200]


def main():
    # Проверяем, что сервер запущен
    try:
        requests.get(f'{BASE_URL}/', timeout=3)
    except requests.ConnectionError:
        print('ОШИБКА: сервер не запущен. Сначала выполните: python app.py')
        sys.exit(1)

    db.init_db()
    passed = 0
    failed = 0

    def run(name, func):
        nonlocal passed, failed
        try:
            func()
            passed += 1
            print(f'[OK]   {name}')
        except AssertionError as e:
            failed += 1
            print(f'[FAIL] {name}: {e}')
        except Exception as e:
            failed += 1
            print(f'[FAIL] {name}: непредвиденная ошибка — {e}')

    # ── GET / ──

    def test_home():
        print('Запрос: GET /')
        resp = requests.get(f'{BASE_URL}/')
        data = check_response(resp, 200, 'GET /')
        assert 'Backend is working' in resp.text, f'Неожиданный ответ: {resp.text}'
    run('Главная страница отвечает', test_home)

    # ── POST /api/rooms ──

    def test_create_room_success():
        payload = {'title': 'Party'}
        print(f'Запрос: POST /api/rooms, тело: {payload}')
        resp = requests.post(f'{BASE_URL}/api/rooms', json=payload)
        data = check_response(resp, 201, 'POST /api/rooms (успех)')
        assert data['success'] is True
        assert data['data']['title'] == 'Party'
        assert len(data['data']['room_code']) == 6, 'Код комнаты должен быть 6 символов'
        assert data['message'] == 'Комната создана'

    run('Создание комнаты', test_create_room_success)

    def test_create_room_without_title():
        payload = {}
        print(f'Запрос: POST /api/rooms, тело: {payload}')
        resp = requests.post(f'{BASE_URL}/api/rooms', json=payload)
        data = check_response(resp, 400, 'POST /api/rooms (без title)')
        assert data['success'] is False
        assert 'title' in data['error']

    run('Создание комнаты без title даёт 400', test_create_room_without_title)

    def test_create_room_no_json():
        print('Запрос: POST /api/rooms, тело: отсутствует')
        resp = requests.post(f'{BASE_URL}/api/rooms')
        assert resp.status_code in (400, 415), \
            f'Ожидался код 400 или 415, получен {resp.status_code}'
        print(f'\n--- POST /api/rooms (без JSON-тела)')
        print(f'Ответ: {resp.status_code} {format_body(resp)}')
    run('Создание комнаты без JSON-тела даёт 400', test_create_room_no_json)

    # ── GET /api/rooms/<id> ──

    # Комната для тестов получения
    print('Запрос: POST /api/rooms, тело: {"title": "Test Room"} (подготовка)')
    resp = requests.post(f'{BASE_URL}/api/rooms', json={'title': 'Test Room'})
    room = resp.json()['data']
    room_id, room_code = room['id'], room['room_code']

    def test_get_room_success():
        print(f'Запрос: GET /api/rooms/{room_id}')
        resp = requests.get(f'{BASE_URL}/api/rooms/{room_id}')
        data = check_response(resp, 200, f'GET /api/rooms/{room_id}')
        assert data['data']['id'] == room_id
        assert data['data']['room_code'] == room_code

    run('Получение комнаты по id', test_get_room_success)

    def test_get_room_not_found():
        print('Запрос: GET /api/rooms/999999')
        resp = requests.get(f'{BASE_URL}/api/rooms/999999')
        data = check_response(resp, 404, 'GET /api/rooms/999999')
        assert data['success'] is False

    run('Получение несуществующей комнаты даёт 404', test_get_room_not_found)

    # ── POST /api/rooms/<id>/users ──

    def test_add_participant_success():
        payload = {'name': 'Alice', 'email': 'alice@test.com', 'wish': 'book'}
        print(f'Запрос: POST /api/rooms/{room_id}/users, тело: {payload}')
        resp = requests.post(f'{BASE_URL}/api/rooms/{room_id}/users', json=payload)
        data = check_response(resp, 201, f'POST /api/rooms/{room_id}/users (успех)')
        assert data['data']['name'] == 'Alice'
        assert data['data']['room_id'] == room_id
        assert data['message'] == 'Участник добавлен'

    run('Добавление участника', test_add_participant_success)

    def test_add_participant_missing_fields():
        payload = {'name': 'Bob'}
        print(f'Запрос: POST /api/rooms/{room_id}/users, тело: {payload}')
        resp = requests.post(f'{BASE_URL}/api/rooms/{room_id}/users', json=payload)
        data = check_response(resp, 400, f'POST /api/rooms/{room_id}/users (без email)')
        assert 'name и email' in data['error']

    run('Добавление участника без email даёт 400', test_add_participant_missing_fields)

    def test_add_participant_room_not_found():
        payload = {'name': 'Bob', 'email': 'bob@test.com'}
        print(f'Запрос: POST /api/rooms/999999/users, тело: {payload}')
        resp = requests.post(f'{BASE_URL}/api/rooms/999999/users', json=payload)
        check_response(resp, 404, 'POST /api/rooms/999999/users')

    run('Добавление участника в несуществующую комнату даёт 404',
        test_add_participant_room_not_found)

    def test_add_participant_duplicate_email():
        payload = {'name': 'Alice', 'email': 'alice@test.com'}
        print(f'Запрос: POST /api/rooms/{room_id}/users, тело: {payload} (повторно)')
        resp = requests.post(f'{BASE_URL}/api/rooms/{room_id}/users', json=payload)
        data = check_response(resp, 409, f'POST /api/rooms/{room_id}/users (дубликат email)')
        assert 'email' in data['error']

    run('Повторный email в одной комнате даёт 409', test_add_participant_duplicate_email)

    def test_add_participant_same_email_different_room():
        print('Запрос: POST /api/rooms, тело: {"title": "Another Room"} (подготовка)')
        other = requests.post(f'{BASE_URL}/api/rooms', json={'title': 'Another Room'}).json()
        other_id = other['data']['id']
        payload = {'name': 'Alice', 'email': 'alice@test.com'}
        print(f'Запрос: POST /api/rooms/{other_id}/users, тело: {payload}')
        resp = requests.post(f'{BASE_URL}/api/rooms/{other_id}/users', json=payload)
        check_response(resp, 201, f'POST /api/rooms/{other_id}/users (email в другой комнате)')

    run('Тот же email в другой комнате допустим', test_add_participant_same_email_different_room)

    # ── GET /api/rooms/<id>/users ──

    def test_get_participants_success():
        print(f'Запрос: GET /api/rooms/{room_id}/users')
        resp = requests.get(f'{BASE_URL}/api/rooms/{room_id}/users')
        data = check_response(resp, 200, f'GET /api/rooms/{room_id}/users')
        assert data['success'] is True
        assert len(data['data']) >= 1
        assert data['data'][0]['name'] == 'Alice'

    run('Получение списка участников', test_get_participants_success)

    def test_get_participants_room_not_found():
        print('Запрос: GET /api/rooms/999999/users')
        resp = requests.get(f'{BASE_URL}/api/rooms/999999/users')
        check_response(resp, 404, 'GET /api/rooms/999999/users')

    run('Список участников несуществующей комнаты даёт 404',
        test_get_participants_room_not_found)

    def test_get_participants_empty():
        print('Запрос: POST /api/rooms, тело: {"title": "Empty Room"} (подготовка)')
        empty = requests.post(f'{BASE_URL}/api/rooms', json={'title': 'Empty Room'}).json()
        empty_id = empty['data']['id']
        print(f'Запрос: GET /api/rooms/{empty_id}/users')
        resp = requests.get(f'{BASE_URL}/api/rooms/{empty_id}/users')
        data = check_response(resp, 200, f'GET /api/rooms/{empty_id}/users (пустая комната)')
        assert data['data'] == [], f'Ожидался пустой список, получено: {data["data"]}'

    run('Пустая комната возвращает пустой список участников',
        test_get_participants_empty)

    # ── Итог ──

    print(f'\n{"=" * 50}')
    print(f'Итог: пройдено {passed}, провалено {failed}, всего {passed + failed}')
    print(f'{"=" * 50}')
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
