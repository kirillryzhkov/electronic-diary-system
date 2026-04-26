from django.core.management.base import BaseCommand

from users.models import User
from subjects.models import Subject
from grades.models import Grade
from academic.models import StudyGroup, Classroom, TeachingAssignment, Schedule, Attendance, Homework
from datetime import time, date


class Command(BaseCommand):
    help = 'Создает демонстрационные данные для электронного дневника'

    def handle(self, *args, **kwargs):
        self.stdout.write('Очистка старых демо-данных...')

        Grade.objects.all().delete()
        Attendance.objects.all().delete()
        Homework.objects.all().delete()
        Schedule.objects.all().delete()
        TeachingAssignment.objects.all().delete()
        Classroom.objects.all().delete()
        StudyGroup.objects.all().delete()
        Subject.objects.all().delete()

        User.objects.filter(username__in=[
            'admin',
            'teacher',
            'teacher2',
            'student1',
            'student2',
            'student3',
            'student4',
        ]).delete()

        self.stdout.write('Создание пользователей...')

        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password123',
            role='admin',
            first_name='Алексей',
            last_name='Администраторов'
        )

        teacher = User.objects.create_user(
            username='teacher',
            email='teacher@example.com',
            password='password123',
            role='teacher',
            first_name='Иван',
            last_name='Петров',
            is_staff=True
        )

        teacher2 = User.objects.create_user(
            username='teacher2',
            email='teacher2@example.com',
            password='password123',
            role='teacher',
            first_name='Мария',
            last_name='Сидорова',
            is_staff=True
        )

        self.stdout.write('Создание групп...')

        group_is_31 = StudyGroup.objects.create(
            name='ИС-31',
            curator=teacher,
            description='Группа студентов по специальности информационные системы'
        )

        group_po_22 = StudyGroup.objects.create(
            name='ПО-22',
            curator=teacher2,
            description='Группа студентов по специальности программное обеспечение'
        )

        student1 = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='password123',
            role='student',
            first_name='Алихан',
            last_name='Нурланов',
            group=group_is_31
        )

        student2 = User.objects.create_user(
            username='student2',
            email='student2@example.com',
            password='password123',
            role='student',
            first_name='Дамир',
            last_name='Сериков',
            group=group_is_31
        )

        student3 = User.objects.create_user(
            username='student3',
            email='student3@example.com',
            password='password123',
            role='student',
            first_name='Аружан',
            last_name='Калиева',
            group=group_po_22
        )

        student4 = User.objects.create_user(
            username='student4',
            email='student4@example.com',
            password='password123',
            role='student',
            first_name='Ерасыл',
            last_name='Тулегенов',
            group=group_po_22
        )

        self.stdout.write('Создание предметов...')

        math = Subject.objects.create(
            name='Математика',
            description='Алгебра, геометрия и практические задачи'
        )

        physics = Subject.objects.create(
            name='Физика',
            description='Механика, электричество и основы физических законов'
        )

        informatics = Subject.objects.create(
            name='Информатика',
            description='Основы программирования, алгоритмы и базы данных'
        )

        history = Subject.objects.create(
            name='История',
            description='История Казахстана и всемирная история'
        )

        self.stdout.write('Создание кабинетов...')

        room_204 = Classroom.objects.create(
            number='204',
            description='Кабинет математики'
        )

        room_305 = Classroom.objects.create(
            number='305',
            description='Кабинет информатики'
        )

        room_112 = Classroom.objects.create(
            number='112',
            description='Кабинет истории'
        )

        room_210 = Classroom.objects.create(
            number='210',
            description='Кабинет физики'
        )

        self.stdout.write('Создание назначений преподавателей...')

        assignment_is31_math = TeachingAssignment.objects.create(
            teacher=teacher,
            subject=math,
            group=group_is_31,
            classroom=room_204
        )

        assignment_is31_informatics = TeachingAssignment.objects.create(
            teacher=teacher,
            subject=informatics,
            group=group_is_31,
            classroom=room_305
        )

        assignment_po22_physics = TeachingAssignment.objects.create(
            teacher=teacher2,
            subject=physics,
            group=group_po_22,
            classroom=room_210
        )

        assignment_po22_history = TeachingAssignment.objects.create(
            teacher=teacher2,
            subject=history,
            group=group_po_22,
            classroom=room_112
        )

        assignment_po22_math = TeachingAssignment.objects.create(
            teacher=teacher2,
            subject=math,
            group=group_po_22,
            classroom=room_204
        )

        self.stdout.write('Создание расписания...')

        demo_schedule = [
            # ИС-31
            (assignment_is31_math, 1, 1, time(8, 30), time(10, 0)),
            (assignment_is31_informatics, 1, 2, time(10, 10), time(11, 40)),
            (assignment_is31_math, 3, 1, time(8, 30), time(10, 0)),
            (assignment_is31_informatics, 4, 3, time(12, 10), time(13, 40)),

            # ПО-22
            (assignment_po22_math, 1, 1, time(8, 30), time(10, 0)),
            (assignment_po22_physics, 2, 2, time(10, 10), time(11, 40)),
            (assignment_po22_history, 3, 3, time(12, 10), time(13, 40)),
            (assignment_po22_physics, 5, 1, time(8, 30), time(10, 0)),
        ]

        for assignment, day, lesson_number, start_time, end_time in demo_schedule:
            Schedule.objects.create(
                assignment=assignment,
                day=day,
                lesson_number=lesson_number,
                start_time=start_time,
                end_time=end_time
            )

            self.stdout.write('Создание посещаемости...')

        demo_attendance = [
            # ИС-31
            (student1, assignment_is31_math, date(2026, 4, 20), 'present', 'Присутствовал на занятии.'),
            (student2, assignment_is31_math, date(2026, 4, 20), 'late', 'Опоздал на 10 минут.'),
            (student1, assignment_is31_informatics, date(2026, 4, 21), 'present', 'Активно работал на практике.'),
            (student2, assignment_is31_informatics, date(2026, 4, 21), 'absent', 'Отсутствовал без предупреждения.'),

            # ПО-22
            (student3, assignment_po22_physics, date(2026, 4, 20), 'present', 'Присутствовал.'),
            (student4, assignment_po22_physics, date(2026, 4, 20), 'excused', 'Отсутствовал по уважительной причине.'),
            (student3, assignment_po22_history, date(2026, 4, 22), 'late', 'Опоздал к началу занятия.'),
            (student4, assignment_po22_history, date(2026, 4, 22), 'present', 'Присутствовал на занятии.'),
        ]

        for student, assignment, attendance_date, status, comment in demo_attendance:
            Attendance.objects.create(
                student=student,
                assignment=assignment,
                date=attendance_date,
                status=status,
                comment=comment
            )

        self.stdout.write('Создание домашних заданий...')

        demo_homeworks = [
            (
                assignment_is31_math,
                'Квадратные уравнения',
                'Решить задачи №1-10 по теме квадратных уравнений. Повторить формулы дискриминанта и способы решения уравнений.',
                date(2026, 5, 12)
            ),
            (
                assignment_is31_informatics,
                'Основы баз данных',
                'Подготовить краткий конспект по теме SQL-запросов: SELECT, WHERE, ORDER BY. Сделать 5 примеров запросов.',
                date(2026, 5, 14)
            ),
            (
                assignment_po22_physics,
                'Законы Ньютона',
                'Повторить три закона Ньютона и решить задачи из учебника по теме динамики.',
                date(2026, 5, 13)
            ),
            (
                assignment_po22_history,
                'История Казахстана',
                'Подготовить сообщение на тему ключевых исторических событий Казахстана XX века.',
                date(2026, 5, 15)
            ),
            (
                assignment_po22_math,
                'Производные',
                'Решить примеры на нахождение производных простых функций. Повторить правила дифференцирования.',
                date(2026, 5, 16)
            ),
        ]

        for assignment, title, description, deadline in demo_homeworks:
            Homework.objects.create(
                assignment=assignment,
                title=title,
                description=description,
                deadline=deadline
            )

        self.stdout.write('Создание оценок...')

        demo_grades = [
            (student1, teacher, math, 5, 'Отлично решил задачи на контрольной работе.'),
            (student1, teacher, informatics, 5, 'Уверенно справился с практическим заданием.'),

            (student2, teacher, math, 4, 'Правильное решение, но есть неточности в оформлении.'),
            (student2, teacher, informatics, 5, 'Отличная работа с алгоритмами.'),

            (student3, teacher2, math, 3, 'Есть ошибки в вычислениях, нужно больше практики.'),
            (student3, teacher2, physics, 4, 'Материал усвоен хорошо.'),
            (student3, teacher2, history, 5, 'Отличный полный ответ.'),

            (student4, teacher2, math, 4, 'Хорошее выполнение задания.'),
            (student4, teacher2, physics, 5, 'Отличное понимание темы.'),
            (student4, teacher2, history, 4, 'Ответ хороший, но можно добавить больше фактов.'),
        ]

        for student, teacher_user, subject, value, comment in demo_grades:
            Grade.objects.create(
                student=student,
                teacher=teacher_user,
                subject=subject,
                value=value,
                comment=comment
            )

        self.stdout.write(self.style.SUCCESS('Демо-данные успешно созданы!'))
        self.stdout.write('')
        self.stdout.write('Данные для входа:')
        self.stdout.write('Администратор: admin / password123')
        self.stdout.write('Учитель 1: teacher / password123')
        self.stdout.write('Учитель 2: teacher2 / password123')
        self.stdout.write('Ученик 1: student1 / password123')
        self.stdout.write('Ученик 2: student2 / password123')
        self.stdout.write('Ученик 3: student3 / password123')
        self.stdout.write('Ученик 4: student4 / password123')