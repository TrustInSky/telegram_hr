from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import Cart, CartItem


def get_cart_keyboard(cart: Cart) -> InlineKeyboardMarkup:
    """Клавиатура для корзины"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    # Добавляем кнопки для каждого товара
    for item in cart.items:
        product_name = item.product.name
        if len(product_name) > 30:
            product_name = product_name[:27] + "..."
        
        keyboard.add(
            InlineKeyboardButton(
                text=f"{product_name} ({item.quantity} шт.)",
                callback_data=f"cart_item_{item.id}"
            )
        )
    
    # Добавляем кнопки действий
    keyboard.row(
        InlineKeyboardButton(text="🔄 Очистить корзину", callback_data="clear_cart"),
        InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout_cart")
    )
    
    # Кнопка возврата в каталог
    keyboard.add(
        InlineKeyboardButton(text="⬅️ Вернуться в каталог", callback_data="show_catalog")
    )
    
    return keyboard


def get_cart_item_keyboard(item: CartItem) -> InlineKeyboardMarkup:
    """Клавиатура для отдельного товара в корзине"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Кнопки изменения количества
    keyboard.row(
        InlineKeyboardButton(text="➖", callback_data=f"decrease_quantity_{item.id}"),
        InlineKeyboardButton(text=f"{item.quantity}", callback_data="dummy"),
        InlineKeyboardButton(text="➕", callback_data=f"increase_quantity_{item.id}")
    )
    
    # Кнопка удаления
    keyboard.add(
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"remove_cart_item_{item.id}")
    )
    
    # Кнопки навигации
    keyboard.row(
        InlineKeyboardButton(text="⬅️ Назад к корзине", callback_data="show_cart")
    )
    
    return keyboard


def get_empty_cart_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для пустой корзины"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="🛍 Перейти в каталог", callback_data="show_catalog"),
        InlineKeyboardButton(text="🏠 На главную", callback_data="start")
    )
    return keyboard


def get_checkout_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после оформления заказа"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton(text="🛍 Вернуться в каталог", callback_data="show_catalog"),
        InlineKeyboardButton(text="🏠 На главную", callback_data="start")
    )
    return keyboard