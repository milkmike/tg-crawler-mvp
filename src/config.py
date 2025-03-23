import os
import re
from dotenv import load_dotenv
from pydantic import BaseSettings, Field, validator

# Загрузка переменных окружения из файла .env
load_dotenv()

# Очистка значений от комментариев и лишних символов
def clean_env_value(key, default=None):
    """Очищает значение переменной окружения от комментариев и лишних символов."""
    value = os.environ.get(key)
    if value:
        # Удаляем комментарии и лишние символы
        value = re.sub(r'#.*$', '', value).strip()
        return value
    return default

# Вручную установим очищенные значения
if 'CRAWL_INTERVAL' in os.environ:
    os.environ['CRAWL_INTERVAL'] = clean_env_value('CRAWL_INTERVAL')
if 'MAX_CHANNELS' in os.environ:
    os.environ['MAX_CHANNELS'] = clean_env_value('MAX_CHANNELS')
if 'MESSAGES_LIMIT' in os.environ:
    os.environ['MESSAGES_LIMIT'] = clean_env_value('MESSAGES_LIMIT')

class Settings(BaseSettings):
    """Конфигурация приложения, загружаемая из переменных окружения."""
    
    # Telegram API настройки
    api_id: int = Field(env='API_ID')
    api_hash: str = Field(env='API_HASH')
    phone_number: str = Field(env='PHONE_NUMBER')
    bot_token: str = Field(env='BOT_TOKEN')
    
    # MongoDB настройки
    mongo_uri: str = Field(env='MONGO_URI', default='mongodb://localhost:27017/')
    mongo_db: str = Field(env='MONGO_DB', default='telegram_crawler')
    
    # Redis настройки
    redis_host: str = Field(env='REDIS_HOST', default='localhost')
    redis_port: int = Field(env='REDIS_PORT', default=6379)
    redis_db: int = Field(env='REDIS_DB', default=0)
    
    # Настройки краулера
    max_channels: int = Field(env='MAX_CHANNELS', default=100)
    messages_limit: int = Field(env='MESSAGES_LIMIT', default=1000)
    crawl_interval: int = Field(env='CRAWL_INTERVAL', default=3600)
    
    # Настройки webhook
    webhook_url: str = Field(env='WEBHOOK_URL', default='')
    webhook_secret: str = Field(env='WEBHOOK_SECRET', default='')
    webhook_retry_count: int = Field(env='WEBHOOK_RETRY_COUNT', default=3)
    webhook_retry_delay: int = Field(env='WEBHOOK_RETRY_DELAY', default=5)
    webhook_enabled: bool = Field(env='WEBHOOK_ENABLED', default=False)
    
    # Валидаторы для обработки возможных ошибок форматирования
    @validator('max_channels', 'messages_limit', 'crawl_interval', 'webhook_retry_count', 'webhook_retry_delay', pre=True)
    def parse_numeric_values(cls, v):
        if isinstance(v, str):
            # Удаляем все нецифровые символы
            cleaned = re.sub(r'[^0-9]', '', v)
            if cleaned:
                return int(cleaned)
        return v
    
    @validator('webhook_enabled', pre=True)
    def parse_boolean_values(cls, v):
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'y', 'on')
        return bool(v)
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

# Создание глобального экземпляра настроек
try:
    settings = Settings()
except Exception as e:
    # Запасной вариант со значениями по умолчанию
    print(f"Ошибка при загрузке настроек: {e}")
    
    class DefaultSettings:
        api_id = int(os.environ.get('API_ID', 0))
        api_hash = os.environ.get('API_HASH', '')
        phone_number = os.environ.get('PHONE_NUMBER', '')
        bot_token = os.environ.get('BOT_TOKEN', '')
        mongo_uri = 'mongodb://localhost:27017/'
        mongo_db = 'telegram_crawler'
        redis_host = 'localhost'
        redis_port = 6379
        redis_db = 0
        max_channels = 100
        messages_limit = 1000
        crawl_interval = 3600
        webhook_url = ''
        webhook_secret = ''
        webhook_retry_count = 3
        webhook_retry_delay = 5
        webhook_enabled = False
    
    settings = DefaultSettings()

# Конфигурация webhook для импорта в модуле webhook.py
WEBHOOK_CONFIG = {
    "url": settings.webhook_url,
    "secret": settings.webhook_secret,
    "retry_count": settings.webhook_retry_count,
    "retry_delay": settings.webhook_retry_delay,
    "enabled": settings.webhook_enabled
}