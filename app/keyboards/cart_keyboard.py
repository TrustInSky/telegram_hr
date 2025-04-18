from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import Cart, CartItem


def get_cart_keyboard(cart: Cart) -> InlineKeyboardMarkup:
    """Клавиатура для корзины"""
    buttons = []

    # Кнопки товаров
    for item in cart.items:
        product_name = item.product.name
        if len(product_name) > 30:
            product_name = product_name[:27] + "..."
        buttons.append([
            InlineKeyboardButton(
                text=f"{product_name} ({item.quantity} шт.)",
                callback_data=f"cart_item_{item.id}"
            )
        ])

    # Кнопки действий
    buttons.append([
        InlineKeyboardButton(text="🔄 Очистить корзину", callback_data="clear_cart"),
        InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout_cart")
    ])

    # Кнопка возврата
    buttons.append([
        InlineKeyboardButton(text="⬅️ Вернуться в каталог", callback_data="show_catalog")
    ])

    # Создание и возврат клавиатуры
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cart_item_keyboard(item: CartItem) -> InlineKeyboardMarkup:
    """Клавиатура для отдельного товара в корзине"""
    buttons = [
        [  # Кнопки изменения количества
            InlineKeyboardButton(text="➖", callback_data=f"decrease_quantity_{item.id}"),
            InlineKeyboardButton(text=f"{item.quantity}", callback_data="dummy"),
            InlineKeyboardButton(text="➕", callback_data=f"increase_quantity_{item.id}")
        ],
        [  # Удалить товар
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"remove_cart_item_{item.id}")
        ],
        [  # Назад
            InlineKeyboardButton(text="⬅️ Назад к корзине", callback_data="show_cart")
        ]
    ]
    
    # Создание и возврат клавиатуры
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_empty_cart_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для пустой корзины"""
    buttons = [
        [InlineKeyboardButton(text="🛍 Перейти в каталог", callback_data="show_catalog")],
        [InlineKeyboardButton(text="🏠 На главную", callback_data="start")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_checkout_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после оформления заказа"""
    buttons = [
        [InlineKeyboardButton(text="🛍 Вернуться в каталог", callback_data="show_catalog")],
        [InlineKeyboardButton(text="🏠 На главную", callback_data="start")]
    ]
    
    # Создаем и возвращаем клавиатуру
    return InlineKeyboardMarkup(inline_keyboard=buttons)