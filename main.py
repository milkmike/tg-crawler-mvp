#!/usr/bin/env python3
"""
Telegram Crawler MVP - Бот для сбора данных из Telegram каналов.
"""

import os
import asyncio
from loguru import logger
from src.bot import bot_handler
from src.utils.logger import setup_logger

def check_environment():
    """Проверка наличия необходимых файлов и директорий."""
    # Проверяем наличие файла .env
    if not os.path.exists(".env"):
        logger.warning("Файл .env не найден. Создайте его на основе .env.example")
        return False
    
    # Создаем необходимые директории
    os.makedirs("sessions", exist_ok=True)
    os.makedirs("exports", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    return True

def main():
    """Основная функция запуска программы."""
    # Настраиваем логирование
    setup_logger()
    
    logger.info("Запуск Telegram Crawler MVP...")
    
    # Проверяем окружение
    if not check_environment():
        logger.error("Ошибка при проверке окружения. Завершение работы.")
        return
    
    try:
        # Запускаем бота
        bot_handler.start_bot()
    except KeyboardInterrupt:
        logger.info("Получен сигнал прерывания. Завершение работы.")
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}")
    finally:
        logger.info("Завершение работы Telegram Crawler MVP.")

if __name__ == "__main__":
    main()