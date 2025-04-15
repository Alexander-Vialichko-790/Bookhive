# Используем официальный образ Python
FROM python:3.11

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт (если используешь Gunicorn)
EXPOSE 8000

# Команда запуска сервера
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
