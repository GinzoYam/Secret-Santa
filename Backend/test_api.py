# -*- coding: utf-8 -*-
"""Тесты API «Тайный Санта» через реальные HTTP-запросы.

Требуется запущенный сервер: python app.py
Запуск тестов: python test_api.py

Защита данных:
Перед прогоном тестов рабочая база (santa.db) копируется в резервный файл
(santa.db.backup). Тесты создают комнаты и участников в реальной базе,
а после прогона база восстанавливается из резервной копии — данные
пользователя не страдают. Если базы до тестов не было, она удаляется
(сервер создаст её заново при следующем запуске).

Для каждого запроса выводится: метод, URL, параметры запроса
и полученный ответ (код + тело).
"""
import json
import os
import shutil
import sqlite3
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import db

BASE_URL = 'http://127.0.0.1:5000'

DB_FILE = db.DB_NAME            # рабочая база (та же, что использует сервер)
DB_BACKUP = DB_FILE + '.backup'  # резервная копия рабочей базы

passed = 0
failed = 0


def backup_db():
    """Копирует рабочую базу в резервный файл перед тестами.
    Если базы ещё нет — просто сообщаем: после тестов её удалим."""
    if os.path.exists(DB_FILE):
        shutil.copyfile(DB_FILE, DB_BACKUP)
        print(f'База скопирована: {DB_FILE} -> {DB_BACKUP}')
    else:
        print(f'База {DB_FILE} не найдена — восстановление не потребуется')


def restore_db():
    """Возвращает базу в состояние до тестов.

    Важный нюанс Windows: пока сервер запущен, файл базы ОТКРЫТ и его нельзя
    удалить (WinError 32), но можно ПЕРЕЗАПИСАТЬ содержимое. Поэтому:
    - база существовала  -> копируем содержимое резервной копии поверх santa.db
      (файл остаётся тот же, но данные — «до тестов»);
    - базы не было       -> очищаем тестовую базу через sqlite3 backup API
      (пустая база с той же схемой — сервер продолжит работать корректно).
    """
    try:
        if os.path.exists(DB_BACKUP) and os.path.exists(DB_FILE):
            # copyfile перезаписывает содержимое — работает даже при открытом файле
            _copy_with_retry(DB_BACKUP, DB_FILE)
            os.remove(DB_BACKUP)
            print(f'\nБаза восстановлена из {DB_BACKUP}: данные до тестов возвращены')
        elif os.path.exists(DB_BACKUP) and not os.path.exists(DB_FILE):
            shutil.copyfile(DB_BACKUP, DB_FILE)
            os.remove(DB_BACKUP)
            print(f'\nБаза восстановлена из {DB_BACKUP} (файл был создан заново)')
        elif os.path.exists(DB_FILE):
            # До тестов базы не было — оставляем пустую базу вместо удаления,
            # потому что удалить файл, открытый сервером, на Windows нельзя
            src = sqlite3.connect(':memory:')  # пустая база в памяти
            dst = sqlite3.connect(DB_FILE)
            src.backup(dst)
            src.close()
            dst.close()
            print(f'\nТестовая база {DB_FILE} очищена (до тестов её не было)')
    except (OSError, sqlite3.Error) as e:
        print(f'\nВНИМАНИЕ: не удалось восстановить базу — {e}')
        print(f'Резервная копия осталась в файле: {DB_BACKUP}')


def _copy_with_retry(src, dst, attempts=3, delay=1.0):
    """copyfile с повторными попытками: файл может быть кратковременно занят
    сервером (выполняется запрос) — пауза между попытками это лечит."""
    for attempt in range(1, attempts + 1):
        try:
            shutil.copyfile(src, dst)
            return
        except PermissionError:
            if attempt == attempts:
                raise  # все попытки исчерпаны — отдадим ошибку вызывающему
            print(f'  (попытка {attempt}: файл занят, жду {delay} сек...)')
            time.sleep(delay)


def format_body(resp):
    """Форматирует тело ответа: JSON — красиво, иначе — как есть."""
    try:
        return json.dumps(resp.json(), ensure_ascii=False)
    except ValueError:
        return resp.text[:200]


def http(method, path, name, params=None, expected=None):
    """Выполняет HTTP-запрос и красиво печатает его и ответ.

    method  — 'GET' или 'POST'
    path    — путь, например '/api/rooms'
    name    — название теста для заголовка
    params  — тело запроса (для POST) или None
    expected — ожидаемый код ответа (None — не проверять)
    Возвращает объект requests.Response.
    """
    url = f'{BASE_URL}{path}'
    print(f'\n--- {name}')
    print(f'Запрос: {method} {path}')
    if params is not None:
        print(f'Параметры запроса: {json.dumps(params, ensure_ascii=False)}')

    resp = requests.request(method, url, json=params)

    print(f'Ответ: {resp.status_code} {format_body(resp)}')

    if expected is not None:
        assert resp.status_code == expected, \
            f'Ожидался код {expected}, получен {resp.status_code}'

    return resp


