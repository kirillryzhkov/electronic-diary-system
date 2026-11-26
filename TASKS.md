# TASKS.md — Координация разработки (Codex + Antigravity)

Проект: `D:\Projects\electronic-diary-system` (Django 5.1 + DRF)
Основная ветка: `main`

## Завершённые спринты
- [x] **Спринт v1:** Интерактивный журнал-сетка (`/journal/`), API `/api/v1/journal/*`, `GradeAuditLog`.
- [x] **Спринт v2:** Очередь проверки ДЗ (`/homework/review-queue/`), автозапись оценки в журнал + аудит, группа риска, экспорт ведомости Excel (25/25 тестов `OK`).

---

## Спринт v3: Telegram-уведомления + Аналитика дашборда + Docker/PostgreSQL

### Рабочие директории (`git worktree`)
- **Codex (`feat/v3-backend`):** `D:\Projects\electronic-diary-system-codex` (файлы: `users/`, `notifications_app/`, `api/`, `diary_project/settings.py`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `requirements.txt`, тесты)
- **Antigravity (`feat/v3-frontend`):** `D:\Projects\electronic-diary-system-agy` (файлы: `frontend/`)

### Согласованный API-контракт (Спринт v3)

Все эндпоинты поддерживают `SessionAuthentication` (с CSRF) и `JWTAuthentication`, доступны любому авторизованному пользователю.

#### 1. `GET /api/v1/profile/telegram/` и `PATCH /api/v1/profile/telegram/`
- `GET` (`200 OK`):
  `{ "telegram_chat_id": "673739010", "telegram_notifications_enabled": true, "bot_configured": false }`
- `PATCH` (`{ "telegram_chat_id": "673739010", "telegram_notifications_enabled": true }`) → обновляет поля текущего `request.user` и возвращает обновлённый объект.

#### 2. `POST /api/v1/profile/telegram/test/`
- Если `telegram_chat_id` пуст или `settings.TELEGRAM_BOT_TOKEN` не задан → `400 Bad Request` (`{ "detail": "..." }`).
- Если отправка через Telegram Bot API успешна → `200 OK` (`{ "ok": true, "detail": "Тестовое уведомление отправлено" }`).

#### 3. `GET /api/v1/analytics/overview/`
- Для `teacher` (по своим назначениям) и `admin` (по всем):
```json
{
  "role": "teacher",
  "summary": { "students_count": 20, "risk_count": 3, "pending_homework": 4, "avg_grade": 4.2 },
  "risk_students": [
    {
      "student_id": 5,
      "student_name": "Петров П.П.",
      "group_name": "ИС-31",
      "avg_grade": 3.1,
      "attendance_rate": 68.0,
      "reasons": ["Низкий ср. балл", "Низкая посещаемость"]
    }
  ],
  "subjects": [
    { "subject_name": "Информатика", "avg_grade": 4.3, "grades_count": 12 }
  ]
}
```
- Для `student` (только свои данные):
```json
{
  "role": "student",
  "summary": { "avg_grade": 4.5, "attendance_rate": 90.0, "unread_notifications": 2, "pending_homework": 1 },
  "subjects": [
    { "subject_name": "Информатика", "avg_grade": 4.6, "grades_count": 5 }
  ]
}
```

---

### Задачи Спринта v3

#### Codex — ветка `feat/v3-backend`
- [ ] Добавить в `users.User` поля `telegram_chat_id`, `telegram_notifications_enabled` + миграцию; в `notifications_app` добавить тип `'attendance'` и сервис `notify_user(...)` (пишет `Notification` в БД и при включённом Telegram + заданном `TELEGRAM_BOT_TOKEN` безопасно шлёт сообщение в Telegram без падения при сетевой ошибке).
- [ ] Подключить `notify_user` в `api/v1/journal.py` (новая/изменённая оценка, пропуск `absent`) и `api/v1/homework.py` (проверка/возврат ДЗ).
- [ ] Реализовать `/api/v1/profile/telegram/`, `/api/v1/profile/telegram/test/` и `/api/v1/analytics/overview/`.
- [ ] Добавить `Dockerfile`, `docker-compose.yml` (Django + Gunicorn + PostgreSQL 16), `.env.example` и чтение env-настроек (`POSTGRES_*`, `TELEGRAM_BOT_TOKEN`, `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) в `diary_project/settings.py` с дефолтным fallback на SQLite.
- [ ] Добавить автотесты (уведомления при оценке/пропуске/ДЗ, мок отправки в Telegram, `/api/v1/profile/telegram/*`, `/api/v1/analytics/overview/` для всех 3 ролей) и прогнать через `.venv\Scripts\python.exe manage.py test`.

#### Antigravity — ветка `feat/v3-frontend` (`frontend/`)
- [ ] Добавить блок настройки Telegram-уведомлений в `frontend/templates/frontend/profile.html` (`GET/PATCH /api/v1/profile/telegram/` + кнопка «Отправить тест»).
- [ ] Добавить блок «Аналитика и группа риска» в `frontend/templates/frontend/dashboard.html` (`GET /api/v1/analytics/overview/` — для преподавателя/админа и для студента).
- [ ] После мёржа веток — накатить миграции, прогнать все тесты и запушить на GitHub.
