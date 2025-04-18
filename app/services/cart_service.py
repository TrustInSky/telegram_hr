from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.repositories.cart_repo import CartRepository
from app.repositories.user_repo import UserRepo
from app.repositories.order_repo import OrderRepo
from app.database.models import Cart, CartItem


class CartService:
    def __init__(self, session: AsyncSession): 
        self.session = session
        self.cart_repo = CartRepository(session)
        self.user_repo = UserRepo(session)
        self.order_repo = OrderRepo(session)

    async def get_or_create_cart(self, user_id: int) -> Cart:
        """Возвращает корзину пользователя, создавая её, если не существует."""
        return await self.cart_repo.get_cart(user_id)

    async def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1, size: str = None, color: str = None):
        """Добавляет товар в корзину"""
        cart = await self.get_or_create_cart(user_id)
        return await self.cart_repo.add_item(cart.id, product_id, quantity, size, color)

    async def remove_from_cart(self, user_id: int, cart_item_id: int):
        """Удаляет товар из корзины"""
        await self.cart_repo.remove_item(cart_item_id)
    
    async def save_cart(self, cart: Cart):
        """Сохраняем корзину в базе данных"""
        # Исправление: Не создавать новую сессию, если уже есть self.session
        self.session.add(cart)
        await self.session.commit()

    async def update_quantity(self, user_id: int, cart_item_id: int, quantity_change: int):
        """Обновляет количество товара в корзине"""
        # Исправление: Получаем текущий элемент и меняем его количество
        result = await self.session.execute(
            select(CartItem).where(CartItem.id == cart_item_id)
        )
        cart_item = result.scalars().first()
        
        if cart_item:
            new_quantity = cart_item.quantity + quantity_change
            await self.cart_repo.update_quantity(cart_item_id, new_quantity)

    async def clear_user_cart(self, user_id: int):
        """Очистка корзины пользователя"""
        cart = await self.cart_repo.get_cart(user_id)
        if cart:
            await self.cart_repo.clear_cart(cart.id)  # Удаление всех товаров из корзины
        return True

    async def get_cart_total(self, user_id: int):
        """Возвращает общую стоимость товаров в корзине"""
        cart = await self.get_or_create_cart(user_id)
        return await self.cart_repo.get_cart_total(cart.id)

    async def checkout_cart(self, user_id: int):
        """Оформить заказ из корзины"""
        try:
            async with self.session.begin():  # Начало транзакции
                # 1. Получаем корзину
                cart = await self.cart_repo.get_cart(user_id)
                if not cart.items:
                    return False, "Корзина пуста"
                    
                # 2. Рассчитываем общую стоимость
                total_cost = await self.cart_repo.get_cart_total(cart.id)
                
                # 3. Получаем данные пользователя и проверяем баланс T-points
                user = await self.user_repo.get_user(user_id)
                
                if not user:
                    return False, "Пользователь не найден"
                
                if user.tpoints < total_cost:
                    return False, f"Недостаточно T-points для оформления заказа. Требуется: {total_cost}, доступно: {user.tpoints}"
                    
                # 4. Создаем заказ
                order = await self.order_repo.create_order(
                    user_id=user_id,
                    total_cost=total_cost,
                    status="pending"  # начальный статус заказа
                )
                
                # 5. Подготовим список товаров для ответа и добавления в заказ
                order_items = []
                
                # 6. Добавляем товары из корзины в заказ
                for item in cart.items:
                    order_item = await self.order_repo.add_order_item(
                        order_id=order.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        price=item.product.price,
                        size=item.size,
                        color=item.color
                    )
                    
                    # Добавляем информацию о товаре для уведомления HR
                    order_items.append({
                        "product_name": item.product.name,
                        "product_id": item.product_id,
                        "quantity": item.quantity,
                        "price": item.product.price,
                        "size": item.size,
                        "color": item.color,
                        "subtotal": item.product.price * item.quantity
                    })
                
                # 7. Создаем транзакцию списания T-points
                await self.order_repo.create_tpoints_transaction(
                    user_id=user_id,
                    amount=-total_cost,  # отрицательная сумма для списания
                    order_id=order.id,
                    comment=f"Оплата заказа #{order.id}"
                )
                
                # 8. Списываем T-points с баланса пользователя
                await self.user_repo.update_tpoints(user_id, user.tpoints - total_cost)
                
                # 9. Очищаем корзину
                await self.cart_repo.clear_cart(cart.id)
                
                # 10. Возвращаем результат
                return True, {
                    "order_id": order.id,
                    "total_cost": total_cost,
                    "remaining_balance": user.tpoints - total_cost,
                    "order_items": order_items  # Для уведомления HR
                }
        
        except Exception as e:
            # Логирование и обработка других ошибок
            print(f"Error during checkout: {e}")
            return False, f"Произошла ошибка при оформлении заказа: {str(e)}"