def json_of(resp):
    """Возвращает JSON-тело ответа или None, если тело не JSON."""
    try:
        return resp.json()
    except ValueError:
        return None


def run(name, func):
    """Запускает тест и учитывает результат (OK/FAIL)."""
    global passed, failed
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


def main():
    # Проверяем, что сервер запущен — без него тестировать нечего
    try:
        requests.get(f'{BASE_URL}/', timeout=3)
    except requests.ConnectionError:
        print('ОШИБКА: сервер не запущен. Сначала выполните: python app.py')
        sys.exit(1)

    backup_db()  # сохраняем данные пользователя до того, как тесты их изменят

    try:
        db.init_db()  # база должна существовать (пустая, если только что создана)
        run_tests()
    finally:
        # Восстанавливаем базу даже если тесты упали с исключением —
        # данные пользователя важнее отчёта о тестах
        restore_db()

    print(f'\n{"=" * 50}')
    print(f'Итог: пройдено {passed}, провалено {failed}, всего {passed + failed}')
    print(f'{"=" * 50}')
    sys.exit(1 if failed else 0)


def run_tests():
    """Все тесты API. Данные после этих тестов будут откачены restore_db()."""

    # ── GET / ──

    def test_home():
        resp = http('GET', '/', 'Проверка главной страницы', expected=200)
        assert 'Backend is working' in resp.text, 'Неожиданный ответ'

    run('Главная страница отвечает', test_home)

    # ── POST /api/rooms ──

    def test_create_room_success():
        data = json_of(http('POST', '/api/rooms', 'Создание комнаты',
                            params={'title': 'Party'}, expected=201))
        assert data['success'] is True
        assert data['data']['title'] == 'Party'
        assert len(data['data']['room_code']) == 6, 'Код комнаты должен быть 6 символов'
        assert data['data'].get('admin_code'), \
            'Код организатора должен возвращаться при создании комнаты'
        assert data['message'] == 'Комната создана'

    run('Создание комнаты', test_create_room_success)

    def test_create_room_without_title():
        data = json_of(http('POST', '/api/rooms', 'Создание комнаты без title',
                            params={}, expected=400))
        assert data['success'] is False
        assert 'Название' in data['error'], \
            f'В ошибке должно быть сказано про название: {data["error"]}'

    run('Создание комнаты без title даёт 400', test_create_room_without_title)

    def test_create_room_no_json():
        # Flask отвечает 415, если Content-Type не application/json
        resp = http('POST', '/api/rooms', 'Создание комнаты без JSON-тела')
        assert resp.status_code in (400, 415), \
            f'Ожидался код 400 или 415, получен {resp.status_code}'
    run('Создание комнаты без JSON-тела даёт 400/415', test_create_room_no_json)

    # ── Подготовка: комната для дальнейших тестов ──

    room = json_of(http('POST', '/api/rooms', 'Подготовка: тестовая комната',
                        params={'title': 'Test Room'}, expected=201))['data']
    room_id, room_code = room['id'], room['room_code']
    admin_code = room['admin_code']

    # ── GET /api/rooms/<id> ──

    def test_get_room_success():
        data = json_of(http('GET', f'/api/rooms/{room_id}', 'Получение комнаты по id',
                            expected=200))
        assert data['data']['id'] == room_id
        assert data['data']['room_code'] == room_code
        assert 'admin_code' not in data['data'], \
            'Секретный код организатора не должен утекать через публичный GET'

    run('Получение комнаты по id', test_get_room_success)

    def test_get_room_not_found():
        data = json_of(http('GET', '/api/rooms/999999', 'Получение несуществующей комнаты',
                            expected=404))
        assert data['success'] is False

    run('Получение несуществующей комнаты даёт 404', test_get_room_not_found)

    # ── POST /api/rooms/<id>/users ──

    def test_add_participant_success():
        data = json_of(http('POST', f'/api/rooms/{room_id}/users', 'Добавление участника',
                            params={'name': 'Alice', 'email': 'alice@test.com',
                                    'wish': 'book'},
                            expected=201))
        assert data['data']['name'] == 'Alice'
        assert data['data']['room_id'] == room_id
        assert data['message'] == 'Участник добавлен'

    run('Добавление участника', test_add_participant_success)

    def test_add_participant_missing_fields():
        data = json_of(http('POST', f'/api/rooms/{room_id}/users',
                            'Добавление участника без email',
                            params={'name': 'Bob'}, expected=400))
        assert 'email' in data['error'], \
            f'В ошибке должно быть сказано про email: {data["error"]}'

    run('Добавление участника без email даёт 400', test_add_participant_missing_fields)

    def test_add_participant_room_not_found():
        http('POST', '/api/rooms/999999/users',
             'Добавление участника в несуществующую комнату',
             params={'name': 'Bob', 'email': 'bob@test.com'}, expected=404)

    run('Добавление участника в несуществующую комнату даёт 404',
        test_add_participant_room_not_found)

    def test_add_participant_duplicate_email():
        data = json_of(http('POST', f'/api/rooms/{room_id}/users',
                            'Повторный email в одной комнате',
                            params={'name': 'Alice', 'email': 'alice@test.com'},
                            expected=409))
        assert 'email' in data['error']

    run('Повторный email в одной комнате даёт 409', test_add_participant_duplicate_email)

    def test_add_participant_same_email_different_room():
        other = json_of(http('POST', '/api/rooms', 'Подготовка: вторая комната',
                             params={'title': 'Another Room'}, expected=201))['data']
        data = json_of(http('POST', f"/api/rooms/{other['id']}/users",
                            'Тот же email в другой комнате',
                            params={'name': 'Alice', 'email': 'alice@test.com'},
                            expected=201))
        assert data['success'] is True

    run('Тот же email в другой комнате допустим',
        test_add_participant_same_email_different_room)

    # ── GET /api/rooms/<id>/users ──

    def test_get_participants_success():
        data = json_of(http('GET', f'/api/rooms/{room_id}/users',
                            'Получение списка участников', expected=200))
        assert data['success'] is True
        assert len(data['data']) >= 1
        assert data['data'][0]['name'] == 'Alice'

    run('Получение списка участников', test_get_participants_success)

    def test_get_participants_room_not_found():
        http('GET', '/api/rooms/999999/users',
             'Список участников несуществующей комнаты', expected=404)

    run('Список участников несуществующей комнаты даёт 404',
        test_get_participants_room_not_found)

    def test_get_participants_empty():
        empty = json_of(http('POST', '/api/rooms', 'Подготовка: пустая комната',
                             params={'title': 'Empty Room'}, expected=201))['data']
        data = json_of(http('GET', f"/api/rooms/{empty['id']}/users",
                            'Список участников пустой комнаты', expected=200))
        assert data['data'] == [], f'Ожидался пустой список, получено: {data["data"]}'

    run('Пустая комната возвращает пустой список участников',
        test_get_participants_empty)

    # ── Результаты для организатора (галочка) ──

    org_room = json_of(http('POST', '/api/rooms', 'Подготовка: комната организатора',
                            params={'title': 'Organizer Room'}, expected=201))['data']
    org_room_id = org_room['id']
    org_admin_code = org_room['admin_code']

    for p_name, p_email in (('Ann', 'ann@test.com'),
                            ('Ben', 'ben@test.com'),
                            ('Cid', 'cid@test.com')):
        http('POST', f'/api/rooms/{org_room_id}/users',
             f'Подготовка: участник {p_name}',
             params={'name': p_name, 'email': p_email}, expected=201)

    def test_results_hidden_without_checkbox():
        http('POST', f'/api/rooms/{org_room_id}/shuffle',
             'Подготовка: жеребьёвка комнаты организатора', expected=200)
        data = json_of(http('POST', f'/api/rooms/{org_room_id}/results',
                            'Результаты без галочки',
                            params={'admin_code': org_admin_code}, expected=403))
        assert data['success'] is False

    run('Без галочки организатор не видит результаты',
        test_results_hidden_without_checkbox)

    def test_results_wrong_admin_code():
        http('POST', f'/api/rooms/{org_room_id}/results',
             'Результаты с чужим кодом организатора',
             params={'admin_code': 'wrong-code'}, expected=403)
        http('PUT', f'/api/rooms/{org_room_id}/results/settings',
             'Галочка с чужим кодом организатора',
             params={'admin_code': 'wrong-code', 'show_results': True}, expected=403)

    run('Чужой код организатора даёт 403', test_results_wrong_admin_code)

    def test_toggle_results_settings():
        data = json_of(http('PUT', f'/api/rooms/{org_room_id}/results/settings',
                            'Поставить галочку показа результатов',
                            params={'admin_code': org_admin_code,
                                    'show_results': True}, expected=200))
        assert data['data']['show_results'] is True

    run('Организатор может поставить галочку', test_toggle_results_settings)

    def test_results_with_checkbox():
        data = json_of(http('POST', f'/api/rooms/{org_room_id}/results',
                            'Результаты при поставленной галочке',
                            params={'admin_code': org_admin_code}, expected=200))
        pairs = data['data']
        assert len(pairs) == 3, f'Ожидалось 3 пары, получено: {len(pairs)}'
        givers = {p['giver'] for p in pairs}
        assert givers == {'Ann', 'Ben', 'Cid'}
        assert all(p['giver'] != p['receiver'] for p in pairs), \
            'Никто не должен дарить сам себе'

    run('С галочкой организатор видит все пары', test_results_with_checkbox)

    def test_uncheck_results_settings():
        json_of(http('PUT', f'/api/rooms/{org_room_id}/results/settings',
                     'Снять галочку показа результатов',
                     params={'admin_code': org_admin_code,
                             'show_results': False}, expected=200))
        http('POST', f'/api/rooms/{org_room_id}/results',
             'Результаты после снятия галочки',
             params={'admin_code': org_admin_code}, expected=403)

    run('После снятия галочки результаты снова скрыты',
        test_uncheck_results_settings)


if __name__ == '__main__':
    main()
