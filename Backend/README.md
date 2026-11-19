# Secret-Santa

Backend приложения «Тайный Санта» (Flask + SQLite).

- Документация API: [API.md](API.md)
- Запуск сервера: `python app.py`
- Тесты API (нужен запущенный сервер): `python test_api.py`
- Инициализация базы отдельно: `python db.py`

После жеребьёвки письма участникам выводятся в консоль сервера
(`notifications.py`): `Отправлено письмо для <email>: ваш подопечный <name>`.
Чтобы подключить реальный SMTP, достаточно изменить функцию `send_email`.

Служебный доступ супер-админа: `POST /api/superadmin/login` (пароль `admin123`)
выдаёт фейковый токен для `GET /api/superadmin/rooms` и
`GET /api/superadmin/rooms/<id>/results`.
