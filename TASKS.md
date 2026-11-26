# TASKS.md — Координация разработки (Codex + Antigravity)

Проект: `D:\Projects\electronic-diary-system` (Django 5.1 + DRF)
Основная ветка: `main`

## Спринт v1 (Завершён и сведён в `main`)
- [x] Интерактивный журнал-сетка (`/journal/`), API `/api/v1/journal/*`, `GradeAuditLog`, 18/18 тестов `OK`.

---

## Спринт v2: Проверка ДЗ + связь с журналом + Ведомость Excel + Группа риска

### Рабочие директории (`git worktree`)
- **Codex (`feat/v2-backend`):** `D:\Projects\electronic-diary-system-codex` (файлы: `api/`, `grades/`, `academic/` при необходимости)
- **Antigravity (`feat/v2-frontend`):** `D:\Projects\electronic-diary-system-agy` (файлы: `frontend/`)

### Согласованный API-контракт (Спринт v2)

Все эндпоинты поддерживают `SessionAuthentication` (с CSRF) и `JWTAuthentication`.
Доступ: `admin` (все назначения), `teacher` (только свои `TeachingAssignment`), `student` → `403 Forbidden`.

#### 1. `GET /api/v1/homework/submissions/?status=submitted|checked|returned|all&assignment_id=<id>`
Параметры `status` (по умолчанию `submitted`) и `assignment_id` опциональны.
Ответ (`200 OK`):
```json
{
  "counts": { "submitted": 3, "checked": 5, "returned": 1, "all": 9 },
  "submissions": [
    {
      "id": 1,
      "homework_id": 2,
      "homework_title": "Лабораторная №1",
      "deadline": "2026-11-26",
      "assignment_id": 1,
      "group_name": "ИС-31",
      "subject_name": "Информатика",
      "student_id": 5,
      "student_name": "Петров П.П.",
      "answer_text": "Ответ студента...",
      "file_url": "/media/homework_submissions/...",
      "file_name": "lab1.pdf",
      "submitted_at": "2026-11-26T10:00:00Z",
      "status": "submitted",
      "grade_value": null,
      "teacher_comment": "",
      "checked_at": null,
      "grade_id": null
    }
  ]
}
```

#### 2. `POST /api/v1/homework/submissions/<submission_id>/review/`
Request JSON:
```json
{
  "status": "checked",
  "grade_value": 5,
  "teacher_comment": "Отличная работа",
  "audit_reason": "Перепроверка ДЗ"
}
```
- Если `status == "checked"`: `grade_value` обязателен (`1..5`). Создаёт или обновляет `Grade` с `assignment=homework.assignment`, `lesson_date=homework.deadline`, `subject=homework.assignment.subject`, `student=submission.student`, `teacher=request.user`, `value=grade_value`, `comment=teacher_comment`, и сохраняет ссылку в `submission.grade`.
- Если `submission.grade` уже существовала и изменились `value` или `comment` — обязательно пишется запись в `GradeAuditLog` (с `changed_by=request.user`, `reason=audit_reason`).
- Если `status == "returned"`: `grade_value` опционален (может быть `null`), обновляется статус и `teacher_comment`.
- Ответ (`200 OK`):
```json
{
  "submission": { "...обновлённый объект submission..." },
  "counts": { "submitted": 2, "checked": 6, "returned": 1, "all": 9 }
}
```

#### 3. `GET /api/v1/journal/export/?assignment_id=<id>&week_start=YYYY-MM-DD`
- Возвращает Excel-файл `.xlsx` (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) с `Content-Disposition: attachment; filename="journal_<assignment_id>_<week_start>.xlsx"`.
- Таблица в файле: Студент, столбцы дат недели (оценка + посещаемость), Средний балл, Посещаемость %.

---

### Задачи Спринта v2

#### Codex — ветка `feat/v2-backend` (`api/`, `grades/`)
- [x] Реализовать `GET /api/v1/homework/submissions/` и `POST /api/v1/homework/submissions/<submission_id>/review/` с проверкой прав, автозаписью/обновлением `Grade` (`assignment`, `lesson_date`) и записью в `GradeAuditLog` при изменении оценки.
- [x] Реализовать `GET /api/v1/journal/export/` на базе `openpyxl` (выгрузка ведомости недели в `.xlsx`).
- [x] Добавить автотесты (права доступа, проверка ДЗ с появлением оценки в `/api/v1/journal/`, перепроверка ДЗ с записью в `GradeAuditLog`, возврат ДЗ на доработку, экспорт `.xlsx`) и прогнать через `.venv\Scripts\python.exe manage.py test`.

#### Antigravity — ветка `feat/v2-frontend` (`frontend/`)
- [x] В `interactive_journal.html`: добавить кнопку **«Скачать ведомость (.xlsx)»** (дёргает `/api/v1/journal/export/`), индикатор **«Группа риска»** (`avg_grade < 3.5` или `attendance_rate < 75%`) и переключатель фильтра «Только группа риска».
- [x] Добавить интерактивную страницу очереди проверки ДЗ `/homework/review-queue/` (`HomeworkReviewQueueView` + ссылка в шапке/журнале): вкладки `На проверке / Проверено / Возвращено`, фильтр по назначению, быстрая оценка `1..5`, комментарий, причина перепроверки, возврат на доработку и мгновенное обновление без перезагрузки.
- [x] После мёржа веток — прогнать все тесты и сквозной smoke-тест.
