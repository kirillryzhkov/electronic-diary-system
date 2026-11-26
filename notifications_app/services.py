import json
import logging
from functools import partial
from http.client import HTTPException
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction

from .models import Notification


logger = logging.getLogger(__name__)


def send_telegram_message(chat_id, text):
    """Try Telegram delivery without logging the token, chat ID or response."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or not chat_id:
        return False

    request = Request(
        f'https://api.telegram.org/bot{quote(token, safe=":")}/sendMessage',
        data=json.dumps({'chat_id': chat_id, 'text': text}).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urlopen(request, timeout=3) as response:
            result = json.loads(response.read(65536))
            return isinstance(result, dict) and result.get('ok') is True
    except (OSError, ValueError, HTTPException):
        logger.warning('Telegram notification delivery failed.')
        return False


def notify_user(user, notification_type, title, message):
    """Store the notice and send a private-data-free Telegram alert after commit."""
    notification = Notification.objects.create(
        user=user, notification_type=notification_type, title=title, message=message
    )
    if settings.TELEGRAM_BOT_TOKEN and user.telegram_notifications_enabled and user.telegram_chat_id:
        # The chat ID is self-entered. Keep student details inside the diary.
        text = f'{title}. Подробности в электронном дневнике.'
        transaction.on_commit(partial(send_telegram_message, user.telegram_chat_id, text))
    return notification
