from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.database.models import Order, User
from sqlalchemy import func



class OrderRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_order(self, user_id: int, product_id: int) -> Order:
        new_order = Order(
            user_id=user_id,
            product_id=product_id,
            status="pending"
        )
        self.session.add(new_order)
        await self.session.commit()
        return new_order

    async def update_status(self, order_id: int, status: str) -> None:
        order = await self.session.get(Order, order_id)
        if order:
            order.status = status
            await self.session.commit()

    async def count_by_status(self, status: str) -> int:
        stmt = select(func.count()).select_from(Order).where(Order.status == status)
        return await self.session.scalar(stmt)

    async def get_department_stats(self) -> list[tuple[str, int]]:
        stmt = (
            select(User.department, func.count(Order.id))
            .join(User, User.telegram_id == Order.user_id)
            .where(Order.status == "pending")
            .group_by(User.department)
        )
        result = await self.session.execute(stmt)
        return result.all()
    
    
    async def get_orders_by_status(self, status: str) -> list[Order]:
        stmt = select(Order).where(Order.status == status).order_by(Order.order_date.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()