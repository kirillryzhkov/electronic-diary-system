# grades/models.py
from django.db import models
from users.models import User
from subjects.models import Subject


class Grade(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name='Ученик'
    )

    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='given_grades',
        limit_choices_to={'role': 'teacher'},
        verbose_name='Преподаватель'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='grades',
        verbose_name='Предмет'
    )

    value = models.IntegerField(verbose_name='Оценка')

    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Пояснение к оценке'
    )

    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время выставления'
    )

    def __str__(self):
        teacher_name = self.teacher.username if self.teacher else 'Без преподавателя'
        return f"{self.student.username} - {self.subject.name}: {self.value} ({teacher_name})"

    class Meta:
        db_table = "grades"
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        ordering = ["-date"]