from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.cart_repo import CartRepository


class CartService:
    def __init__(self, session: AsyncSession): 
        self.session = session
        self.cart_repo = CartRepository(session)

    async def get_user_cart(self, user_id: int):
        """Возвращает корзину с товарами пользователя"""
        return await self.cart_repo.get_cart(user_id)

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1, size: str = None, color: str = None):
        cart = await self.cart_repo.get_cart(user_id)
        return await self.cart_repo.add_item(cart.id, product_id, quantity, size, color)

    async def remove_from_cart(self, cart_item_id: int):
        await self.cart_repo.remove_item(cart_item_id)

    async def update_quantity(self, cart_item_id: int, quantity: int):
        await self.cart_repo.update_quantity(cart_item_id, quantity)

    async def clear_cart(self, user_id: int):
        cart = await self.cart_repo.get_cart(user_id)
        await self.cart_repo.clear_cart(cart.id)

    async def get_cart_total(self, user_id: int):
        cart = await self.cart_repo.get_cart(user_id)
        return await self.cart_repo.get_cart_total(cart.id)
