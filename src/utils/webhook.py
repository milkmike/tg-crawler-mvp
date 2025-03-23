"""
Модуль для отправки данных через webhook.
"""

import json
import hashlib
import hmac
import asyncio
import time
from typing import Dict, Any, List, Optional
import aiohttp
from loguru import logger
from ..config import WEBHOOK_CONFIG
from ..database import cache
from src.config import settings

class WebhookSender:
    """Класс для отправки данных через webhook."""
    
    def __init__(self):
        """Инициализация отправщика webhook."""
        self.url = settings.webhook_url
        self.secret = settings.webhook_secret
        self.retry_count = settings.webhook_retry_count
        self.retry_delay = settings.webhook_retry_delay
        self.enabled = settings.webhook_enabled
        
        logger.debug(f"Инициализация WebhookSender: URL={self.url}, enabled={self.enabled}")
        
        self.queue = asyncio.Queue()
        self.session = None
        self.is_running = False
        self.worker_task = None
    
    async def _init_session(self):
        """Инициализация HTTP сессии."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    def _generate_signature(self, payload: str) -> str:
        """
        Генерирует подпись для webhook запроса.
        
        Args:
            payload: JSON-строка с данными
            
        Returns:
            Строка с HMAC-подписью
        """
        if not self.secret:
            return ""
        
        return hmac.new(
            self.secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def send(self, data: Dict[str, Any], event_type: str = "message") -> bool:
        """
        Отправляет данные на webhook URL.
        
        Args:
            data: Данные для отправки
            event_type: Тип события (message, channel, etc.)
            
        Returns:
            True если отправка успешна, False в противном случае
        """
        if not self.enabled:
            logger.debug(f"Webhook выключен в настройках. Пропуск отправки.")
            return False
            
        if not self.url:
            logger.warning("Webhook URL не настроен. Пропуск отправки.")
            return False
        
        await self._init_session()
        
        # Формируем payload
        payload = {
            "event_type": event_type,
            "timestamp": int(time.time()),
            "data": data
        }
        
        payload_json = json.dumps(payload)
        signature = self._generate_signature(payload_json)
        
        headers = {
            "Content-Type": "application/json",
            "X-Telegram-Crawler-Signature": signature
        }
        
        # Подготавливаем запись для логирования в MongoDB
        log_entry = {
            "event_type": event_type,
            "timestamp": int(time.time()),
            "url": self.url,
            "status": "pending",
            "attempt_count": 0,
            "error": None
        }
        
        # Импортируем соединение с MongoDB
        from src.database.db import get_db
        db = get_db()
        
        # Проверяем существование коллекции webhook_logs
        if "webhook_logs" not in db.list_collection_names():
            db.create_collection("webhook_logs")
            logger.info("Создана коллекция webhook_logs в MongoDB")
        
        # Добавляем запись в логи перед отправкой
        log_id = db.webhook_logs.insert_one(log_entry).inserted_id
        
        for attempt in range(self.retry_count):
            try:
                # Обновляем номер попытки в логах
                db.webhook_logs.update_one(
                    {"_id": log_id},
                    {"$set": {"attempt_count": attempt + 1}}
                )
                
                async with self.session.post(self.url, data=payload_json, headers=headers) as response:
                    if response.status in (200, 201, 202):
                        logger.info(f"Webhook успешно отправлен: {event_type}, статус: {response.status}")
                        
                        # Обновляем статистику в Redis
                        self._update_stats(success=True)
                        
                        # Обновляем запись в MongoDB
                        db.webhook_logs.update_one(
                            {"_id": log_id},
                            {
                                "$set": {
                                    "status": "success",
                                    "response_code": response.status,
                                    "response_text": await response.text(),
                                    "completed_at": int(time.time())
                                }
                            }
                        )
                        
                        return True
                    else:
                        logger.warning(f"Ошибка отправки webhook: {response.status}, попытка {attempt+1}/{self.retry_count}")
                        text = await response.text()
                        logger.debug(f"Ответ: {text[:200]}")
                        
                        # Обновляем ошибку в MongoDB
                        db.webhook_logs.update_one(
                            {"_id": log_id},
                            {
                                "$set": {
                                    "status": "error",
                                    "response_code": response.status,
                                    "response_text": text,
                                    "error": f"HTTP {response.status}: {text[:200]}"
                                }
                            }
                        )
                        
                        # Обновляем статистику в Redis
                        self._update_stats(success=False)
                        
                        # Делаем паузу перед следующей попыткой
                        await asyncio.sleep(self.retry_delay)
            except Exception as e:
                logger.error(f"Исключение при отправке webhook: {e}")
                
                # Обновляем ошибку в MongoDB
                db.webhook_logs.update_one(
                    {"_id": log_id},
                    {
                        "$set": {
                            "status": "error",
                            "error": str(e)
                        }
                    }
                )
                
                # Обновляем статистику в Redis
                self._update_stats(success=False)
                
                # Делаем паузу перед следующей попыткой
                await asyncio.sleep(self.retry_delay)
        
        # Если все попытки неудачны, отмечаем как неудачную отправку
        db.webhook_logs.update_one(
            {"_id": log_id},
            {
                "$set": {
                    "status": "failed",
                    "completed_at": int(time.time())
                }
            }
        )
        
        logger.error(f"Все попытки отправки webhook неудачны: {event_type}")
        return False
    
    def _update_stats(self, success: bool = True):
        """
        Обновляет статистику отправки webhook в Redis.
        
        Args:
            success: Была ли отправка успешной
        """
        try:
            # Получаем текущую дату
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            # Ключи для статистики
            total_key = f"webhook:stats:total:{date_str}"
            success_key = f"webhook:stats:success:{date_str}"
            error_key = f"webhook:stats:error:{date_str}"
            
            # Увеличиваем счетчики в Redis
            cache.incr(total_key)
            if success:
                cache.incr(success_key)
            else:
                cache.incr(error_key)
        except Exception as e:
            logger.error(f"Ошибка при обновлении статистики webhook: {e}")
    
    def start_background_worker(self):
        """Запускает фоновую задачу для отправки данных из очереди."""
        if not self.is_running:
            self.is_running = True
            self.worker_task = asyncio.create_task(self._background_worker())
    
    def stop_background_worker(self):
        """Останавливает фоновую задачу."""
        if self.is_running and self.worker_task:
            self.is_running = False
            self.worker_task.cancel()
    
    async def _background_worker(self):
        """Фоновая задача для отправки данных из очереди."""
        await self._init_session()
        
        while self.is_running:
            try:
                # Получаем данные из очереди
                data, event_type = await self.queue.get()
                
                # Отправляем данные
                await self.send(data, event_type)
                
                # Отмечаем задачу как выполненную
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в фоновой задаче webhook: {e}")
    
    async def close(self):
        """Закрывает ресурсы."""
        self.stop_background_worker()
        
        if self.session:
            await self.session.close()
            self.session = None

# Глобальный экземпляр отправщика webhook
_webhook_sender = WebhookSender()

async def send_message_data(channel_id: str, message_data: Dict[str, Any]) -> bool:
    """
    Отправляет данные о сообщении через webhook.
    
    Args:
        channel_id: ID канала
        message_data: Данные сообщения
        
    Returns:
        True если отправка успешна, False в противном случае
    """
    # Добавляем ID канала к данным
    data = {
        "channel_id": channel_id,
        "message": message_data
    }
    
    return await _webhook_sender.send(data, "message")

async def send_channel_data(channel_data: Dict[str, Any]) -> bool:
    """
    Отправляет данные о канале через webhook.
    
    Args:
        channel_data: Данные канала
        
    Returns:
        True если отправка успешна, False в противном случае
    """
    return await _webhook_sender.send(channel_data, "channel")

async def send_batch_data(batch_data: List[Dict[str, Any]], event_type: str = "batch") -> bool:
    """
    Отправляет пакет данных через webhook.
    
    Args:
        batch_data: Пакет данных
        event_type: Тип события
        
    Returns:
        True если отправка успешна, False в противном случае
    """
    return await _webhook_sender.send({"items": batch_data}, event_type)

async def test_webhook(test_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Тестирует соединение с webhook.
    
    Args:
        test_data: Тестовые данные (опционально)
        
    Returns:
        True если тест успешен, False в противном случае
    """
    if test_data is None:
        test_data = {
            "test": True,
            "timestamp": int(time.time()),
            "message": "Тестовое сообщение webhook"
        }
    
    return await _webhook_sender.send(test_data, "test")