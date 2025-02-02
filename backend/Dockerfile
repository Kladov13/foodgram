# Используем базовый образ Python
FROM python:3.9

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем зависимости проекта (например, requirements.txt)
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта в контейнер
COPY . .


# Открываем порт для приложения (если оно запускается на 8000)
# EXPOSE 8000

# Указываем команду для запуска сервера
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "backend.wsgi"]