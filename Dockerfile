FROM python:3.9-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов проекта
COPY requirements.txt .
COPY .env.example .

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Копирование остальных файлов проекта
COPY . .

# Создание необходимых директорий
RUN mkdir -p logs exports sessions data

# Предоставление прав на выполнение скрипта перезапуска
RUN chmod +x restart_bot.sh

# Запуск приложения
CMD ["python", "main.py"]