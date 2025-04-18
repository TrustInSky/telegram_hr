from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, insert
from sqlalchemy.orm import joinedload
from datetime import datetime
from typing import List, Optional, Dict

from app.database.models import Order, OrderItem, Product, User, TPointsTransaction


class OrderRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # Основные методы работы с заказами
    async def create_order(self, user_id: int, total_cost: float, status: str = "pending") -> Order:
        """Создает новый заказ"""
        order = Order(
            user_id=user_id,
            total_cost=total_cost,
            status=status,
            created_at=datetime.now()
        )
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order
    
    async def add_order_item(self, order_id: int, product_id: int, quantity: int, 
                            price: float, size: str = None, color: str = None) -> OrderItem:
        """Добавляет товар в заказ"""
        order_item = OrderItem(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            price=price,
            size=size,
            color=color
        )
        self.session.add(order_item)
        await self.session.flush()
        await self.session.refresh(order_item)
        return order_item
    
    async def get_order(self, order_id: int) -> Optional[Order]:
        """Получает заказ по ID с загрузкой товаров"""
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product)
            )
        )
        return result.scalars().first()
    
    async def get_user_orders(self, user_id: int) -> List[Order]:
        """Получает все заказы пользователя"""
        result = await self.session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product)
            )
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновляет статус заказа"""
        order = await self.get_order(order_id)
        if order:
            order.status = status
            order.updated_at = datetime.now()
            self.session.add(order)
            await self.session.flush()
            return True
        return False
    
    # Методы для работы с транзакциями
    async def create_tpoints_transaction(self, user_id: int, amount: int, 
                                        order_id: int = None, product_id: int = None, 
                                        comment: str = None) -> TPointsTransaction:
        """Создает новую транзакцию T-points"""
        transaction = TPointsTransaction(
            user_id=user_id,
            amount=amount,
            transaction_date=datetime.now().date(),
            order_id=order_id,
            product_id=product_id,
            comment=comment
        )
        
        self.session.add(transaction)
        await self.session.flush()
        return transaction
    
    # Дополнительные методы
    async def cancel_order(self, order_id: int) -> Optional[Order]:
        """Отменяет заказ и возвращает средства пользователю"""
        order = await self.get_order(order_id)
        if not order:
            return None
            
        if order.status in ["delivered", "completed"]:
            raise ValueError(f"Невозможно отменить заказ в статусе '{order.status}'")
            
        await self.update_order_status(order_id, "cancelled")
        
        # Возвращаем средства
        user = await self.session.get(User, order.user_id)
        if user:
            user.tpoints += order.total_cost
            self.session.add(user)
            await self.session.flush()
            
        return order
    
    async def count_by_status(self, status: str) -> int:
        """Считает количество заказов по статусу"""
        result = await self.session.execute(
            select(func.count()).where(Order.status == status)
        )
        return result.scalar_one()
    
    async def get_pending_orders(self) -> List[Order]:
        """Получает все ожидающие заказы"""
        result = await self.session.execute(
            select(Order)
            .where(Order.status == "pending")
            .options(
                joinedload(Order.items).joinedload(OrderItem.product)
            )
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()
    
    async def get_department_stats(self) -> Dict[str, int]:
        """Получает статистику заказов по отделам"""
        result = await self.session.execute(
            select(
                User.department,
                func.count(Order.id).label('count')
            )
            .join(Order.user)
            .where(Order.status != "cancelled")
            .group_by(User.department)
        )
        
        return {row.department or "Неизвестно": row.count for row in result}
    
    async def get_orders_by_status(self, status: str) -> List[Order]:
        """Получает все заказы с определенным статусом"""
        result = await self.session.execute(
            select(Order)
            .where(Order.status == status)
            .options(
                joinedload(Order.items).joinedload(OrderItem.product),
                joinedload(Order.user)
            )
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()