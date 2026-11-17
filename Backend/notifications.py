"""Отправка уведомлений участникам «Тайного Санты».

Бизнес-смысл из ТЗ: после жеребьёвки каждому участнику приходит письмо
с именем его «подопечного» и пожеланиями к подарку.

Учебная реализация: вместо реального SMTP письмо пишется в лог сервера.
Чтобы подключить настоящую почту, достаточно заменить тело
send_email — остальной код (app.py, db.py) менять не придётся.
"""

import logging

from db import get_notifications

logger = logging.getLogger(__name__)


def send_email(email, receiver_name, receiver_wish):
    """«Отправляет» одно письмо участнику.

    В учебной версии — запись в лог сервера. Формат совпадает с ТЗ:
    'Отправлено письмо для <email>: ваш подопечный <name>'.
    Пожелание пишем отдельным сообщением, чтобы не ломать этот формат.
    """
    logger.info("Отправлено письмо для %s: ваш подопечный %s",
                email, receiver_name)
    if receiver_wish:
        logger.info("Пожелания для %s: %s", email, receiver_wish)


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
