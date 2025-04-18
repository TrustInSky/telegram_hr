from aiogram import Bot
from typing import List, Dict, Any
import json
import os
from datetime import datetime


class NotificationService:
    def __init__(self, bot: Bot):
        self.bot = bot
        # Здесь можно загрузить ID HR-менеджеров из конфигурации или базы данных
        self.hr_chat_ids = self._load_hr_chat_ids()
        
    def _load_hr_chat_ids(self) -> List[int]:
        """Загружает ID чатов HR-менеджеров"""
        # Можно брать из переменных окружения, конфиг-файла или базы данных
        hr_ids_str = os.getenv("HR_CHAT_IDS", "")
        if hr_ids_str:
            try:
                return [int(chat_id.strip()) for chat_id in hr_ids_str.split(",")]
            except ValueError:
                print("Error parsing HR_CHAT_IDS. Should be comma-separated list of integers.")
        
        # Можно задать ID чата HR-менеджера напрямую для тестирования
        # В реальном приложении эти ID должны быть получены из конфига или БД
        return [123456789]  # Замените на реальные ID
    
    async def notify_hr_about_order(self, order_id: int, user_id: int, username: str, 
                                   total_cost: float, order_items: List[Dict[str, Any]]):
        """Отправляет уведомление HR-менеджеру о новом заказе"""
        
        # Формируем сообщение о новом заказе
        message = self._format_order_notification(
            order_id, user_id, username, total_cost, order_items
        )
        
        # Отправляем сообщение всем HR-менеджерам
        for hr_chat_id in self.hr_chat_ids:
            try:
                await self.bot.send_message(
                    chat_id=hr_chat_id,
                    text=message,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Failed to notify HR (chat_id={hr_chat_id}): {e}")
    
    def _format_order_notification(self, order_id: int, user_id: int, username: str, 
                                  total_cost: float, order_items: List[Dict[str, Any]]) -> str:
        """Форматирует сообщение с уведомлением о заказе"""
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        
        # Шапка уведомления
        message = (
            f"🔔 <b>НОВЫЙ ЗАКАЗ #{order_id}</b> 🔔\n\n"
            f"⏰ <b>Время:</b> {current_time}\n"
            f"👤 <b>Пользователь:</b> {username} (ID: {user_id})\n\n"
            f"📋 <b>Содержимое заказа:</b>\n"
        )
        
        # Добавляем информацию о товарах
        for i, item in enumerate(order_items, 1):
            product_info = (
                f"{i}. <b>{item['product_name']}</b>\n"
                f"   Количество: {item['quantity']}\n"
                f"   Цена: {item['price']} T-points\n"
            )
            
            if item.get('size'):
                product_info += f"   Размер: {item['size']}\n"
            
            if item.get('color'):
                product_info += f"   Цвет: {item['color']}\n"
            
            product_info += f"   Сумма: {item['subtotal']} T-points\n\n"
            message += product_info
        
        # Добавляем итоговую информацию
        message += (
            f"<b>Итого:</b> {total_cost} T-points\n\n"
            f"❗️ <b>Необходимо связаться с пользователем для уточнения деталей доставки.</b>"
        )
        
        return message
    
    async def notify_user_about_order_status(self, user_id: int, order_id: int, status: str, comment: str = None):
        """Отправляет уведомление пользователю об изменении статуса заказа"""
        # Преобразуем статус в читаемый формат
        status_text = {
            "pending": "В обработке",
            "processing": "Обрабатывается",
            "shipped": "Отправлен",
            "delivered": "Доставлен",
            "cancelled": "Отменён"
        }.get(status, status)
        
        # Формируем сообщение
        message = (
            f"📦 <b>Обновление статуса заказа #{order_id}</b>\n\n"
            f"Новый статус: <b>{status_text}</b>\n"
        )
        
        if comment:
            message += f"\nКомментарий: {comment}"
        
        # Отправляем сообщение пользователю
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Failed to notify user (ID={user_id}) about order status: {e}")