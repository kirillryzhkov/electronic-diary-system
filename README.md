# Electronic Diary System

**Electronic Diary System** — это дипломный проект системы электронного дневника, разработанный на Django и Django REST Framework.

Проект предназначен для работы с учениками, учителями, предметами и оценками.  
Система поддерживает роли пользователей, JWT-авторизацию, REST API, Swagger-документацию и автоматические тесты.

---

## Основные возможности

- Авторизация через JWT
- Роли пользователей:
  - Учитель
  - Ученик
- Управление предметами
- Добавление и редактирование оценок
- Просмотр оценок ученика
- Расчёт среднего балла ученика
- Статистика по предметам
- Ограничение доступа по ролям
- Документация API через Swagger
- Автоматические тесты

---

## Технологии

- Python
- Django
- Django REST Framework
- SimpleJWT
- drf-spectacular
- django-filter
- SQLite

---

## Структура проекта

```text
diary_project/
├── api/
│   ├── management/
│   │   └── commands/
│   │       └── seed_demo.py
│   └── v1/
│       ├── serializers.py
│       ├── urls.py
│       ├── views.py
│       ├── permissions.py
│       └── tests.py
│
├── users/
│   ├── models.py
│   ├── admin.py
│   └── apps.py
│
├── subjects/
│   ├── models.py
│   ├── admin.py
│   └── apps.py
│
├── grades/
│   ├── models.py
│   ├── admin.py
│   └── apps.py
│
├── diary_project/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── manage.py
├── requirements.txt
└── README.md

Установка и запуск проекта
1. Клонировать проект
git clone <ссылка-на-репозиторий>
cd diary_project
2. Создать виртуальное окружение
python -m venv .venv
3. Активировать виртуальное окружение

Для Windows:

.venv\Scripts\activate
4. Установить зависимости
pip install -r requirements.txt
5. Выполнить миграции
python manage.py migrate
6. Создать суперпользователя
python manage.py createsuperuser
7. Создать демонстрационные данные
python manage.py seed_demo
8. Запустить сервер
python manage.py runserver

После запуска проект будет доступен по адресу:

http://127.0.0.1:8000/
Демо-аккаунты

После запуска команды:

python manage.py seed_demo

будут созданы тестовые пользователи:

Роль	Логин	Пароль
Учитель	teacher	password123
Ученик	student1	password123
Ученик	student2	password123
Ученик	student3	password123
Админ-панель

Админ-панель доступна по адресу:

http://127.0.0.1:8000/admin/

В админ-панели можно управлять:

Пользователями
Предметами
Оценками
Swagger-документация API

Документация API доступна по адресу:

http://127.0.0.1:8000/api/docs/

Redoc-документация:

http://127.0.0.1:8000/api/redoc/

OpenAPI schema:

http://127.0.0.1:8000/api/schema/
Авторизация API

Для получения JWT-токена нужно отправить POST-запрос:

POST /api/v1/token/

Пример тела запроса:

{
  "username": "teacher",
  "password": "password123"
}

Ответ содержит access и refresh токены:

{
  "refresh": "...",
  "access": "..."
}

Для авторизации в Swagger нужно нажать кнопку Authorize и вставить:

Bearer <access_token>
API endpoints
Метод	URL	Описание	Доступ
POST	/api/v1/token/	Получение JWT-токена	Все
POST	/api/v1/token/refresh/	Обновление JWT-токена	Все
GET	/api/v1/subjects/	Получить список предметов	Учитель
POST	/api/v1/subjects/	Создать предмет	Учитель
GET	/api/v1/subjects/stats/	Статистика по предметам	Учитель
GET	/api/v1/grades/	Получить список оценок	Учитель / Ученик
POST	/api/v1/grades/create/	Создать оценку	Учитель
GET	/api/v1/grades/<id>/	Получить конкретную оценку	Учитель / владелец
PUT	/api/v1/grades/<id>/	Изменить оценку	Учитель
DELETE	/api/v1/grades/<id>/	Удалить оценку	Учитель
GET	/api/v1/average/	Средний балл ученика	Ученик
Роли и права доступа
Учитель

Учитель может:

просматривать все оценки;
создавать оценки;
редактировать оценки;
удалять оценки;
создавать предметы;
просматривать статистику по предметам.
Ученик

Ученик может:

просматривать только свои оценки;
смотреть свой средний балл;
не может изменять оценки;
не может просматривать оценки других учеников.
Примеры запросов
Получение списка оценок
GET /api/v1/grades/

Пример ответа:

{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "student": {
        "id": 2,
        "username": "student1"
      },
      "subject": {
        "id": 1,
        "name": "Математика"
      },
      "value": 5,
      "date": "2026-04-26"
    }
  ]
}
Получение среднего балла ученика
GET /api/v1/average/

Пример ответа:

{
  "average": 4.5
}
Статистика по предметам
GET /api/v1/subjects/stats/

Пример ответа:

[
  {
    "subject": "Математика",
    "total_grades": 3,
    "average": 4.0
  },
  {
    "subject": "Физика",
    "total_grades": 3,
    "average": 3.67
  }
]
Фильтрация оценок

Оценки можно фильтровать по предмету:

GET /api/v1/grades/?subject=1
Тестирование

Для запуска тестов:

python manage.py test api.v1.tests

Текущий результат тестирования:

Found 10 test(s).
System check identified no issues.
..........
Ran 10 tests

OK