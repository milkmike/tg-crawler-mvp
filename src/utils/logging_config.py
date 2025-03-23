"""Модуль для настройки логирования."""

import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(logger_name='telegram_crawler', log_level=logging.INFO):
    """Настройка логирования с использованием стандартного модуля logging.
    
    Args:
        logger_name (str, optional): Название логгера.
        log_level: Уровень логирования.
        
    Returns:
        Logger: Настроенный логгер.
    """
    # Создаем директорию для логов, если она не существует
    os.makedirs("logs", exist_ok=True)
    
    # Получаем или создаем логгер
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    # Если обработчики уже добавлены, не добавляем их повторно
    if logger.handlers:
        return logger
    
    # Настройка форматирования логов
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                                 datefmt='%Y-%m-%d %H:%M:%S')
    
    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Обработчик для записи в файл с ротацией
    file_handler = RotatingFileHandler(
        f"logs/{logger_name}.log",
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger