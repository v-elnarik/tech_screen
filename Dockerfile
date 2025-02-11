# Используем официальный образ Python 3.10
FROM python:3.10

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы проекта внутрь контейнера
COPY . .

# Устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт 8000 для взаимодействия с FastAPI
EXPOSE 8000

# Устанавливаем Supervisor
RUN pip install supervisor

# Копируем конфигурацию Supervisor
COPY supervisord.conf /etc/supervisord.conf

# Запускаем Supervisor
CMD ["supervisord", "-c", "/etc/supervisord.conf"]
