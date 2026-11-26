import json
from urllib.error import URLError
from unittest.mock import patch

from django.db import transaction
from django.test import TestCase, override_settings

from notifications_app.models import Notification
from notifications_app.services import notify_user, send_telegram_message
from users.models import User


@override_settings(TELEGRAM_BOT_TOKEN='test-token')
class TelegramDeliveryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='student', telegram_chat_id='123456', telegram_notifications_enabled=True,
        )

    @patch('notifications_app.services.urlopen')
    def test_delivers_after_commit_and_keeps_private_details_in_the_database(self, open_url):
        open_url.return_value.__enter__.return_value.read.return_value = b'{"ok": true}'
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            notice = notify_user(self.user, 'grade', 'Новая оценка', 'Информатика: 4.')
            open_url.assert_not_called()
            self.assertEqual(notice.message, 'Информатика: 4.')
        self.assertEqual(len(callbacks), 1)
        request = open_url.call_args.args[0]
        self.assertEqual(request.host, 'api.telegram.org')
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(open_url.call_args.kwargs['timeout'], 3)
        self.assertEqual(json.loads(request.data), {
            'chat_id': '123456',
            'text': 'Новая оценка. Подробности в электронном дневнике.',
        })

    @patch('notifications_app.services.urlopen', side_effect=URLError('unreachable'))
    def test_network_error_keeps_database_notification(self, open_url):
        with self.assertLogs('notifications_app.services', level='WARNING') as logs:
            with self.captureOnCommitCallbacks(execute=True):
                notify_user(self.user, 'attendance', 'Отмечен пропуск', 'Подробности')
        self.assertNotIn('unreachable', '\n'.join(logs.output))
        self.assertEqual(Notification.objects.get().notification_type, 'attendance')
        open_url.assert_called_once()

    @patch('notifications_app.services.urlopen')
    def test_rollbacks_and_disabled_delivery_do_not_send(self, open_url):
        with self.captureOnCommitCallbacks(execute=True):
            with transaction.atomic():
                notify_user(self.user, 'grade', 'Оценка', 'Подробности')
                transaction.set_rollback(True)
        self.assertFalse(Notification.objects.exists())
        self.user.telegram_notifications_enabled = False
        with self.captureOnCommitCallbacks(execute=True):
            notify_user(self.user, 'grade', 'Оценка', 'Подробности')
            self.user.telegram_notifications_enabled = True
            with override_settings(TELEGRAM_BOT_TOKEN=''):
                notify_user(self.user, 'grade', 'Оценка', 'Подробности')
        self.assertEqual(Notification.objects.count(), 2)
        open_url.assert_not_called()

    @patch('notifications_app.services.urlopen')
    def test_telegram_response_must_confirm_delivery(self, open_url):
        open_url.return_value.__enter__.return_value.read.return_value = b'{"ok": false}'
        self.assertFalse(send_telegram_message('123456', 'Тест'))
