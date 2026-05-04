from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User


class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = (
        ('grade', _('Новая оценка')),
        ('homework', _('Новое домашнее задание')),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'notifications'

    def __str__(self):
        return f'{self.user.username} - {self.title}'