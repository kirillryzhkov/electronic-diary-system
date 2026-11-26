# TASKS.md — Координация разработки (Codex + Antigravity)

Проект: `D:\Projects\electronic-diary-system` (Django 5.1 + DRF)
Основная ветка: `main`

## Завершённые спринты
- [x] **Спринт v1:** Интерактивный журнал-сетка (`/journal/`), API `/api/v1/journal/*`, `GradeAuditLog`.
- [x] **Спринт v2:** Очередь проверки ДЗ (`/homework/review-queue/`), автозапись оценки в журнал + аудит, группа риска, экспорт ведомости Excel.
- [x] **Спринт v3:** Telegram-уведомления, аналитический дашборд `/api/v1/analytics/overview/`, Docker + PostgreSQL (35/35 тестов `OK`).

---

## Спринт v4: Современный адаптивный UI/UX + Живые демо-данные + Документация

### Рабочие директории (`git worktree`)
- **Codex (`feat/v4-backend`):** `D:\Projects\electronic-diary-system-codex` (файлы: `api/management/commands/seed_demo.py`, `README.md`, тесты)
- **Antigravity (`feat/v4-frontend`):** `D:\Projects\electronic-diary-system-agy` (файлы: `frontend/`)

### Задачи Спринта v4

#### Codex — ветка `feat/v4-backend` (`api/management/`, `README.md`, `grades/tests*`)
- [ ] Прокачать `seed_demo`: создать 8–10 студентов по 2–3 группам, заполнить интерактивный журнал на текущую неделю (`Grade` с `assignment` и `lesson_date` + `Attendance`), добавить 2–3 записи в `GradeAuditLog` (реальные правки оценок с причинами), сделать 1–2 студентов в «группе риска» (низкий балл / много пропусков) и добавить 4–6 сданных ДЗ (`HomeworkSubmission`) в статусах `submitted`, `checked`, `returned`. Сохранить существующие демо-логины (`admin`, `teacher`, `teacher2`, `student1..student4` с паролем `password123`).
- [ ] Обновить `README.md`: добавить описание всех новых возможностей (интерактивный журнал `/journal/`, аудит оценок, очередь проверки ДЗ `/homework/review-queue/`, экспорт Excel, аналитика и группа риска, Telegram-уведомления, запуск через Docker Compose).
- [ ] Добавить тест на `seed_demo` (проверка, что команда идемпотентна и наполняет журнал, аудит, риск-группу и очередь ДЗ) и прогнать все тесты через `.venv\Scripts\python.exe manage.py test`.

#### Antigravity — ветка `feat/v4-frontend` (`frontend/`)
- [ ] Пересобрать дизайн-систему в `frontend/templates/frontend/base.html`: современный шрифт `Inter`, чистая палитра светлой/тёмной тем, удаление дублей/битого CSS, подсветка активного пункта навигации, аккуратный адаптивный Header + мобильный Drawer без наездов на 360px–1920px.
- [ ] Обновить `login.html` и `home.html` под современный SaaS-стиль.
- [ ] Улучшить адаптивность и UX `interactive_journal.html` (широкий контейнер на десктопе, bottom-sheet модалка на мобилке, сохранение по `Enter`), `homework_review_queue.html`, `dashboard.html` и `profile.html`.
- [ ] После мёржа веток — прогнать `seed_demo`, все тесты, проверить UI и запушить на GitHub.
