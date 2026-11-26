from datetime import time, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from academic.models import Attendance, Classroom, Homework, HomeworkSubmission, Schedule
from academic.models import StudyGroup, TeachingAssignment
from grades.models import Grade, GradeAuditLog
from subjects.models import Subject
from users.models import User


PASSWORD = 'password123'
STUDENTS = (
    ('Алихан', 'Нурланов', 0),
    ('Дамир', 'Сериков', 0),
    ('Аружан', 'Калиева', 1),
    ('Ерасыл', 'Тулегенов', 1),
    ('София', 'Ким', 0),
    ('Амина', 'Исабаева', 1),
    ('Арман', 'Омаров', 0),
    ('Диана', 'Ахметова', 1),
)
LESSONS = (
    (0, 'Математика', '204', (1, 3), 8, 'Квадратные уравнения', 'Реши пять уравнений.'),
    (0, 'Информатика', '305', (1, 4), 10, 'Основы баз данных', 'Напиши три SQL-запроса.'),
    (1, 'Физика', '210', (2, 5), 8, 'Законы Ньютона', 'Разбери примеры из учебника.'),
    (1, 'История', '112', (3,), 10, 'История Казахстана', 'Подготовь краткое сообщение.'),
    (1, 'Математика', '204', (1,), 10, 'Производные', 'Найди производные пяти функций.'),
)


def demo_user(username, role, first_name, last_name, group=None):
    email = f'{username}@example.com'
    user = User.objects.filter(username=username).first()
    if user:
        if (user.email, user.role, user.group_id) != (email, role, group.pk if group else None):
            raise CommandError(f'Логин {username} уже занят другим пользователем.')
        return user

    create = User.objects.create_superuser if role == 'admin' else User.objects.create_user
    return create(
        username=username, email=email, password=PASSWORD, role=role,
        first_name=first_name, last_name=last_name, group=group, is_staff=role != 'student',
    )


class Command(BaseCommand):
    help = 'Дополняет демо-данные на текущую неделю без удаления существующих записей'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        demo_user('admin', 'admin', 'Алексей', 'Администраторов')
        teachers = (
            demo_user('teacher', 'teacher', 'Иван', 'Петров'),
            demo_user('teacher2', 'teacher', 'Мария', 'Сидорова'),
        )
        groups = [
            StudyGroup.objects.get_or_create(name=name, defaults={'curator': teacher})[0]
            for name, teacher in zip(('ИС-31', 'ПО-22'), teachers)
        ]
        students = [
            demo_user(f'student{number}', 'student', first, last, groups[group_index])
            for number, (first, last, group_index) in enumerate(STUDENTS, 1)
        ]

        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday())
        homeworks = []
        for index, (group_index, subject_name, room, days, hour, title, description) in enumerate(LESSONS):
            subject, _ = Subject.objects.get_or_create(name=subject_name)
            classroom, _ = Classroom.objects.get_or_create(number=room)
            assignment, _ = TeachingAssignment.objects.get_or_create(
                teacher=teachers[group_index], subject=subject, group=groups[group_index],
                defaults={'classroom': classroom},
            )
            deadline = monday + timedelta(days=days[0] - 1)
            homework, _ = Homework.objects.get_or_create(
                assignment=assignment, title=title, deadline=deadline,
                defaults={'description': description},
            )
            homeworks.append(homework)
            for day in days:
                slot = {(1, 4): 12, (2, 2): 10, (3, 3): 12, (4, 1): 8}.get((index, day), hour)
                start_time, end_time, lesson_number = {
                    8: (time(8, 30), time(10), 1),
                    10: (time(10, 10), time(11, 40), 2),
                    12: (time(12, 10), time(13, 40), 3),
                }[slot]
                Schedule.objects.get_or_create(
                    assignment=assignment, day=day, start_time=start_time,
                    defaults={'end_time': end_time, 'lesson_number': lesson_number},
                )
                lesson_date = monday + timedelta(days=day - 1)
                for number, student in enumerate(students, 1):
                    if student.group_id == assignment.group_id:
                        self.seed_cell(assignment, student, number, index, lesson_date, deadline)

        reviews = (
            (0, 1, 'checked'), (0, 2, 'submitted'), (1, 5, 'returned'),
            (2, 3, 'checked'), (2, 4, 'submitted'), (3, 6, 'submitted'),
        )
        for index, number, status in reviews:
            homework = homeworks[index]
            student = students[number - 1]
            defaults = {'status': status, 'answer_text': 'Решение подготовлено, основные шаги описаны.'}
            if status == 'checked':
                grade = Grade.objects.get(
                    assignment=homework.assignment, student=student, lesson_date=homework.deadline,
                )
                if not HomeworkSubmission.objects.filter(grade=grade).exists():
                    defaults.update(grade=grade, grade_value=grade.value, teacher_comment=grade.comment)
                else:
                    defaults['grade_value'] = grade.value
                defaults['checked_at'] = timezone.now()
            elif status == 'returned':
                defaults.update(teacher_comment='Добавь объяснение к решению.', checked_at=timezone.now())
            HomeworkSubmission.objects.get_or_create(homework=homework, student=student, defaults=defaults)

        self.stdout.write(self.style.SUCCESS(f'Демо-данные на неделю с {monday:%d.%m.%Y} готовы.'))
        self.stdout.write('Логины: admin, teacher, teacher2, student1–student8. Пароль: password123.')

    def seed_cell(self, assignment, student, number, index, date, deadline):
        status = 'absent' if number >= 7 else 'present'
        if (number, index, date == deadline) in ((2, 0, True), (4, 2, True)):
            status = 'late' if number == 2 else 'excused'
        Attendance.objects.get_or_create(
            assignment=assignment, student=student, date=date, defaults={'status': status},
        )

        value = 2 + (index % 2) if number >= 7 else 4 + ((number + index) % 2)
        reason = {
            (0, 1): 'Учтено решение дополнительной задачи.',
            (1, 5): 'Проверен исправленный SQL-запрос.',
            (2, 3): 'Подтверждён балл за эксперимент.',
        }.get((index, number)) if date == deadline else None
        grade, created = Grade.objects.get_or_create(
            assignment=assignment, student=student, lesson_date=date,
            defaults={
                'teacher': assignment.teacher, 'subject': assignment.subject,
                'value': value - 1 if reason else value,
                'comment': 'Первичная проверка.' if reason else 'Работа на занятии.',
            },
        )
        if created and reason:
            comment = 'Оценка уточнена после проверки.'
            GradeAuditLog.objects.create(
                grade_id=grade.pk, assignment=assignment, changed_by=assignment.teacher,
                changed_by_name=assignment.teacher.full_name, old_value=grade.value,
                new_value=value, old_comment=grade.comment, new_comment=comment, reason=reason,
            )
            grade.value = value
            grade.comment = comment
            grade.save(update_fields=['value', 'comment', 'updated_at'])
