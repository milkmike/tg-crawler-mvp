#!/bin/bash

# Скрипт для корректного перезапуска бота

# Определение пути к PID файлу
PID_FILE="telegram_bot.pid"

# Функция для очистки перед выходом
cleanup() {
    echo "Очистка временных файлов..."
    rm -f "$PID_FILE"
    echo "Очистка завершена."
}

# Регистрация обработчика для завершения скрипта
trap cleanup EXIT

# Проверка PID файла и завершение процесса бота, если он запущен
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "Найден PID файл с PID: $PID"
    
    if ps -p $PID > /dev/null; then
        echo "Бот запущен. Завершаем процесс $PID..."
        kill -15 $PID
        sleep 1
        if ps -p $PID > /dev/null; then
            echo "Процесс не завершился. Принудительное завершение..."
            kill -9 $PID
        fi
    else
        echo "Процесс с PID $PID не найден. PID файл будет удален."
    fi
    
    rm -f "$PID_FILE"
fi

# Запуск нового экземпляра бота
echo "Запуск бота..."
python main.py

echo "Бот запущен!"