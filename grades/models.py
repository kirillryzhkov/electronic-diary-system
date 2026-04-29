from calendar import month_name

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models import User
from subjects.models import Subject


class Grade(models.Model):
    GRADE_TYPE_CHOICES = (
        ('current', _('Текущая оценка')),
        ('monthly', _('Месячная аттестация')),
        ('semester', _('Полугодовая сессия')),
        ('exam', _('Экзамен')),
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_grades',
        null=True,
        blank=True
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='grades'
    )
    value = models.IntegerField()
    comment = models.TextField(blank=True, null=True)

    grade_type = models.CharField(
        max_length=20,
        choices=GRADE_TYPE_CHOICES,
        default='current',
        verbose_name='Тип оценки'
    )

    month = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name='Месяц аттестации'
    )

    semester = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name='Полугодие'
    )

    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время выставления'
    )

    def clean(self):
        if self.value < 1 or self.value > 5:
            raise ValidationError('Оценка должна быть от 1 до 5.')

        if self.grade_type == 'monthly' and not self.month:
            raise ValidationError('Для месячной аттестации нужно указать месяц.')

        if self.grade_type in ['semester', 'exam'] and not self.semester:
            raise ValidationError('Для сессии и экзамена нужно указать полугодие.')

        if self.month and (self.month < 1 or self.month > 12):
            raise ValidationError('Месяц должен быть от 1 до 12.')

        if self.semester and self.semester not in [1, 2]:
            raise ValidationError('Полугодие должно быть 1 или 2.')

    @property
    def period_label(self):
        if self.grade_type == 'monthly' and self.month:
            months_ru = {
                1: 'Январь',
                2: 'Февраль',
                3: 'Март',
                4: 'Апрель',
                5: 'Май',
                6: 'Июнь',
                7: 'Июль',
                8: 'Август',
                9: 'Сентябрь',
                10: 'Октябрь',
                11: 'Ноябрь',
                12: 'Декабрь',
            }
            return months_ru.get(self.month, '—')

        if self.grade_type in ['semester', 'exam'] and self.semester:
            return f'{self.semester} полугодие'

        return '—'

    def __str__(self):
        return f"{self.student.username} - {self.subject.name}: {self.value}"

    class Meta:
        db_table = "grades"
        ordering = ['-date']