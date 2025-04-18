from app.repositories.order_repo import OrderRepo
from app.repositories.user_repo import UserRepo
from app.repositories.catalog_repo import CatalogRepo
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from app.database.models import User, Product, CartItem, Order, OrderItem, TPointsTransaction
from app.services.cart_service import CartService
from datetime import datetime
from typing import List, Optional, Tuple, Dict

class OrderService:
    def __init__(self, order_repo: OrderRepo, user_repo: UserRepo,catalog_repo:CatalogRepo):
        self.order_repo = order_repo
        self.user_repo = user_repo
        self.catalog_repo = catalog_repo


    async def create_order(self, user_id: int, product_id: int):
        return await self.order_repo.create_order(user_id, product_id)

    async def complete_order(self, order_id: int):
        return await self.order_repo.update_order_status(order_id, "completed")

    async def cancel_order(self, order_id: int):
        return await self.order_repo.update_order_status(order_id, "cancelled")

    async def get_pending_orders(self):
        return await self.order_repo.get_pending_orders()
    
    async def get_order_summary(self) -> dict:
        return {
            "pending": await self.order_repo.count_by_status("pending"),
            "completed": await self.order_repo.count_by_status("completed"),
            "cancelled": await self.order_repo.count_by_status("cancelled"),
            "by_departments": await self.order_repo.get_department_stats()
        }
        
    
    async def get_orders_by_status(self, status: str):
        return await self.order_repo.get_orders_by_status(status)
    

    def create_order_from_cart(self, user_id: int) -> Tuple[bool, str, Optional[Order]]:
        """Создать заказ из корзины пользователя"""
        # Получаем сервис корзины
        cart_service = CartService(self.db)
        
        # Получаем корзину пользователя
        cart_items = cart_service.get_user_cart(user_id)
        
        if not cart_items:
            return False, "Корзина пуста", None
        
        # Получаем пользователя
        user = self.db.query(User).filter(User.telegram_id == user_id).first()
        
        if not user:
            return False, "Пользователь не найден", None
        
        # Считаем общую сумму заказа и проверяем доступность товаров
        total_price = 0
        order_items_data = []
        
        for cart_item in cart_items:
            product = self.db.query(Product).filter(Product.id == cart_item.product_id).first()
            
            # Проверяем наличие товара
            if not product:
                return False, f"Товар с ID {cart_item.product_id} не найден", None
            
            # Проверяем доступность товара
            if not product.is_available:
                return False, f"Товар '{product.name}' недоступен для заказа", None
            
            # Проверяем наличие на складе
            if product.stock < cart_item.quantity:
                return False, f"Недостаточно товара '{product.name}' на складе. Требуется: {cart_item.quantity}, доступно: {product.stock}", None
            
            # Добавляем данные для создания OrderItem
            order_items_data.append({
                "product_id": product.id,
                "quantity": cart_item.quantity,
                "price_at_purchase": product.price
            })
            
            # Подсчет общей стоимости
            total_price += product.price * cart_item.quantity
        
        # Проверяем, хватает ли у пользователя T-поинтов
        if user.tpoints < total_price:
            return False, f"Недостаточно T-поинтов для оформления заказа. Требуется: {total_price}, у вас: {user.tpoints}", None
        
        # Создаем заказ
        new_order = Order(
            user_id=user_id,
            status="paid",  # Сразу устанавливаем статус "оплачено"
            order_date=datetime.now(),
            total_price=total_price
        )
        
        self.db.add(new_order)
        self.db.flush()  # Получаем ID заказа без коммита
        
        # Создаем элементы заказа
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                price_at_purchase=item_data["price_at_purchase"]
            )
            self.db.add(order_item)
            
            # Уменьшаем остаток товара на складе
            product = self.db.query(Product).filter(Product.id == item_data["product_id"]).first()
            product.stock -= item_data["quantity"]
        
        # Создаем транзакцию списания T-поинтов
        transaction = TPointsTransaction(
            user_id=user_id,
            amount=-total_price,  # отрицательное значение для списания
            transaction_date=datetime.now().date(),
            order_id=new_order.id,
            comment=f"Оплата заказа #{new_order.id}"
        )
        self.db.add(transaction)
        
        # Обновляем баланс пользователя
        user.tpoints -= total_price
        
        # Очищаем корзину
        cart_service.clear_cart(user_id)
        
        # Коммитим все изменения
        self.db.commit()
        
        return True, f"Заказ #{new_order.id} успешно оформлен", new_order
    
    def get_user_orders(self, user_id: int) -> List[Order]:
        """Получить все заказы пользователя"""
        return self.db.query(Order).filter(Order.user_id == user_id).order_by(Order.order_date.desc()).all()
    
    def get_order_details(self, order_id: int, user_id: int = None) -> Optional[Dict]:
        """Получить детали заказа с элементами"""
        query = self.db.query(Order)
        
        if user_id is not None:
            query = query.filter(Order.user_id == user_id)
            
        order = query.filter(Order.id == order_id).first()
        
        if not order:
            return None
        
        # Получаем элементы заказа
        order_items = self.db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        
        # Собираем детальную информацию о товарах
        items_details = []
        for item in order_items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            item_detail = {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name if product else "Товар не найден",
                "quantity": item.quantity,
                "price": item.price_at_purchase,
                "subtotal": item.price_at_purchase * item.quantity
            }
            items_details.append(item_detail)
        
        # Формируем результат
        result = {
            "order_id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "order_date": order.order_date,
            "total_price": order.total_price,
            "items": items_details
        }
        
        return result
    
    def cancel_order(self, order_id: int, user_id: int) -> Tuple[bool, str]:
        """Отменить заказ и вернуть T-поинты"""
        order = self.db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
        
        if not order:
            return False, "Заказ не найден"
        
        # Проверяем статус заказа
        if order.status not in ["pending", "paid"]:
            return False, f"Невозможно отменить заказ в статусе '{order.status}'"
        
        # Получаем пользователя
        user = self.db.query(User).filter(User.telegram_id == user_id).first()
        
        # Возвращаем товары на склад
        order_items = self.db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        for item in order_items:
            product = self.db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock += item.quantity
        
        # Создаем транзакцию возврата T-поинтов
        transaction = TPointsTransaction(
            user_id=user_id,
            amount=order.total_price,  # положительное значение для возврата
            transaction_date=datetime.now().date(),
            order_id=order.id,
            comment=f"Возврат за отмененный заказ #{order.id}"
        )
        self.db.add(transaction)
        
        # Обновляем баланс пользователя
        user.tpoints += order.total_price
        
        # Обновляем статус заказа
        order.status = "cancelled"
        
        self.db.commit()
        
        return True, f"Заказ #{order.id} отменен, {order.total_price} T-поинтов возвращены"