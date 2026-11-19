"""Отправка уведомлений участникам «Тайного Санты».

Бизнес-смысл из ТЗ: после жеребьёвки каждому участнику приходит письмо
с именем его «подопечного» и пожеланиями к подарку.

Учебная реализация: вместо реального SMTP письмо выводится в консоль
сервера. Чтобы подключить настоящую почту, достаточно заменить тело
send_email — остальной код (app.py, db.py) менять не придётся.
"""

from db import get_notifications


def send_email(email, receiver_name, receiver_wish):
    """«Отправляет» одно письмо участнику.

    По ТЗ в учебной версии письмо выводится в консоль сервера. Формат
    совпадает с ТЗ: 'Отправлено письмо для <email>: ваш подопечный <name>'.
    Пожелание выводим отдельной строкой, чтобы не ломать этот формат.
    """
    print(f"Отправлено письмо для {email}: ваш подопечный {receiver_name}",
          flush=True)
    if receiver_wish:
        print(f"  Пожелания: {receiver_wish}", flush=True)


def notify_participants(room_id):
    """Рассылает письма всем участникам комнаты после жеребьёвки.

    Бросает RoomNotFoundError если комнаты нет,
    ShuffleNotDoneError если жеребьёвка ещё не проводилась.
    Возвращает количество отправленных писем.
    """
    notifications = get_notifications(room_id)
    for item in notifications:
        send_email(item['email'], item['receiver_name'], item['receiver_wish'])
    return len(notifications)
