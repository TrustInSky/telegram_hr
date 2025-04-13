from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from app.services.cart_service import CartService
from app.services.catalog import CatalogService
from app.decorator.injectors import inject_services
from app.keyboards.cart_keyboard import (
    get_cart_keyboard,
    get_cart_item_keyboard,
    get_checkout_keyboard,
    get_empty_cart_keyboard
)

cart_router = Router()


@cart_router.callback_query(F.data == "show_cart")
@inject_services(CartService, CatalogService)
async def show_cart(callback: CallbackQuery, cartservice: CartService, catalogservice: CatalogService):
    """Просмотр корзины"""
    user_id = callback.from_user.id
    
    # Получаем корзину пользователя
    cart = await cartservice.get_or_create_cart(user_id)
    
    if not cart.items:
        await callback.answer("Ваша корзина пуста", show_alert=True)
        return
    
    # Форматируем сообщение
    text = "<b>🛒 Ваша корзина:</b>\n\n"
    total = 0
    
    for i, item in enumerate(cart.items, 1):
        product = item.product
        text += (
            f"{i}. <b>{product.name}</b>\n"
            f"   Количество: {item.quantity}\n"
            f"   Цена: {product.price} T-points\n"
        )
        
        if item.size:
            text += f"   Размер: {item.size}\n"
        
        if item.color:
            text += f"   Цвет: {item.color}\n"
        
        text += f"   Сумма: {product.price * item.quantity} T-points\n\n"
        total += product.price * item.quantity
    
    text += f"<b>Итого: {total} T-points</b>"
    
    # Отправляем сообщение с клавиатурой
    await callback.message.answer(
        text=text,
        reply_markup=get_cart_keyboard(cart),
        parse_mode="HTML"
    )
    await callback.answer()


@cart_router.callback_query(F.data.startswith("cart_item_"))
@inject_services(CartService)
async def show_cart_item(callback: CallbackQuery, cartservice: CartService):
    """Просмотр отдельного товара в корзине"""
    item_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    # Получаем корзину пользователя
    cart = await cartservice.get_or_create_cart(user_id)
    
    # Находим нужный товар
    item = next((i for i in cart.items if i.id == item_id), None)
    
    if not item:
        await callback.answer("Товар не найден в корзине", show_alert=True)
        return
    
    # Форматируем сообщение
    product = item.product
    text = (
        f"<b>{product.name}</b>\n\n"
        f"Цена: {product.price} T-points\n"
        f"Количество: {item.quantity}\n"
        f"Сумма: {product.price * item.quantity} T-points\n"
    )
    
    if item.size:
        text += f"Размер: {item.size}\n"
    
    if item.color:
        text += f"Цвет: {item.color}\n"
    
    # Отправляем сообщение с клавиатурой
    await callback.message.answer(
        text=text,
        reply_markup=get_cart_item_keyboard(item),
        parse_mode="HTML"
    )
    await callback.answer()


@cart_router.callback_query(F.data.startswith("remove_cart_item_"))
@inject_services(CartService)
async def remove_cart_item(callback: CallbackQuery, cartservice: CartService):
    """Удаление товара из корзины"""
    item_id = int(callback.data.split("_")[3])
    user_id = callback.from_user.id
    
    # Удаляем товар из корзины
    await cartservice.remove_from_cart(user_id, item_id)
    
    await callback.answer("Товар удален из корзины")
    
    # Обновляем отображение корзины
    await show_cart(callback, cartservice)


@cart_router.callback_query(F.data == "clear_cart")
@inject_services(CartService)
async def clear_cart(callback: CallbackQuery, cartservice: CartService):
    """Очистка корзины"""
    user_id = callback.from_user.id
    
    # Очищаем корзину
    await cartservice.clear_user_cart(user_id)
    
    await callback.answer("Корзина очищена")
    await callback.message.answer(
        "Ваша корзина пуста",
        reply_markup=get_empty_cart_keyboard()
    )


@cart_router.callback_query(F.data == "checkout_cart")
@inject_services(CartService)
async def checkout_cart(callback: CallbackQuery, cartservice: CartService):
    """Оформление заказа"""
    user_id = callback.from_user.id
    
    # Оформляем заказ
    success, result = await cartservice.checkout_cart(user_id)
    
    if not success:
        await callback.answer(result, show_alert=True)
        return
    
    # Отправляем сообщение об успешном оформлении заказа
    text = (
        "✅ <b>Заказ успешно оформлен!</b>\n\n"
        f"Сумма заказа: <b>{result['total_cost']} T-points</b>\n"
        f"Остаток на счету: <b>{result['remaining_balance']} T-points</b>\n\n"
        "Наш менеджер свяжется с вами для уточнения деталей доставки."
    )
    
    await callback.message.answer(
        text=text,
        reply_markup=get_checkout_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer("Заказ успешно оформлен!")