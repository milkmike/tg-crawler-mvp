"""Модуль для обработки и логирования ошибок."""

import time
import functools
from dataclasses import dataclass
from typing import Callable, Any, TypeVar, Optional, Union, Dict
from loguru import logger

# Типы для аннотаций
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

@dataclass
class RetrySettings:
    """Настройки повторных попыток при возникновении ошибок."""
    max_retries: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0
    exceptions_to_retry: tuple = (Exception,)

def with_retry(settings: Optional[RetrySettings] = None) -> Callable[[F], F]:
    """Декоратор для автоматического повтора функции при возникновении ошибок.
    
    Args:
        settings: Настройки повторных попыток.
        
    Returns:
        Декоратор для функции.
    """
    if settings is None:
        settings = RetrySettings()
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            delay = settings.initial_delay
            
            for attempt in range(settings.max_retries + 1):
                try:
                    if attempt > 0:
                        logger.debug(f"Повторная попытка {attempt}/{settings.max_retries} для {func.__name__} через {delay:.1f}с")
                        time.sleep(delay)
                        
                    return func(*args, **kwargs)
                except settings.exceptions_to_retry as e:
                    last_exception = e
                    logger.warning(f"Ошибка в {func.__name__}. Попытка {attempt + 1}/{settings.max_retries + 1}. Ошибка: {e}")
                    
                    # Увеличиваем задержку для следующей попытки
                    delay = min(delay * settings.backoff_factor, settings.max_delay)
                except Exception as e:
                    # Если это не ошибка из списка для повтора, пробрасываем дальше
                    logger.error(f"Неожиданная ошибка в {func.__name__}: {e}")
                    raise
            
            # Если все попытки неудачны, вызываем последнее исключение
            logger.error(f"Все попытки выполнить {func.__name__} неудачны. Последняя ошибка: {last_exception}")
            raise last_exception
        
        return wrapper
    return decorator

def async_with_retry(settings: Optional[RetrySettings] = None) -> Callable[[F], F]:
    """Декоратор для автоматического повтора асинхронной функции при возникновении ошибок.
    
    Args:
        settings: Настройки повторных попыток.
        
    Returns:
        Декоратор для асинхронной функции.
    """
    if settings is None:
        settings = RetrySettings()
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            import asyncio
            
            last_exception = None
            delay = settings.initial_delay
            
            for attempt in range(settings.max_retries + 1):
                try:
                    if attempt > 0:
                        logger.debug(f"Повторная попытка {attempt}/{settings.max_retries} для {func.__name__} через {delay:.1f}с")
                        await asyncio.sleep(delay)
                        
                    return await func(*args, **kwargs)
                except settings.exceptions_to_retry as e:
                    last_exception = e
                    logger.warning(f"Ошибка в {func.__name__}. Попытка {attempt + 1}/{settings.max_retries + 1}. Ошибка: {e}")
                    
                    # Увеличиваем задержку для следующей попытки
                    delay = min(delay * settings.backoff_factor, settings.max_delay)
                except Exception as e:
                    # Если это не ошибка из списка для повтора, пробрасываем дальше
                    logger.error(f"Неожиданная ошибка в {func.__name__}: {e}")
                    raise
            
            # Если все попытки неудачны, вызываем последнее исключение
            logger.error(f"Все попытки выполнить {func.__name__} неудачны. Последняя ошибка: {last_exception}")
            raise last_exception
        
        return wrapper
    return decorator

def log_exceptions(func: F) -> F:
    """Декоратор для логирования исключений, возникающих в функции.
    
    Args:
        func: Исходная функция.
        
    Returns:
        Обернутая функция.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Исключение в {func.__name__}: {e}")
            raise
    return wrapper

def async_log_exceptions(func: F) -> F:
    """Декоратор для логирования исключений, возникающих в асинхронной функции.
    
    Args:
        func: Исходная асинхронная функция.
        
    Returns:
        Обернутая асинхронная функция.
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Исключение в асинхронной функции {func.__name__}: {e}")
            raise
    return wrapper