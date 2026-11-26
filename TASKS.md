# TASKS.md — Координация разработки (Codex + Antigravity)

Проект: `D:\Projects\electronic-diary-system` (Django 5.1 + DRF)
Основная ветка: `main`

## Завершённые спринты
- [x] **Спринт v1–v4:** Интерактивный журнал-сетка, `GradeAuditLog`, очередь проверки ДЗ, группа риска, экспорт Excel, Telegram-уведомления, аналитический дашборд, Docker/PostgreSQL, адаптивный дизайн-редизайн и живые демо-данные (36/36 тестов `OK`).

---

## Спринт v5: QR-посещаемость на паре

### Рабочие директории (`git worktree`)
- **Codex (`feat/v5-backend`):** `D:\Projects\electronic-diary-system-codex` (файлы: `academic/`, `api/`, `grades/test*`)
- **Antigravity (`feat/v5-frontend`):** `D:\Projects\electronic-diary-system-agy` (файлы: `frontend/`)

### Согласованный API-контракт (QR-посещаемость)

Все эндпоинты поддерживают `SessionAuthentication` (с CSRF) и `JWTAuthentication`.

#### 1. Модель `academic.AttendanceQRSession`
- `token`: `CharField(max_length=64, unique=True, db_index=True)` (одноразовый криптостойкий токен `secrets.token_urlsafe(24)`)
- `assignment`: `ForeignKey(TeachingAssignment, on_delete=models.CASCADE, related_name='qr_sessions')`
- `date`: `DateField`
- `created_by`: `ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)`
- `created_at`: `DateTimeField(auto_now_add=True)`
- `expires_at`: `DateTimeField`
- `is_active`: `BooleanField(default=True)`

#### 2. `POST /api/v1/attendance/qr/create/` (только `teacher` своего назначения и `admin`; `student` → `403`)
- Request JSON: `{ "assignment_id": 1, "date": "2026-11-26", "ttl_minutes": 5 }` (`ttl_minutes`: `1..30`, default `5`).
- Деактивирует предыдущие активные QR-сессии на ту же пару `(assignment, date)`.
- Response `201 Created`:
```json
{
  "token": "...",
  "assignment_id": 1,
  "group_name": "ИС-31",
  "subject_name": "Информатика",
  "date": "2026-11-26",
  "expires_at": "2026-11-26T15:20:00Z",
  "checkin_path": "/attendance/qr/checkin/<token>/",
  "total_students": 4,
  "checked_in_count": 0
}
```

#### 3. `GET /api/v1/attendance/qr/<token>/status/` (`teacher` этого назначения и `admin`)
- Response `200 OK`:
```json
{
  "token": "...",
  "is_active": true,
  "is_expired": false,
  "expires_at": "2026-11-26T15:20:00Z",
  "total_students": 4,
  "checked_in_count": 2,
  "checked_in_students": [
    { "id": 5, "full_name": "Петров П.П.", "status": "present" }
  ]
}
```

#### 4. `POST /api/v1/attendance/qr/<token>/close/` (`teacher` этого назначения и `admin`)
- Деактивирует сессию (`is_active = False`), возвращает `{ "ok": true, "is_active": false }`.

#### 5. `POST /api/v1/attendance/qr/<token>/checkin/` (только `student` из группы этого `assignment`)
- Если пользователь не `student` или не из `assignment.group` → `403 Forbidden` (`{ "detail": "..." }`).
- Если сессия не найдена → `404`; если закрыта (`is_active=False`) или истекла (`now > expires_at`) → `410 Gone` (`{ "detail": "QR-код недействителен или истёк" }`).
- Ставит/обновляет `Attendance(student=user, assignment=session.assignment, date=session.date, status='present')`, не затрагивая `Grade`.
- Response `200 OK`:
```json
{
  "ok": true,
  "status": "present",
  "already_checked_in": false,
  "subject_name": "Информатика",
  "group_name": "ИС-31",
  "date": "2026-11-26",
  "detail": "Присутствие отмечено!"
}
```

---

### Задачи Спринта v5

#### Codex — ветка `feat/v5-backend` (`academic/`, `api/`, тесты)
- [x] Добавить модель `AttendanceQRSession` в `academic/models.py` + миграцию.
- [x] Реализовать 4 эндпоинта `/api/v1/attendance/qr/create/`, `/status/`, `/close/`, `/checkin/` с проверкой прав, TTL и идемпотентным check-in (с сохранением оценок).
- [x] Написать автотесты (создание QR, права преподавателя/админа/студента, check-in студента своей группы, запрет чужой группы `403`, истёкший/закрытый QR `410`, повторный check-in, сохранность оценки) и прогнать все тесты через `.venv\Scripts\python.exe manage.py test`.

#### Antigravity — ветка `feat/v5-frontend` (`frontend/`)
- [x] В `interactive_journal.html`: добавить кнопку **«QR на пару»** и модалку с генерацией QR-кода, живым таймером, счётчиком «Отметились X из Y», списком студентов в реальном времени (polling `/status/`), копированием ссылки и кнопкой «Завершить приём».
- [x] Добавить страницу `/attendance/qr/checkin/<str:token>/` (`QRCheckinView` + `frontend/templates/frontend/qr_checkin.html`) для отметки присутствия студентом с телефона.
- [x] После мёржа веток — накатить миграцию, прогнать все тесты и запушить на GitHub.
