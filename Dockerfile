FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --system --no-create-home diary \
    && mkdir /app/media /app/staticfiles \
    && chown diary:diary /app/media /app/staticfiles

COPY . .
USER diary
RUN DEBUG=True python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "diary_project.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
