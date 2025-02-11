# Используем официальный образ Python 3.10
FROM python:3.10

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы проекта внутрь контейнера
COPY . .

# Устанавливаем зависимости (сначала копируем requirements.txt, затем устанавливаем)
RUN pip install --no-cache-dir -r requirements.txt

# Указываем переменные окружения (при необходимости, они могут быть переопределены в Render)
ENV DATABASE_URL=postgresql+psycopg2://postgres:123@db:5432/Tech_screen

# Открываем порт 8000 для взаимодействия с FastAPI
EXPOSE 8000

# Команда, которая запускает сервер FastAPI
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
