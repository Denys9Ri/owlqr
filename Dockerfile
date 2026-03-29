FROM python:3.11-slim

# Встановлюємо системні залежності: gcc для пакетів та gettext для перекладів
RUN apt-get update && apt-get install -y \
    gcc \
    gettext \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Збираємо статику
RUN python manage.py collectstatic --no-input

# Компілюємо файли перекладу (.po -> .mo) під час збірки образу
RUN python manage.py compilemessages

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--chdir", "/app"]
