# academic/models.py
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
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

class Schedule(models.Model):
    DAY_CHOICES = (
        (1, _('Понедельник')),
        (2, _('Вторник')),
        (3, _('Среда')),
        (4, _('Четверг')),
        (5, _('Пятница')),
        (6, _('Суббота')),
    )

    assignment = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.CASCADE,
        related_name='schedule_items',
        verbose_name='Назначение преподавателя'
    )

    day = models.PositiveSmallIntegerField(
        choices=DAY_CHOICES,
        verbose_name='День недели'
    )

    start_time = models.TimeField(
        verbose_name='Время начала'
    )

    end_time = models.TimeField(
        verbose_name='Время окончания'
    )

    lesson_number = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name='Номер пары/урока'
    )

    def __str__(self):
        return (
            f'{self.get_day_display()} '
            f'{self.start_time}-{self.end_time} — '
            f'{self.assignment.subject.name} — '
            f'{self.assignment.group.name}'
        )

    class Meta:
        db_table = 'schedule'
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'
        ordering = ['day', 'start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['assignment', 'day', 'start_time'],
                name='unique_assignment_day_start_time'
            )
        ]

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', _('Присутствовал')),
        ('absent', _('Отсутствовал')),
        ('late', _('Опоздал')),
        ('excused', _('Уважительная причина')),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='attendance_records',
        verbose_name='Студент'
    )

    assignment = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name='Назначение'
    )

    date = models.DateField(
        verbose_name='Дата'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name='Статус'
    )

    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Комментарий'
    )

    def __str__(self):
        return f'{self.student.full_name} — {self.assignment.subject.name} — {self.get_status_display()}'

    class Meta:
        db_table = 'attendance'
        verbose_name = 'Посещаемость'
        verbose_name_plural = 'Посещаемость'
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'assignment', 'date'],
                name='unique_student_assignment_date_attendance'
            )
        ]

class Homework(models.Model):
    assignment = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.CASCADE,
        related_name='homeworks',
        verbose_name='Назначение'
    )

    title = models.CharField(
        max_length=200,
        verbose_name='Тема задания'
    )

    description = models.TextField(
        verbose_name='Описание задания'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    deadline = models.DateField(
        verbose_name='Срок сдачи'
    )

    def __str__(self):
        return f'{self.assignment.subject.name} — {self.title}'

    class Meta:
        db_table = 'homework'
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        ordering = ['-created_at']