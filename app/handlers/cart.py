from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from app.handlers.main_menu import back_to_main_menu
from app.handlers.catalog import open_catalog

from app.services.cart_service import CartService
from app.services.catalog_service import CatalogService
from app.services.notification_service import NotificationService
from app.decorator.injectors import inject_services
from app.keyboards.cart_keyboard import (
    get_cart_keyboard,
    get_cart_item_keyboard,
    get_checkout_keyboard,
    get_empty_cart_keyboard
)
from app.utils.message_editor import update_message

cart_router = Router()


@cart_router.callback_query(F.data == "show_cart")
@inject_services(CartService, CatalogService)
async def show_cart(callback: CallbackQuery, cartservice: CartService, catalogservice: CatalogService = None):
    """Просмотр корзины"""
    user_id = callback.from_user.id
    
    # Получаем корзину пользователя
    cart = await cartservice.get_or_create_cart(user_id)
    
    if not cart.items:
        await callback.answer("Ваша корзина пуста", show_alert=True)
        await update_message(
            callback,
            text="Ваша корзина пуста",
            reply_markup=get_empty_cart_keyboard()
        )
        return
    
    # Форматируем сообщение
    text = await format_cart_message(cart)
    
    # Отправляем сообщение с клавиатурой
    await update_message(
        callback,
        text=text,
        reply_markup=get_cart_keyboard(cart)
    )
    await callback.answer()


async def format_cart_message(cart):
    """Форматирует сообщение с содержимым корзины"""
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
    return text


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
    await update_message(
        callback,
        text=text,
        reply_markup=get_cart_item_keyboard(item)
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
    
    # Обновляем корзину
    cart = await cartservice.get_or_create_cart(user_id)
    if not cart.items:
        await update_message(
            callback,
            text="Ваша корзина пуста",
            reply_markup=get_empty_cart_keyboard()
        )
    else:
        text = await format_cart_message(cart)
        await update_message(
            callback,
            text=text,
            reply_markup=get_cart_keyboard(cart)
        )


@cart_router.callback_query(F.data == "clear_cart")
@inject_services(CartService)
async def clear_cart(callback: CallbackQuery, cartservice: CartService):
    """Очистка корзины"""
    user_id = callback.from_user.id
    
    # Очищаем корзину
    await cartservice.clear_user_cart(user_id)
    
    await callback.answer("Корзина очищена")
    await update_message(
        callback,
        text="Ваша корзина пуста",
        reply_markup=get_empty_cart_keyboard()
    )


@cart_router.callback_query(F.data == "checkout_cart")
@inject_services(CartService, NotificationService)
async def checkout_cart(callback: CallbackQuery, cartservice: CartService, notificationservice: NotificationService):
    """Оформление заказа"""
    user_id = callback.from_user.id
    username = callback.from_user.username or f"user_{user_id}"
    
    # Оформляем заказ
    success, result = await cartservice.checkout_cart(user_id)
    
    if not success:
        await callback.answer(result, show_alert=True)
        return
    
    # Отправляем сообщение об успешном оформлении заказа
    text = (
        "✅ <b>Заказ успешно оформлен!</b>\n\n"
        f"Номер заказа: <b>#{result['order_id']}</b>\n"
        f"Сумма заказа: <b>{result['total_cost']} T-points</b>\n"
        f"Остаток на счету: <b>{result['remaining_balance']} T-points</b>\n\n"
        "Наш менеджер свяжется с вами для уточнения деталей доставки."
    )
    
    await update_message(
        callback,
        text=text,
        reply_markup=get_checkout_keyboard()
    )
    await callback.answer("Заказ успешно оформлен!")
    
    # Отправляем уведомление HR-менеджеру
    await notificationservice.notify_hr_about_order(
        order_id=result['order_id'],
        user_id=user_id,
        username=username,
        total_cost=result['total_cost'],
        order_items=result['order_items']
    )


@cart_router.callback_query(F.data.startswith("increase_quantity_"))
@inject_services(CartService)
async def increase_quantity(callback: CallbackQuery, cartservice: CartService):
    """Увеличение количества товара в корзине"""
    item_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    # Увеличиваем количество товара
    await cartservice.update_quantity(user_id, item_id, 1)
    await callback.answer("Количество увеличено")
    
    # Обновляем информацию о товаре
    cart = await cartservice.get_or_create_cart(user_id)
    item = next((i for i in cart.items if i.id == item_id), None)
    
    if item:
        # Если находимся в детальном просмотре товара
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
        
        await update_message(
            callback,
            text=text,
            reply_markup=get_cart_item_keyboard(item)
        )


@cart_router.callback_query(F.data.startswith("decrease_quantity_"))
@inject_services(CartService)
async def decrease_quantity(callback: CallbackQuery, cartservice: CartService):
    """Уменьшение количества товара в корзине"""
    item_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    # Уменьшаем количество товара
    await cartservice.update_quantity(user_id, item_id, -1)
    await callback.answer("Количество уменьшено")
    
    # Обновляем информацию о товаре в интерфейсе
    cart = await cartservice.get_or_create_cart(user_id)
    # Проверяем, существует ли товар ещё (мог быть удален при уменьшении до 0)
    item = next((i for i in cart.items if i.id == item_id), None)
    
    if item:
        # Если товар все еще существует, обновляем его отображение
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
        
        await update_message(
            callback,
            text=text,
            reply_markup=get_cart_item_keyboard(item)
        )
    else:
        # Если товар был удален (количество стало 0), возвращаемся к корзине
        await show_cart(callback, cartservice)
        
@cart_router.callback_query(F.data == "show_catalog")
async def redirect_to_catalog(callback: CallbackQuery):
    """Перенаправление в каталог"""
    # Импортируем обработчик show_catalog из модуля с каталогом
    await open_catalog(callback)
    await callback.answer()

@cart_router.callback_query(F.data == "start")
async def redirect_to_main(callback: CallbackQuery):
    back_to_main_menu(callback)
    await callback.answer()