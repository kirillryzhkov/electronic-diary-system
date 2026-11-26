# TASKS.md — Координация разработки (Codex + Antigravity)

Проект: `D:\Projects\electronic-diary-system` (Django 5.1 + DRF)
Основная ветка: `main` (виртуальное окружение `.venv` и локальная `db.sqlite3` находятся в корневой папке).

## Рабочие директории (`git worktree`)
- **Codex (`feat/journal-backend`):** `D:\Projects\electronic-diary-system-codex` (файлы: `grades/`, `api/`, `diary_project/settings.py` если нужно)
- **Antigravity (`feat/journal-ui`):** `D:\Projects\electronic-diary-system-agy` (файлы: `frontend/`)

---

## Согласованный API-контракт (Интерактивный журнал + Аудит оценок)

Все эндпоинты под `/api/v1/journal/` поддерживают как `SessionAuthentication` (с CSRF для браузера), так и `JWTAuthentication`.
Доступ: `admin` (все назначения) и `teacher` (только свои `TeachingAssignment`). `student` получает `403 Forbidden`.

### 1. `GET /api/v1/journal/assignments/`
Возвращает список доступных назначений для селектора:
```json
{
  "assignments": [
    {
      "id": 1,
      "group_id": 1,
      "group_name": "ИС-21",
      "subject_id": 1,
      "subject_name": "Программирование",
      "teacher_id": 2,
      "teacher_name": "Иванов И.И."
    }
  ]
}
```

### 2. `GET /api/v1/journal/?assignment_id=<id>&week_start=YYYY-MM-DD`
Если `week_start` не передан — берётся понедельник текущей недели.
Возвращает сетку Пн–Сб (6 дней):
```json
{
  "assignment": { "id": 1, "group_id": 1, "group_name": "...", "subject_id": 1, "subject_name": "...", "teacher_name": "..." },
  "week_start": "2026-11-23",
  "week_end": "2026-11-28",
  "prev_week": "2026-11-16",
  "next_week": "2026-11-30",
  "dates": [
    { "date": "2026-11-23", "weekday": 1, "label": "Пн 23.11", "has_lesson": true, "lesson_time": "08:30–10:00" }
  ],
  "students": [
    {
      "id": 5,
      "username": "student1",
      "full_name": "Петров П.П.",
      "avg_grade": 4.5,
      "attendance_rate": 85.0,
      "cells": {
        "2026-11-23": {
          "attendance": { "id": 10, "status": "present", "comment": "" },
          "grade": { "id": 22, "value": 5, "comment": "Отлично", "teacher_name": "...", "updated_at": "2026-11-23T10:15:00Z", "audit_count": 1 }
        }
      }
    }
  ]
}
```
Если за дату нет посещаемости или оценки, соответствующее поле — `null`.

### 3. `POST /api/v1/journal/cell/`
Сохраняет посещаемость и/или оценку для ячейки **раздельно** (если поле не передано в JSON, существующее значение в БД не затирается):
```json
{
  "assignment_id": 1,
  "student_id": 5,
  "date": "2026-11-23",
  "attendance_status": "absent",
  "attendance_comment": "",
  "grade_value": 5,
  "grade_comment": "Исправлено после пересдачи",
  "audit_reason": "Пересдал лабораторную"
}
```
- `attendance_status`: `"present" | "absent" | "late" | "excused" | ""` (`""` удаляет отметку посещаемости за дату; если ключ отсутствует в JSON — не трогать).
- `grade_value`: `1..5 | null` (`null` при явном наличии ключа `grade_value` или не менять, если ключ отсутствует; если `grade_value` передан как `null`, существующая оценка удаляется или если `delete_grade: true` — удаляется с записью в аудит).
- При изменении существующей оценки (`value` или `comment`) создаётся запись в `GradeAuditLog`.
- Ответ (`200 OK`):
```json
{
  "student_id": 5,
  "date": "2026-11-23",
  "cell": { "attendance": { ... }, "grade": { ... } },
  "avg_grade": 4.6,
  "attendance_rate": 80.0
}
```

### 4. `GET /api/v1/journal/grades/<grade_id>/history/`
Возвращает историю правок оценки (от новых к старым):
```json
{
  "grade_id": 22,
  "history": [
    {
      "id": 1,
      "changed_by_name": "Иванов И.И.",
      "old_value": 4,
      "new_value": 5,
      "old_comment": "",
      "new_comment": "Исправлено после пересдачи",
      "reason": "Пересдал лабораторную",
      "changed_at": "2026-11-26T14:25:00Z"
    }
  ]
}
```

---

## Задачи и статусы

### Codex — ветка `feat/journal-backend` (`grades/`, `api/`)
- [x] Добавить в `grades.Grade` опциональные поля `assignment` (`ForeignKey` на `academic.TeachingAssignment`, `null=True, blank=True`) и `lesson_date` (`DateField`, `null=True, blank=True`) + модель `GradeAuditLog` + миграцию.
- [x] Реализовать эндпоинты `/api/v1/journal/assignments/`, `/api/v1/journal/`, `/api/v1/journal/cell/`, `/api/v1/journal/grades/<grade_id>/history/` с проверкой прав доступа (`teacher` только свои назначения и студентов своей группы, `admin` — все, `student` — 403).
- [x] Написать автотесты (права доступа, раздельное хранение оценки и посещаемости «н», запись `GradeAuditLog` при правке оценки с 4 на 5, пересчёт `avg_grade` и `attendance_rate`) и прогнать через `D:\Projects\electronic-diary-system\.venv\Scripts\python.exe manage.py test`.

### Antigravity — ветка `feat/journal-ui` (`frontend/`)
- [x] Добавить страницу `/journal/` (`InteractiveJournalView`) и ссылку в навигацию `base.html` для преподавателей и администраторов (не ломая старый `/grades/journal/`).
- [x] Реализовать `frontend/templates/frontend/interactive_journal.html`: выбор назначения, переключение недель, интерактивная сетка «студенты × дни», раздельные бейджи посещаемости и оценки, маркер правок, автоподсчёт среднего балла и % посещаемости.
- [x] Реализовать модалку/поповер ячейки: быстрый ввод оценки `1..5`, статуса `П/Н/О/У`, комментария, причины правки, сохранение через `fetch` + CSRF без перезагрузки и просмотр «Истории правок» прямо в модалке.
- [x] После мёржа веток — прогнать все тесты и проверить сквозной сценарий.
