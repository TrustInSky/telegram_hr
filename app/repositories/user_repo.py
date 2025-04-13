from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database.models import User


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, telegram_id: int, fullname: str, username: str = None) -> User:
        new_user = User(
            telegram_id=telegram_id,
            fullname=fullname,
            username=username,
        )
        self.session.add(new_user)
        await self.session.commit()
        return new_user

    async def update_balance(self, telegram_id: int, amount: int) -> None:
        stmt = (
            update(User)
            .where(User.telegram_id == telegram_id)
            .values(tpoints=amount)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def add_points(self, telegram_id: int, delta: int) -> None:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.tpoints += delta
            await self.session.commit()

    async def set_birth_date(self, telegram_id: int, birth_date) -> None:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            user.birth_date = birth_date
            await self.session.commit()

    async def get_all_users(self) -> list[User]:
        result = await self.session.execute(select(User))
        return result.scalars().all()

    async def get_hr_by_telegram_id(self, telegram_id: int) -> User:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id, User.role == "hr")
        )
        return result.scalars().first()
    
    async def get_user_role(self, user_id: int) -> str:
        """Получает роль пользователя, если нет — возвращает 'user'."""
        user = await self.get_by_telegram_id(user_id) 
        return user.role if user else "user"
    
    async def get_users_by_status(self, is_active: bool):
        """Получает список активных или неактивных пользователей."""
        result = await self.session.scalars(select(User).where(User.is_active == is_active))
        return result.all()
    
    async def get_all_by_roles(self, roles: list[str]) -> list[User]:
        stmt = select(User).where(User.role.in_(roles))
        result = await self.session.execute(stmt)
        return result.scalars().all()