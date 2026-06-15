import random
from datetime import date, datetime, time, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from academic.models import (
    StudyGroup,
    Classroom,
    TeachingAssignment,
    Schedule,
    Attendance,
    Homework,
)
from grades.models import Grade
from subjects.models import Subject
from users.models import User


class Command(BaseCommand):
    help = 'Создаёт реалистичные демонстрационные данные для электронного дневника'

    def handle(self, *args, **options):
        random.seed(42)

        self.stdout.write(self.style.WARNING('Создание данных электронного журнала...'))

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
        # Преподаватели и предметы
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

            # Предметы 4 курса для группы П4Б
            ('Компьютерные сети и информационная безопасность', 'teacher_network_security', 'Руслан', 'Нуртаев'),
            ('Data mining', 'teacher_data_mining', 'Ержан', 'Ахметов'),
            ('Моделирование атак и защиты инфоресурсов', 'teacher_attack_defense', 'Сергей', 'Васильев'),
            ('Анализ и оценка процессов предприятия', 'teacher_business_analysis', 'Алина', 'Ким'),
            ('Разработка и тестировка мобильных приложений', 'teacher_mobile_dev', 'Ирина', 'Орлова'),
        ]

        subject_descriptions = {
            'Математика': 'Дисциплина направлена на развитие логического мышления и навыков решения прикладных задач.',
            'Информатика': 'Дисциплина изучает основы работы с информацией, алгоритмами и программными средствами.',
            'Физика': 'Дисциплина изучает основные физические законы и их практическое применение.',
            'Базы данных': 'Дисциплина посвящена проектированию, созданию и использованию баз данных.',
            'Алгоритмы и структуры данных': 'Дисциплина изучает методы обработки данных и построения эффективных алгоритмов.',
            'Английский язык': 'Дисциплина направлена на развитие навыков профессионального и общего общения на английском языке.',
            'История Казахстана': 'Дисциплина изучает основные этапы исторического развития Казахстана.',
            'Веб-разработка': 'Дисциплина посвящена созданию современных веб-сайтов и веб-приложений.',
            'Операционные системы': 'Дисциплина изучает устройство, функции и принципы работы операционных систем.',
            'Компьютерные сети и информационная безопасность': 'Дисциплина изучает устройство компьютерных сетей и методы защиты информации.',
            'Data mining': 'Дисциплина посвящена анализу данных, поиску закономерностей и интеллектуальной обработке информации.',
            'Моделирование атак и защиты инфоресурсов': 'Дисциплина изучает угрозы информационной безопасности и методы защиты информационных ресурсов.',
            'Анализ и оценка процессов предприятия': 'Дисциплина направлена на изучение бизнес-процессов предприятия и методов их оценки.',
            'Разработка и тестировка мобильных приложений': 'Дисциплина посвящена созданию и проверке мобильных приложений.',
        }

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

            changed = False

            if teacher.role != 'teacher':
                teacher.role = 'teacher'
                changed = True

            if teacher.first_name != first_name:
                teacher.first_name = first_name
                changed = True

            if teacher.last_name != last_name:
                teacher.last_name = last_name
                changed = True

            if changed:
                teacher.save()

            subject, _ = Subject.objects.get_or_create(
                name=subject_name,
                defaults={
                    'description': subject_descriptions.get(
                        subject_name,
                        f'Дисциплина учебного плана: {subject_name}'
                    )
                }
            )

            if hasattr(subject, 'description'):
                new_description = subject_descriptions.get(
                    subject_name,
                    f'Дисциплина учебного плана: {subject_name}'
                )
                if subject.description != new_description:
                    subject.description = new_description
                    subject.save(update_fields=['description'])

            teachers_by_subject[subject_name] = {
                'teacher': teacher,
                'subject': subject,
            }

        # --------------------
        # Кабинеты
        # --------------------
        classroom_numbers = [
            '103', '201', '202', '203', '204', '205', '206', '207', '208',
            '301', '302', '303', '401', '406', '410'
        ]

        classrooms_by_number = {}
        classrooms = []

        for number in classroom_numbers:
            classroom, _ = Classroom.objects.get_or_create(
                number=number,
                defaults={
                    'description': f'Учебный кабинет №{number}'
                }
            )

            if hasattr(classroom, 'description') and not classroom.description:
                classroom.description = f'Учебный кабинет №{number}'
                classroom.save(update_fields=['description'])

            classrooms_by_number[number] = classroom
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
            ('П4Б', 'p4b'),
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

        teacher_list = [item['teacher'] for item in teachers_by_subject.values()]

        created_groups = []
        created_students = []
        groups_by_code = {}

        for group_index, (group_name, group_code) in enumerate(group_configs):
            curator = teacher_list[group_index % len(teacher_list)]

            group, _ = StudyGroup.objects.get_or_create(
                name=group_name,
                defaults={
                    'curator': curator,
                    'description': f'Учебная группа {group_name}'
                }
            )

            changed = False

            if group.curator != curator:
                group.curator = curator
                changed = True

            if hasattr(group, 'description') and (
                not group.description or 'Тестовая' in group.description
            ):
                group.description = f'Учебная группа {group_name}'
                changed = True

            if changed:
                group.save()

            created_groups.append((group, group_code))
            groups_by_code[group_code] = group

            # Для П4Б ниже создаются реальные студенты, поэтому здесь пропускаем случайную генерацию
            if group_code == 'p4b':
                continue

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

                if student.first_name != first_name:
                    student.first_name = first_name
                    changed = True

                if student.last_name != last_name:
                    student.last_name = last_name
                    changed = True

                if changed:
                    student.save()

                created_students.append(student)

        # --------------------
        # Реальные студенты группы П4Б
        # --------------------
        p4b_students = [
            ('Айдарұлы', 'Санжар'),
            ('Амангелді', 'Темірлан'),
            ('Багинский', 'Владимир'),
            ('Барботько', 'Руслан'),
            ('Белуш', 'Ярослав'),
            ('Беляков', 'Эмиль'),
            ('Бермухамбетов', 'Рахимжан'),
            ('Войчук', 'Даниил'),
            ('Громов', 'Михаил'),
            ('Иванников', 'Илья'),
            ('Иванов', 'Станислав'),
            ('Коршунов', 'Георгий'),
            ('Кузубова', 'Виктория'),
            ('Леденев', 'Александр'),
            ('Ли', 'Сафрон'),
            ('Лырчиков', 'Артем'),
            ('Муратов', 'Азиз'),
            ('Пан', 'Кирилл'),
            ('Пилюгина', 'София'),
            ('Пшеничный', 'Артем'),
            ('Репин', 'Никита'),
            ('Рыжков', 'Кирилл'),
            ('Сибилев', 'Эдуард'),
            ('Сорокин', 'Илья'),
            ('Таганов', 'Егор'),
            ('Терехин', 'Ярослав'),
            ('Ткачев', 'Алексей'),
            ('Торговский', 'Дмитрий'),
            ('Юсупова', 'Амина'),
        ]

        p4b_group = groups_by_code['p4b']

        if hasattr(p4b_group, 'description'):
            p4b_group.description = 'Учебная группа 4 курса П4Б'
            p4b_group.save(update_fields=['description'])

        for index, (last_name, first_name) in enumerate(p4b_students, start=1):
            username = f'p4b_st{index:02d}'

            student, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'student',
                    'group': p4b_group,
                }
            )

            if created:
                student.set_password('password123')
                student.save()

            changed = False

            if student.role != 'student':
                student.role = 'student'
                changed = True

            if student.group != p4b_group:
                student.group = p4b_group
                changed = True

            if student.first_name != first_name:
                student.first_name = first_name
                changed = True

            if student.last_name != last_name:
                student.last_name = last_name
                changed = True

            if changed:
                student.save()

            created_students.append(student)

        self.stdout.write(self.style.SUCCESS(f'Групп создано/обновлено: {len(created_groups)}'))
        self.stdout.write(self.style.SUCCESS(f'Студентов создано/обновлено: {len(created_students)}'))

        # --------------------
        # Назначения преподавателей
        # --------------------
        core_subject_names = [
            'Математика',
            'Информатика',
            'Физика',
            'Базы данных',
            'Алгоритмы и структуры данных',
            'Английский язык',
            'История Казахстана',
            'Веб-разработка',
            'Операционные системы',
        ]

        assignments = []

        for group_index, (group, group_code) in enumerate(created_groups):
            if group_code == 'p4b':
                continue

            group_subjects = [
                core_subject_names[group_index % len(core_subject_names)],
                core_subject_names[(group_index + 1) % len(core_subject_names)],
                core_subject_names[(group_index + 2) % len(core_subject_names)],
                core_subject_names[(group_index + 3) % len(core_subject_names)],
                core_subject_names[(group_index + 4) % len(core_subject_names)],
                core_subject_names[(group_index + 5) % len(core_subject_names)],
            ]

            for subject_index, subject_name in enumerate(group_subjects):
                teacher = teachers_by_subject[subject_name]['teacher']
                subject = teachers_by_subject[subject_name]['subject']
                classroom = classrooms[(group_index + subject_index) % len(classrooms)]

                assignment, _ = TeachingAssignment.objects.update_or_create(
                    teacher=teacher,
                    subject=subject,
                    group=group,
                    defaults={
                        'classroom': classroom
                    }
                )

                assignments.append(assignment)

        # Предметы и кабинеты для группы П4Б
        p4b_subjects = [
            ('Компьютерные сети и информационная безопасность', '410'),
            ('Data mining', '406'),
            ('Моделирование атак и защиты инфоресурсов', '401'),
            ('Анализ и оценка процессов предприятия', '103'),
            ('Разработка и тестировка мобильных приложений', '303'),
        ]

        p4b_assignments = {}

        for subject_name, classroom_number in p4b_subjects:
            teacher = teachers_by_subject[subject_name]['teacher']
            subject = teachers_by_subject[subject_name]['subject']
            classroom = classrooms_by_number[classroom_number]

            assignment, _ = TeachingAssignment.objects.update_or_create(
                teacher=teacher,
                subject=subject,
                group=p4b_group,
                defaults={
                    'classroom': classroom
                }
            )

            p4b_assignments[subject_name] = assignment
            assignments.append(assignment)

        self.stdout.write(self.style.SUCCESS(f'Назначений создано/обновлено: {len(assignments)}'))

                # --------------------
        # Расписание
        # --------------------
        day_choices = [choice[0] for choice in Schedule._meta.get_field('day').choices]

        def get_day_value(day_number):
            """
            Возвращает значение дня недели из choices модели Schedule.
            1 - понедельник, 2 - вторник, 3 - среда, 4 - четверг, 5 - пятница.
            """
            if len(day_choices) >= day_number:
                return day_choices[day_number - 1]
            return str(day_number)

        lesson_times = {
            1: (time(8, 0), time(9, 20)),
            2: (time(9, 30), time(10, 50)),
            3: (time(11, 0), time(12, 20)),
            4: (time(12, 50), time(14, 10)),
        }

        schedule_count = 0

        # Чтобы после повторного запуска не оставалось старое расписание
        Schedule.objects.all().delete()

        # --------------------
        # Расписание для обычных групп
        # --------------------
        for group_index, (group, group_code) in enumerate(created_groups):
            if group_code == 'p4b':
                continue

            group_assignments = [
                a for a in assignments
                if a.group_id == group.id
            ]

            if not group_assignments:
                continue

            for day_number in range(1, 6):  # понедельник - пятница
                day = get_day_value(day_number)

                for lesson_number in range(1, 5):  # 4 пары каждый день
                    assignment_index = (
                        group_index + day_number + lesson_number
                    ) % len(group_assignments)

                    assignment = group_assignments[assignment_index]

                    start_time, end_time = lesson_times[lesson_number]

                    Schedule.objects.create(
                        assignment=assignment,
                        day=day,
                        lesson_number=lesson_number,
                        start_time=start_time,
                        end_time=end_time,
                    )

                    schedule_count += 1

        # --------------------
        # Реалистичное расписание для П4Б
        # --------------------
        p4b_schedule = {
            1: [  # Понедельник
                'Компьютерные сети и информационная безопасность',
                'Data mining',
                'Моделирование атак и защиты инфоресурсов',
                'Разработка и тестировка мобильных приложений',
            ],
            2: [  # Вторник
                'Анализ и оценка процессов предприятия',
                'Компьютерные сети и информационная безопасность',
                'Data mining',
                'Разработка и тестировка мобильных приложений',
            ],
            3: [  # Среда
                'Моделирование атак и защиты инфоресурсов',
                'Анализ и оценка процессов предприятия',
                'Компьютерные сети и информационная безопасность',
                'Data mining',
            ],
            4: [  # Четверг
                'Разработка и тестировка мобильных приложений',
                'Моделирование атак и защиты инфоресурсов',
                'Анализ и оценка процессов предприятия',
                'Компьютерные сети и информационная безопасность',
            ],
            5: [  # Пятница
                'Data mining',
                'Разработка и тестировка мобильных приложений',
                'Моделирование атак и защиты инфоресурсов',
                'Анализ и оценка процессов предприятия',
            ],
        }

        for day_number, subjects in p4b_schedule.items():
            day = get_day_value(day_number)

            for lesson_number, subject_name in enumerate(subjects, start=1):
                assignment = p4b_assignments[subject_name]
                start_time, end_time = lesson_times[lesson_number]

                Schedule.objects.create(
                    assignment=assignment,
                    day=day,
                    lesson_number=lesson_number,
                    start_time=start_time,
                    end_time=end_time,
                )

                schedule_count += 1

        self.stdout.write(self.style.SUCCESS(f'Занятий в расписании добавлено: {schedule_count}'))

        # --------------------
        # Домашние задания
        # --------------------
        homework_count = 0

        default_homeworks = [
            (
                'Изучение теоретического материала',
                'Повторить материалы лекции и подготовить ответы на контрольные вопросы.'
            ),
            (
                'Практическое задание',
                'Выполнить практическую работу согласно методическим указаниям.'
            ),
            (
                'Подготовка к рубежному контролю',
                'Повторить изученные темы и подготовиться к проверочной работе.'
            ),
        ]

        subject_homeworks = {
            'Компьютерные сети и информационная безопасность': [
                (
                    'Практическая работа: настройка локальной сети',
                    'Составить схему локальной сети, указать IP-адреса устройств и описать назначение сетевого оборудования.'
                ),
                (
                    'Изучение принципов VLAN',
                    'Подготовить краткий конспект по теме VLAN и привести пример сегментации сети предприятия.'
                ),
                (
                    'Анализ угроз сетевой безопасности',
                    'Описать основные угрозы компьютерной сети и предложить меры защиты для учебной организации.'
                ),
            ],
            'Data mining': [
                (
                    'Анализ набора данных',
                    'Провести первичный анализ набора данных, определить признаки и описать найденные закономерности.'
                ),
                (
                    'Подготовка данных к обработке',
                    'Описать этапы очистки данных, удаления пропусков и подготовки признаков для анализа.'
                ),
                (
                    'Построение простого прогноза',
                    'Составить описание модели прогнозирования и объяснить, какие данные используются для результата.'
                ),
            ],
            'Моделирование атак и защиты инфоресурсов': [
                (
                    'Разработка модели угроз',
                    'Составить модель угроз для веб-приложения и описать возможные способы защиты.'
                ),
                (
                    'Анализ уязвимостей информационной системы',
                    'Определить возможные уязвимости в информационной системе и предложить методы их устранения.'
                ),
                (
                    'План защиты информационных ресурсов',
                    'Подготовить план мероприятий по защите информационных ресурсов учебной организации.'
                ),
            ],
            'Анализ и оценка процессов предприятия': [
                (
                    'Описание бизнес-процесса',
                    'Описать бизнес-процесс обработки заявки клиента и выделить основные этапы.'
                ),
                (
                    'Построение схемы процесса',
                    'Подготовить текстовую схему процесса предприятия с указанием входных и выходных данных.'
                ),
                (
                    'Оценка эффективности процесса',
                    'Выделить показатели эффективности процесса и предложить возможные улучшения.'
                ),
            ],
            'Разработка и тестировка мобильных приложений': [
                (
                    'Макет экрана авторизации',
                    'Разработать структуру экрана авторизации мобильного приложения и описать основные элементы.'
                ),
                (
                    'Тестирование мобильного интерфейса',
                    'Составить список проверок для мобильного приложения: ввод данных, кнопки, навигация и ошибки.'
                ),
                (
                    'Проектирование пользовательского сценария',
                    'Описать пользовательский сценарий входа в приложение и просмотра учебной информации.'
                ),
            ],
        }

        for assignment in assignments:
            homework_data = subject_homeworks.get(
                assignment.subject.name,
                default_homeworks
            )

            for i, (title, description) in enumerate(homework_data, start=1):
                _, created = Homework.objects.update_or_create(
                    assignment=assignment,
                    title=title,
                    defaults={
                        'description': description,
                        'deadline': date.today() + timedelta(days=7 * i),
                    }
                )

                if created:
                    homework_count += 1

        self.stdout.write(self.style.SUCCESS(f'Домашних заданий добавлено: {homework_count}'))

        # --------------------
        # Оценки
        # --------------------
                # --------------------
        # Оценки
        # --------------------
        grades_count = 0

        strong_students = {
            'Рыжков', 'Юсупова', 'Пан', 'Пилюгина', 'Репин',
            'Кузубова', 'Громов', 'Айдарұлы', 'Иванов'
        }

        good_students = {
            'Амангелді', 'Багинский', 'Беляков', 'Иванников',
            'Коршунов', 'Леденев', 'Ли', 'Муратов', 'Пшеничный',
            'Сибилев', 'Сорокин', 'Терехин'
        }

        def get_student_value(student, important=False):
            """
            Реалистичное распределение оценок:
            сильные студенты чаще получают 5,
            хорошие — 4 и 5,
            остальные — 3 и 4, иногда 5.
            """
            if student.last_name in strong_students:
                values = [5, 5, 5, 5, 4] if not important else [5, 5, 5, 4]
            elif student.last_name in good_students:
                values = [5, 4, 4, 4, 3] if not important else [5, 4, 4, 4]
            else:
                values = [4, 4, 3, 3, 3, 5] if not important else [4, 4, 3, 3]

            return random.choice(values)

        def make_aware(dt):
            if timezone.is_naive(dt):
                return timezone.make_aware(dt, timezone.get_current_timezone())
            return dt

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
                date__date=dt.date() if dt else None,
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
                Grade.objects.filter(pk=grade.pk).update(date=make_aware(dt))

            grades_count += 1

        current_comments = [
            'Ответ у доски',
            'Практическая работа',
            'Самостоятельная работа',
            'Лабораторная работа',
            'Домашнее задание',
            'Контрольная работа',
            'Устный опрос',
            'Работа на занятии',
            'Выполнение задания',
            'Проверочная работа',
            'Работа с конспектом',
            'Защита практической работы',
        ]

        subject_topics = {
            'Компьютерные сети и информационная безопасность': [
                'IP-адресация',
                'сетевые протоколы',
                'VLAN',
                'маршрутизация',
                'межсетевые экраны',
                'защита локальной сети',
                'анализ сетевых угроз',
            ],
            'Data mining': [
                'предобработка данных',
                'поиск закономерностей',
                'классификация данных',
                'кластеризация',
                'анализ признаков',
                'очистка данных',
                'построение прогноза',
            ],
            'Моделирование атак и защиты инфоресурсов': [
                'модель угроз',
                'анализ уязвимостей',
                'защита веб-приложений',
                'оценка рисков',
                'меры защиты',
                'сценарии атак',
                'защита информационных ресурсов',
            ],
            'Анализ и оценка процессов предприятия': [
                'бизнес-процесс',
                'оценка эффективности',
                'схема процесса',
                'входные и выходные данные',
                'оптимизация процесса',
                'анализ деятельности предприятия',
                'описание процесса обслуживания',
            ],
            'Разработка и тестировка мобильных приложений': [
                'экран авторизации',
                'пользовательский сценарий',
                'тест-кейс',
                'мобильный интерфейс',
                'проверка формы',
                'адаптация экрана',
                'тестирование приложения',
            ],
        }

        default_topics = [
            'теоретический материал',
            'практическое задание',
            'контрольные вопросы',
            'самостоятельная работа',
            'учебный раздел',
            'домашнее задание',
        ]

        def generate_grade_dates(start_date, end_date):
            """
            Генерирует учебные даты с 12.09.2025 по 17.05.2026.
            Берём только будние дни, чтобы журнал выглядел реалистично.
            """
            result = []
            current = start_date

            while current <= end_date:
                if current.weekday() < 5:
                    result.append(current)
                current += timedelta(days=1)

            return result

        academic_start = date(2025, 9, 12)
        academic_end = date(2026, 5, 17)

        all_school_dates = generate_grade_dates(academic_start, academic_end)

        month_attestation_dates = {
            9: datetime(2025, 9, 30, 12, 0),
            10: datetime(2025, 10, 31, 12, 0),
            11: datetime(2025, 11, 28, 12, 0),
            12: datetime(2025, 12, 25, 12, 0),
            1: datetime(2026, 1, 30, 12, 0),
            2: datetime(2026, 2, 27, 12, 0),
            3: datetime(2026, 3, 31, 12, 0),
            4: datetime(2026, 4, 30, 12, 0),
            5: datetime(2026, 5, 16, 12, 0),
        }

        month_names = {
            1: 'январь',
            2: 'февраль',
            3: 'март',
            4: 'апрель',
            5: 'май',
            9: 'сентябрь',
            10: 'октябрь',
            11: 'ноябрь',
            12: 'декабрь',
        }

        for assignment in assignments:
            students = User.objects.filter(
                role='student',
                group=assignment.group
            ).order_by('last_name', 'first_name')

            topics = subject_topics.get(assignment.subject.name, default_topics)

            # Берём разные даты для каждого предмета, чтобы оценки не стояли все в один день
            subject_dates = random.sample(all_school_dates, 18)
            subject_dates.sort()

            for student_index, student in enumerate(students, start=1):
                # --------------------
                # Текущие оценки за учебный год
                # --------------------
                for grade_index, grade_day in enumerate(subject_dates, start=1):
                    lesson_time = datetime.combine(
                        grade_day,
                        time(
                            hour=random.choice([8, 9, 10, 11, 12, 14, 15]),
                            minute=random.choice([0, 10, 15, 20, 30, 40])
                        )
                    )

                    comment = f'{random.choice(current_comments)}: {random.choice(topics)}'

                    create_grade(
                        student=student,
                        teacher=assignment.teacher,
                        subject=assignment.subject,
                        value=get_student_value(student),
                        comment=comment,
                        grade_type='current',
                        dt=lesson_time + timedelta(minutes=student_index % 25)
                    )

                # --------------------
                # Месячные аттестации с сентября по май
                # --------------------
                for month, attestation_dt in month_attestation_dates.items():
                    create_grade(
                        student=student,
                        teacher=assignment.teacher,
                        subject=assignment.subject,
                        value=get_student_value(student, important=True),
                        comment=f'Аттестация за {month_names[month]}',
                        grade_type='monthly',
                        month=month,
                        dt=attestation_dt + timedelta(minutes=student_index)
                    )

                # --------------------
                # 1 полугодие
                # --------------------
                create_grade(
                    student=student,
                    teacher=assignment.teacher,
                    subject=assignment.subject,
                    value=get_student_value(student, important=True),
                    comment='Итоговая оценка за 1 полугодие',
                    grade_type='semester',
                    semester=1,
                    dt=datetime(2025, 12, 26, 10, 0) + timedelta(minutes=student_index)
                )

                create_grade(
                    student=student,
                    teacher=assignment.teacher,
                    subject=assignment.subject,
                    value=get_student_value(student, important=True),
                    comment='Экзаменационная работа за 1 полугодие',
                    grade_type='exam',
                    semester=1,
                    dt=datetime(2025, 12, 27, 10, 0) + timedelta(minutes=student_index)
                )

                # --------------------
                # 2 полугодие
                # --------------------
                create_grade(
                    student=student,
                    teacher=assignment.teacher,
                    subject=assignment.subject,
                    value=get_student_value(student, important=True),
                    comment='Итоговая оценка за 2 полугодие',
                    grade_type='semester',
                    semester=2,
                    dt=datetime(2026, 5, 16, 10, 0) + timedelta(minutes=student_index)
                )

                create_grade(
                    student=student,
                    teacher=assignment.teacher,
                    subject=assignment.subject,
                    value=get_student_value(student, important=True),
                    comment='Итоговая экзаменационная работа',
                    grade_type='exam',
                    semester=2,
                    dt=datetime(2026, 5, 17, 10, 0) + timedelta(minutes=student_index)
                )

        self.stdout.write(self.style.SUCCESS(f'Оценок добавлено: {grades_count}'))

         # --------------------
        # Посещаемость
        # --------------------
        attendance_count = 0

        day_choices = [choice[0] for choice in Schedule._meta.get_field('day').choices]

        strong_students = {
            'Рыжков', 'Юсупова', 'Пан', 'Пилюгина', 'Репин',
            'Кузубова', 'Громов', 'Айдарұлы', 'Иванов'
        }

        good_students = {
            'Амангелді', 'Багинский', 'Беляков', 'Иванников',
            'Коршунов', 'Леденев', 'Ли', 'Муратов', 'Пшеничный',
            'Сибилев', 'Сорокин', 'Терехин'
        }

        def get_day_number(schedule_day):
            """
            Получает номер дня недели.
            1 - понедельник, 2 - вторник и так далее.
            """
            for index, day_value in enumerate(day_choices, start=1):
                if day_value == schedule_day:
                    return index

            try:
                return int(schedule_day)
            except (TypeError, ValueError):
                return 1

        def get_lesson_dates(schedule_day, start_date, end_date):
            """
            Генерирует даты занятий по расписанию
            с 12 сентября 2025 года по 17 мая 2026 года.
            """
            day_number = get_day_number(schedule_day)
            current = start_date
            result = []

            while current <= end_date:
                if current.isoweekday() == day_number:
                    result.append(current)

                current += timedelta(days=1)

            return result

        def choose_attendance_status(student):
            """
            Реалистичное распределение посещаемости.
            Большинство занятий посещено, иногда есть опоздания,
            уважительные причины и пропуски.
            """
            if student.last_name in strong_students:
                statuses = (
                    ['present'] * 22 +
                    ['late'] * 1 +
                    ['excused'] * 1
                )
            elif student.last_name in good_students:
                statuses = (
                    ['present'] * 19 +
                    ['late'] * 2 +
                    ['excused'] * 2 +
                    ['absent'] * 1
                )
            else:
                statuses = (
                    ['present'] * 16 +
                    ['late'] * 3 +
                    ['excused'] * 2 +
                    ['absent'] * 3
                )

            return random.choice(statuses)

        def attendance_comment(status):
            """
            Комментарии без тестовых надписей.
            """
            comments = {
                'present': [
                    '',
                    'Присутствовал на занятии',
                    'Работал на практическом занятии',
                    'Участвовал в обсуждении темы',
                    'Выполнил задание на занятии',
                ],
                'late': [
                    'Опоздание на занятие',
                    'Опоздание на 10 минут',
                    'Опоздание по уважительной причине',
                ],
                'absent': [
                    'Отсутствовал на занятии',
                    'Отсутствовал без уважительной причины',
                ],
                'excused': [
                    'Уважительная причина',
                    'Справка предоставлена',
                    'Предупредил заранее',
                ],
            }

            return random.choice(comments.get(status, ['']))

        attendance_start = date(2025, 9, 12)
        attendance_end = date(2026, 5, 17)

        schedule_items = Schedule.objects.select_related(
            'assignment',
            'assignment__group',
            'assignment__subject',
            'assignment__teacher',
        ).all()

        for schedule_item in schedule_items:
            assignment = schedule_item.assignment

            students = User.objects.filter(
                role='student',
                group=assignment.group
            ).order_by('last_name', 'first_name')

            lesson_dates = get_lesson_dates(
                schedule_day=schedule_item.day,
                start_date=attendance_start,
                end_date=attendance_end,
            )

            for lesson_date in lesson_dates:
                for student in students:
                    status = choose_attendance_status(student)

                    _, created = Attendance.objects.update_or_create(
                        student=student,
                        assignment=assignment,
                        date=lesson_date,
                        defaults={
                            'status': status,
                            'comment': attendance_comment(status),
                        }
                    )

                    if created:
                        attendance_count += 1

        self.stdout.write(self.style.SUCCESS(f'Записей посещаемости добавлено: {attendance_count}'))