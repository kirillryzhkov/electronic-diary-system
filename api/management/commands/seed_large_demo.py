import random
from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from academic.models import StudyGroup, Classroom, TeachingAssignment, Schedule, Attendance, Homework
from grades.models import Grade
from subjects.models import Subject
from users.models import User



class Command(BaseCommand):
    help = 'Создаёт расширенные тестовые данные: 7 групп по 10-15 студентов'

    def handle(self, *args, **options):
        random.seed(42)

        self.stdout.write(self.style.WARNING('Создание расширенных тестовых данных...'))

        # --------------------
        # Администратор
        # --------------------
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Администратор',
                'last_name': 'Системы',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )

        if created:
            admin.set_password('password123')
            admin.save()

        # --------------------
        # Преподаватели + предметы
        # --------------------
        teacher_subjects = [
            ('Математика', 'teacher_math', 'Алексей', 'Иванов'),
            ('Информатика', 'teacher_info', 'Дмитрий', 'Сергеев'),
            ('Физика', 'teacher_physics', 'Арман', 'Садыков'),
            ('Базы данных', 'teacher_db', 'Ержан', 'Ахметов'),
            ('Алгоритмы и структуры данных', 'teacher_algo', 'Никита', 'Павлов'),
            ('Английский язык', 'teacher_english', 'Алина', 'Ким'),
            ('История Казахстана', 'teacher_history', 'Марат', 'Жумабаев'),
            ('Веб-разработка', 'teacher_web', 'Ирина', 'Орлова'),
            ('Операционные системы', 'teacher_os', 'Сергей', 'Васильев'),
        ]

        teachers_by_subject = {}

        for subject_name, username, first_name, last_name in teacher_subjects:
            teacher, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'teacher',
                }
            )

            if created:
                teacher.set_password('password123')
                teacher.save()

            if teacher.role != 'teacher':
                teacher.role = 'teacher'
                teacher.save(update_fields=['role'])

            subject, _ = Subject.objects.get_or_create(
                name=subject_name,
                defaults={
                    'description': f'Учебный предмет: {subject_name}'
                }
            )

            teachers_by_subject[subject_name] = {
                'teacher': teacher,
                'subject': subject,
            }

        # --------------------
        # Кабинеты
        # --------------------
        classroom_numbers = ['201', '202', '203', '204', '205', '206', '207', '208', '301', '302']
        classrooms = []

        for number in classroom_numbers:
            classroom, _ = Classroom.objects.get_or_create(
                number=number,
                defaults={
                    'description': f'Учебный кабинет №{number}'
                }
            )
            classrooms.append(classroom)

        # --------------------
        # Группы
        # --------------------
        group_configs = [
            ('ИС-11', 'is11'),
            ('ИС-12', 'is12'),
            ('ПО-21', 'po21'),
            ('ПО-22', 'po22'),
            ('ВТ-31', 'vt31'),
            ('ВТ-32', 'vt32'),
            ('CS-41', 'cs41'),
        ]

        first_names = [
            'Андрей', 'Артём', 'Даниил', 'Максим', 'Кирилл',
            'Нурсултан', 'Алихан', 'Руслан', 'Егор', 'Илья',
            'Тимур', 'Азамат', 'Бекзат', 'Денис', 'Михаил',
            'София', 'Алина', 'Диана', 'Виктория', 'Мария',
            'Екатерина', 'Аружан', 'Айдана', 'Асель', 'Камила',
            'Полина', 'Елизавета', 'Анастасия', 'Дарья', 'Анна',
        ]

        last_names = [
            'Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов',
            'Попов', 'Васильев', 'Ахметов', 'Садыков', 'Жумабаев',
            'Нуртаев', 'Тлеубергенов', 'Ким', 'Абдрахманов', 'Сергеев',
            'Павлов', 'Орлов', 'Новиков', 'Фролов', 'Морозов',
            'Белов', 'Ковалёв', 'Зайцев', 'Громов', 'Мельников',
        ]

        created_groups = []
        created_students = []

        teacher_list = [item['teacher'] for item in teachers_by_subject.values()]

        for group_index, (group_name, group_code) in enumerate(group_configs):
            curator = teacher_list[group_index % len(teacher_list)]

            group, _ = StudyGroup.objects.get_or_create(
                name=group_name,
                defaults={
                    'curator': curator,
                    'description': f'Тестовая учебная группа {group_name}'
                }
            )

            if group.curator != curator:
                group.curator = curator
                group.save(update_fields=['curator'])

            created_groups.append((group, group_code))

            student_count = random.randint(10, 15)

            for student_index in range(1, student_count + 1):
                username = f'{group_code}_st{student_index:02d}'

                first_name = first_names[(group_index * 6 + student_index) % len(first_names)]
                last_name = last_names[(group_index * 5 + student_index) % len(last_names)]

                student, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': 'student',
                        'group': group,
                    }
                )

                if created:
                    student.set_password('password123')
                    student.save()

                changed = False

                if student.role != 'student':
                    student.role = 'student'
                    changed = True

                if student.group != group:
                    student.group = group
                    changed = True

                if changed:
                    student.save()

                created_students.append(student)

        self.stdout.write(self.style.SUCCESS(f'Групп создано/обновлено: {len(created_groups)}'))
        self.stdout.write(self.style.SUCCESS(f'Студентов создано/обновлено: {len(created_students)}'))

        # --------------------
        # Назначения преподавателей
        # --------------------
        subject_names = list(teachers_by_subject.keys())
        assignments = []

        for group_index, (group, group_code) in enumerate(created_groups):
            group_subjects = [
                subject_names[group_index % len(subject_names)],
                subject_names[(group_index + 1) % len(subject_names)],
                subject_names[(group_index + 2) % len(subject_names)],
                subject_names[(group_index + 3) % len(subject_names)],
                subject_names[(group_index + 4) % len(subject_names)],
                subject_names[(group_index + 5) % len(subject_names)],
            ]

            for subject_index, subject_name in enumerate(group_subjects):
                teacher = teachers_by_subject[subject_name]['teacher']
                subject = teachers_by_subject[subject_name]['subject']
                classroom = classrooms[(group_index + subject_index) % len(classrooms)]

                assignment, _ = TeachingAssignment.objects.get_or_create(
                    teacher=teacher,
                    subject=subject,
                    group=group,
                    defaults={
                        'classroom': classroom
                    }
                )

                if not assignment.classroom:
                    assignment.classroom = classroom
                    assignment.save(update_fields=['classroom'])

                assignments.append(assignment)

        self.stdout.write(self.style.SUCCESS(f'Назначений создано/обновлено: {len(assignments)}'))

        # --------------------
        # Расписание
        # --------------------
        day_choices = [choice[0] for choice in Schedule._meta.get_field('day').choices]
        weekdays = day_choices[:5]

        lesson_times = [
            (1, time(8, 0), time(8, 50)),
            (2, time(9, 0), time(9, 50)),
            (3, time(10, 0), time(10, 50)),
            (4, time(11, 0), time(11, 50)),
            (5, time(12, 0), time(12, 50)),
            (6, time(13, 0), time(13, 50)),
        ]

        schedule_count = 0

        for group_index, (group, _) in enumerate(created_groups):
            group_assignments = [a for a in assignments if a.group_id == group.id]

            for idx, assignment in enumerate(group_assignments):
                day = weekdays[(group_index + idx) % len(weekdays)]
                lesson_number, start_time, end_time = lesson_times[idx % len(lesson_times)]

                _, created = Schedule.objects.get_or_create(
                    assignment=assignment,
                    day=day,
                    lesson_number=lesson_number,
                    start_time=start_time,
                    end_time=end_time,
                )

                if created:
                    schedule_count += 1

        self.stdout.write(self.style.SUCCESS(f'Занятий в расписании добавлено: {schedule_count}'))

        # --------------------
        # Домашние задания
        # --------------------
        homework_count = 0

        for assignment in assignments:
            homework_data = [
            (
                f'Домашняя работа 1 по предмету {assignment.subject.name}',
                f'Повторить основные темы по предмету {assignment.subject.name}, выполнить практические задания и подготовиться к устному опросу.'
            ),
            (
                f'Домашняя работа 2 по предмету {assignment.subject.name}',
                f'Подготовить краткий конспект, решить дополнительные упражнения и повторить материал предыдущих занятий по предмету {assignment.subject.name}.'
            ),
            (
                f'Подготовка к контрольной работе по предмету {assignment.subject.name}',
                f'Повторить теорию, основные определения, формулы и примеры задач по предмету {assignment.subject.name}.'
            ),
        ]

            for i, (title, description) in enumerate(homework_data, start=1):
                _, created = Homework.objects.update_or_create(
                    assignment=assignment,
                    title=title,
                    defaults={
                        'description': description,
                        'deadline': date.today() + timedelta(days=5 * i),
                    }
                )

                if created:
                    homework_count += 1

        self.stdout.write(self.style.SUCCESS(f'Домашних заданий добавлено: {homework_count}'))

        # --------------------
        # Оценки
        # --------------------
        grades_count = 0

        def create_grade(
            student,
            teacher,
            subject,
            value,
            comment,
            grade_type='current',
            month=None,
            semester=None,
            dt=None
        ):
            nonlocal grades_count

            exists = Grade.objects.filter(
                student=student,
                teacher=teacher,
                subject=subject,
                comment=comment,
                grade_type=grade_type,
                month=month,
                semester=semester,
            ).exists()

            if exists:
                return

            grade = Grade.objects.create(
                student=student,
                teacher=teacher,
                subject=subject,
                value=value,
                comment=comment,
                grade_type=grade_type,
                month=month,
                semester=semester,
            )

            if dt:
                aware_dt = timezone.make_aware(dt, timezone.get_current_timezone())
                Grade.objects.filter(pk=grade.pk).update(date=aware_dt)

            grades_count += 1

        base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

        current_comments = [
            'Активная работа на занятии',
            'Хороший ответ у доски',
            'Самостоятельная работа',
            'Практическая работа выполнена',
            'Устный ответ',
            'Работа на уроке',
            'Домашнее задание выполнено',
            'Контрольный опрос',
        ]

        monthly_comments = [
            'Месячная аттестация',
            'Итог за месяц',
            'Промежуточная аттестация за месяц',
        ]

        semester_comments = [
            'Полугодовая сессия',
            'Итоговая сессия за полугодие',
        ]

        exam_comments = [
            'Экзаменационная работа',
            'Итоговый экзамен',
        ]

        for assignment in assignments:
            students = User.objects.filter(
                role='student',
                group=assignment.group
            ).order_by('id')

            for student_index, student in enumerate(students, start=1):
                # текущие оценки
                # текущие оценки
                current_values = [
                    random.randint(3, 5),
                    random.randint(3, 5),
                    random.randint(2, 5),
                    random.randint(3, 5),
                    random.randint(2, 5),
                ]

                for current_idx, value in enumerate(current_values, start=1):
                    create_grade(
                        student=student,
                        teacher=assignment.teacher,
                        subject=assignment.subject,
                        value=value,
                        comment=random.choice(current_comments),
                        grade_type='current',
                        dt=base_date - timedelta(days=(student_index + current_idx + assignment.id) % 45)
                    )

                # месячные аттестации
                for month in [2, 3, 4, 5]:
                    create_grade(
                        student=student,
                        teacher=assignment.teacher,
                        subject=assignment.subject,
                        value=random.randint(3, 5),
                        comment=f'{random.choice(monthly_comments)} за {month} месяц',
                        grade_type='monthly',
                        month=month,
                        dt=base_date - timedelta(days=(student_index + month + assignment.id) % 60)
                    )

                # сессии и экзамены
                create_grade(
                    student=student,
                    teacher=assignment.teacher,
                    subject=assignment.subject,
                    value=random.randint(3, 5),
                    comment=f'{random.choice(semester_comments)} за 1 полугодие',
                    grade_type='semester',
                    semester=1,
                    dt=base_date - timedelta(days=(student_index + assignment.id) % 70)
                )

                create_grade(
                    student=student,
                    teacher=assignment.teacher,
                    subject=assignment.subject,
                    value=random.randint(3, 5),
                    comment=f'{random.choice(exam_comments)} за 1 полугодие',
                    grade_type='exam',
                    semester=1,
                    dt=base_date - timedelta(days=(student_index + assignment.id + 5) % 75)
                )

                create_grade(
                    student=student,
                    teacher=assignment.teacher,
                    subject=assignment.subject,
                    value=random.randint(3, 5),
                    comment=f'{random.choice(semester_comments)} за 2 полугодие',
                    grade_type='semester',
                    semester=2,
                    dt=base_date - timedelta(days=(student_index + assignment.id + 10) % 80)
                )

                create_grade(
                    student=student,
                    teacher=assignment.teacher,
                    subject=assignment.subject,
                    value=random.randint(3, 5),
                    comment=f'{random.choice(exam_comments)} за 2 полугодие',
                    grade_type='exam',
                    semester=2,
                    dt=base_date - timedelta(days=(student_index + assignment.id + 15) % 85)
                )

        self.stdout.write(self.style.SUCCESS(f'Оценок добавлено: {grades_count}'))

        # --------------------
        # Посещаемость
        # --------------------
        attendance_count = 0

        attendance_dates = [
            date.today() - timedelta(days=10),
            date.today() - timedelta(days=8),
            date.today() - timedelta(days=6),
            date.today() - timedelta(days=4),
            date.today() - timedelta(days=2),
        ]

        statuses = ['present', 'present', 'present', 'late', 'absent', 'excused']

        for assignment in assignments:
            students = User.objects.filter(
                role='student',
                group=assignment.group
            )

            for student in students:
                for att_date in attendance_dates:
                    _, created = Attendance.objects.update_or_create(
                        student=student,
                        assignment=assignment,
                        date=att_date,
                        defaults={
                            'status': random.choice(statuses),
                            'comment': 'Тестовая запись посещаемости'
                        }
                    )

                    if created:
                        attendance_count += 1

        self.stdout.write(self.style.SUCCESS(f'Записей посещаемости добавлено: {attendance_count}'))

        self.stdout.write(self.style.SUCCESS('Расширенные тестовые данные успешно созданы.'))
        self.stdout.write(self.style.SUCCESS('Пароль для всех созданных пользователей: password123'))

        self.stdout.write(self.style.SUCCESS('Преподаватели:'))
        for subject_name, data in teachers_by_subject.items():
            self.stdout.write(f'{data["teacher"].username} — {subject_name}')

        self.stdout.write(self.style.SUCCESS('Примеры студентов:'))
        for _, group_code in group_configs:
            self.stdout.write(f'{group_code}_st01 / password123')