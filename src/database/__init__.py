"""Модуль для работы с базой данных MongoDB и кэшем Redis."""

# Импорт интерфейса для базы данных MongoDB
from src.database.db import (
    connect, disconnect, is_connected, save_channel, channel_exists,
    get_channels, save_messages, get_messages_by_channel, search_messages
)

# Импорт интерфейса для кэширования Redis
from src.database.redis_cache import RedisCache

# Создание глобального экземпляра кэша
cache = RedisCache()

__all__ = [
    "connect", "disconnect", "is_connected", "save_channel", "channel_exists",
    "get_channels", "save_messages", "get_messages_by_channel", "search_messages",
    "cache"
]