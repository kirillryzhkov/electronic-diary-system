# academic/models.py
from django.conf import settings
from django.db import models

from subjects.models import Subject


class StudyGroup(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Название группы'
    )

    curator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'teacher'},
        related_name='curated_groups',
        verbose_name='Куратор группы'
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание'
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'study_groups'
        verbose_name = 'Учебная группа'
        verbose_name_plural = 'Учебные группы'
        ordering = ['name']


class Classroom(models.Model):
    number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Номер кабинета'
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Описание'
    )

    def __str__(self):
        return self.number

    class Meta:
        db_table = 'classrooms'
        verbose_name = 'Кабинет'
        verbose_name_plural = 'Кабинеты'
        ordering = ['number']


class TeachingAssignment(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'},
        related_name='teaching_assignments',
        verbose_name='Преподаватель'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='teaching_assignments',
        verbose_name='Предмет'
    )

    group = models.ForeignKey(
        StudyGroup,
        on_delete=models.CASCADE,
        related_name='teaching_assignments',
        verbose_name='Группа'
    )

    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_assignments',
        verbose_name='Кабинет'
    )

    def __str__(self):
        return f'{self.teacher.username} — {self.subject.name} — {self.group.name}'

    class Meta:
        db_table = 'teaching_assignments'
        verbose_name = 'Назначение преподавателя'
        verbose_name_plural = 'Назначения преподавателей'
        ordering = ['group__name', 'subject__name']
        constraints = [
            models.UniqueConstraint(
                fields=['teacher', 'subject', 'group'],
                name='unique_teacher_subject_group'
            )
        ]