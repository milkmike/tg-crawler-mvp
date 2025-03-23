"""Модуль для настройки логирования."""

import logging
import sys
import os
from loguru import logger

def setup_logger(name="telegram_crawler", level="INFO"):
    """Настройка логирования через loguru.
    
    Args:
        name (str, optional): Название логгера.
        level (str, optional): Уровень логирования.
        
    Returns:
        логгер loguru.
    """
    # Создаем директорию для логов, если она не существует
    os.makedirs("logs", exist_ok=True)
    
    # Удаляем стандартный обработчик
    logger.remove()
    
    # Добавляем обработчик для вывода в консоль
    logger.add(sys.stderr, level=level, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # Добавляем обработчик для записи в файл
    logger.add(
        f"logs/{name}.log",
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="1 day",
        retention="7 days"
    )
    
    # Настройка loguru для перехвата стандартных логов Python
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Получаем соответствующий loguru-уровень
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            
            # Найдем вызывающий кадр
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            
            # Логируем сообщение
            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
    
    # Настраиваем перехват для стандартных библиотек Python
    logging.basicConfig(handlers=[InterceptHandler()], level=0)
    
    # Настраиваем перехват для логов библиотек
    for logger_name in ["telethon", "pymongo", "telegram"]:
        module_logger = logging.getLogger(logger_name)
        module_logger.handlers = [InterceptHandler()]
        module_logger.propagate = False
    
    return logger