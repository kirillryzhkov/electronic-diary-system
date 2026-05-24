# Техническая часть проекта

Файл предназначен для подготовки к защите дипломного проекта. Здесь описана техническая структура Electronic Diary System.

## 1. Технологический стек

В проекте используются:

- Python — основной язык программирования;
- Django — backend-фреймворк;
- Django REST Framework — REST API;
- SimpleJWT — JWT-авторизация для API;
- drf-spectacular — Swagger/OpenAPI-документация;
- SQLite — база данных для разработки и демонстрации;
- HTML, CSS, JavaScript — интерфейс;
- openpyxl — формирование Excel-отчётов;
- WhiteNoise — отдача статических файлов на Render;
- Gunicorn — WSGI-сервер для деплоя;
- Git и GitHub — контроль версий.

## 2. Архитектура проекта

Проект построен по классической архитектуре Django:

```text
Пользователь → браузер → Django views → forms → models → SQLite
```

Для API используется схема:

```text
API-клиент → DRF view → serializer → model → database → JSON response
```

## 3. Основные приложения Django

### users

Содержит кастомную модель пользователя. Пользователь имеет роль:

- admin;
- teacher;
- student.

Студент может быть привязан к учебной группе.

### subjects

Хранит учебные предметы. Предметы используются в оценках, расписании, домашних заданиях и назначениях преподавателей.

### grades

Хранит оценки студентов. Модель Grade поддерживает текущие оценки, месячные аттестации, сессии и экзамены.

### academic

Содержит учебные сущности:

- StudyGroup;
- Classroom;
- TeachingAssignment;
- Schedule;
- Attendance;
- Homework.

### frontend

Содержит формы, views, маршруты и HTML-шаблоны пользовательского интерфейса.

### api

Содержит REST API проекта, сериализаторы, permissions и тесты.

### notifications_app

Отвечает за уведомления пользователей.

## 4. База данных

Основная база данных — SQLite. Для учебного проекта она удобна, потому что не требует отдельного сервера.

Основные таблицы:

- users_user;
- subjects_subject;
- grades;
- study_groups;
- classrooms;
- teaching_assignments;
- schedule;
- attendance;
- homework;
- notifications.

## 5. Безопасность

В проекте используются следующие механизмы безопасности:

- авторизация пользователей;
- разграничение доступа по ролям;
- Django permissions и mixins;
- CSRF-защита форм;
- JWT-аутентификация для API;
- фильтрация данных по текущему пользователю.

Пример: студент видит только свои оценки, а преподаватель — только оценки и посещаемость по своим назначениям.

## 6. Деплой

Проект подготовлен к деплою на Render:

- добавлен STATIC_ROOT;
- подключён WhiteNoise;
- добавлен Gunicorn;
- ALLOWED_HOSTS можно настраивать через переменную окружения DJANGO_ALLOWED_HOSTS;
- DEBUG можно отключить через DJANGO_DEBUG=False.

Рекомендуемые команды Render:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

Start Command:

```bash
gunicorn diary_project.wsgi:application
```

## 7. Тестовые данные

В проекте есть команда seed_large_demo. Она создаёт демонстрационные данные:

- 7 учебных групп;
- 10–15 студентов в каждой группе;
- преподавателей;
- предметы;
- кабинеты;
- расписание;
- оценки;
- посещаемость;
- домашние задания.

Запуск:

```bash
python manage.py seed_large_demo
```
