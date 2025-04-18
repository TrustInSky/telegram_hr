from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from datetime import datetime
from typing import Optional, List

from app.database.models import User, TPointsTransaction


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # Старые методы
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получает пользователя по Telegram ID"""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_user(self, telegram_id: int, fullname: str, username: str = None) -> User:
        """Создает нового пользователя"""
        new_user = User(
            telegram_id=telegram_id,
            fullname=fullname,
            username=username,
        )
        self.session.add(new_user)
        await self.session.commit()
        return new_user
    
    async def update_balance(self, telegram_id: int, amount: int) -> None:
        """Обновляет баланс пользователя"""
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(tpoints=amount)
        )
        await self.session.execute(stmt)
        await self.session.commit()
    
    async def add_points(self, telegram_id: int, delta: int) -> None:
        """Добавляет T-points пользователю"""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.tpoints += delta
            await self.session.commit()
    
    async def set_birth_date(self, telegram_id: int, birth_date) -> None:
        """Устанавливает дату рождения пользователя"""
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.birth_date = birth_date
            await self.session.commit()
    
    async def get_all_users(self) -> List[User]:
        """Получает всех пользователей"""
        result = await self.session.execute(select(User))
        return result.scalars().all()
    
    async def get_hr_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получает HR по Telegram ID"""
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id, User.role == "hr")
        )
        return result.scalars().first()
    
    async def get_user_role(self, user_id: int) -> str:
        """Получает роль пользователя, если нет — возвращает 'user'."""
        user = await self.get_by_telegram_id(user_id)
        return user.role if user else "user"
    
    async def get_users_by_status(self, is_active: bool) -> List[User]:
        """Получает список активных или неактивных пользователей."""
        result = await self.session.scalars(select(User).where(User.is_active == is_active))
        return result.all()
    
    async def get_all_by_roles(self, roles: List[str]) -> List[User]:
        """Получает пользователей по ролям"""
        stmt = select(User).where(User.role.in_(roles))
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    # Новые методы из второго фрагмента
    async def get_user(self, user_id: int) -> Optional[User]:
        """Получает пользователя по ID (аналог get_by_telegram_id)"""
        return await self.get_by_telegram_id(user_id)
    
    async def update_tpoints(self, user_id: int, new_balance: int) -> bool:
        """Обновляет баланс T-points пользователя (более строгая версия)"""
        if new_balance < 0:
            return False
        
        user = await self.get_by_telegram_id(user_id)
        if user:
            user.tpoints = new_balance
            self.session.add(user)
            await self.session.flush()
            return True
        return False
    
    async def add_tpoints(self, user_id: int, amount: int) -> bool:
        """Добавляет T-points пользователю (аналог add_points)"""
        return await self.add_points(user_id, amount)
    
    async def get_admin_users(self) -> List[User]:
        """Получает список всех администраторов (аналог get_all_by_roles)"""
        return await self.get_all_by_roles(["admin"])
    
    async def get_hr_users(self) -> List[User]:
        """Получает список всех HR-менеджеров (аналог get_all_by_roles)"""
        return await self.get_all_by_roles(["hr"])
    
    # Новые методы для работы с транзакциями
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