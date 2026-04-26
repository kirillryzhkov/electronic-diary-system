# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('teacher', 'Учитель'),
        ('student', 'Ученик'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student',
        verbose_name='Роль'
    )

    group = models.ForeignKey(
        'academic.StudyGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name='Учебная группа'
    )

    @property
    def full_name(self):
        name = f'{self.last_name} {self.first_name}'.strip()
        return name if name else self.username

    def __str__(self):
        role = self.get_role_display()

        if self.role == 'student' and self.group:
            return f"{self.full_name} ({role}, {self.group.name})"

        return f"{self.full_name} ({role})"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']