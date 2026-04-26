from django.core.management.base import BaseCommand

from users.models import User
from subjects.models import Subject
from grades.models import Grade
from academic.models import StudyGroup, Classroom, TeachingAssignment


class Command(BaseCommand):
    help = 'Создает демонстрационные данные для электронного дневника'

    def handle(self, *args, **kwargs):
        self.stdout.write('Очистка старых демо-данных...')

        Grade.objects.all().delete()
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

        TeachingAssignment.objects.create(
            teacher=teacher,
            subject=math,
            group=group_is_31,
            classroom=room_204
        )

        TeachingAssignment.objects.create(
            teacher=teacher,
            subject=informatics,
            group=group_is_31,
            classroom=room_305
        )

        TeachingAssignment.objects.create(
            teacher=teacher2,
            subject=physics,
            group=group_po_22,
            classroom=room_210
        )

        TeachingAssignment.objects.create(
            teacher=teacher2,
            subject=history,
            group=group_po_22,
            classroom=room_112
        )

        TeachingAssignment.objects.create(
            teacher=teacher2,
            subject=math,
            group=group_po_22,
            classroom=room_204
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