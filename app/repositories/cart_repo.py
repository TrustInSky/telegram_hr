from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload

from app.database.models import Cart, CartItem, Product



class CartRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_cart(self, user_id: int):
        """Получение активной корзины пользователя или создание новой"""
        result = await self.session.execute(
            select(Cart)
            .where(Cart.user_id == user_id, Cart.is_active == True)
            .options(joinedload(Cart.items).joinedload(CartItem.product))
        )
        cart = result.scalars().first()
        
        if not cart:
            cart = Cart(user_id=user_id)
            self.session.add(cart)
            await self.session.flush()
            await self.session.refresh(cart)
        
        return cart
    
    async def add_item(self, cart_id: int, product_id: int, quantity: int = 1, size: str = None, color: str = None):
        """Добавление товара в корзину"""
        # Проверяем, есть ли уже такой товар в корзине с такими же параметрами
        result = await self.session.execute(
            select(CartItem)
            .where(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id,
                CartItem.size == size,
                CartItem.color == color
            )
        )
        cart_item = result.scalars().first()
        
        if cart_item:
            # Увеличиваем количество
            cart_item.quantity += quantity
            self.session.add(cart_item)
        else:
            # Создаем новый элемент корзины
            cart_item = CartItem(
                cart_id=cart_id,
                product_id=product_id,
                quantity=quantity,
                size=size,
                color=color
            )
            self.session.add(cart_item)
        
        await self.session.flush()
        return cart_item
    
    async def remove_item(self, cart_item_id: int):
        """Удаление товара из корзины"""
        await self.session.execute(
            delete(CartItem).where(CartItem.id == cart_item_id)
        )
        await self.session.flush()
    
    async def update_quantity(self, cart_item_id: int, quantity: int):
        """Обновление количества товара в корзине"""
        if quantity <= 0:
            await self.remove_item(cart_item_id)
            return
        
        await self.session.execute(
            update(CartItem)
            .where(CartItem.id == cart_item_id)
            .values(quantity=quantity)
        )
        await self.session.flush()
    
    async def clear_cart(self, cart_id: int):
        """Очистка корзины"""
        await self.session.execute(
            delete(CartItem).where(CartItem.cart_id == cart_id)
        )
        await self.session.flush()
    
    async def get_cart_total(self, cart_id: int):
        """Получение общей стоимости корзины"""
        result = await self.session.execute(
            select(CartItem, Product)
            .join(Product, CartItem.product_id == Product.id)
            .where(CartItem.cart_id == cart_id)
        )
        
        total = 0
        for cart_item, product in result:
            total += product.price * cart_item.quantity
        
        return total