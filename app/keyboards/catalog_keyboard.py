from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.models import Product


def catalog_keyboard(products: list[Product]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for product in products:
        kb.button(
            text=f"{product.name} ({product.price} T)",
            callback_data=f"product_{product.id}"
        )
    kb.button(text="🛒 Корзина", callback_data="show_cart")
    kb.button(text="🔙 Назад", callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def product_navigation_keyboard(product_id: int, products: list[Product], current_index: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    
    # Навигационные кнопки
    nav_row = []
    if current_index > 0:
        nav_row.append(InlineKeyboardButton(
            text="⬅️ Предыдущий",
            callback_data=f"product_nav_{products[current_index-1].id}_{current_index-1}"
        ))
    
    if current_index < len(products) - 1:
        nav_row.append(InlineKeyboardButton(
            text="Следующий ➡️",
            callback_data=f"product_nav_{products[current_index+1].id}_{current_index+1}"
        ))
    
    if nav_row:
        kb.row(*nav_row)
    
    # Кнопка купить
    kb.button(text="✅ Купить", callback_data=f"buy_product_show_options_{product_id}")
    
    # Кнопка назад
    kb.button(text="🔙 В каталог", callback_data="back_to_catalog")
    
    kb.adjust(2, 1, 1)
    return kb.as_markup()


def buy_options_keyboard(product: Product) -> InlineKeyboardMarkup:
    """Первый шаг - выбор параметров товара (что выбирать)"""
    kb = InlineKeyboardBuilder()
    
    has_multiple_sizes = product.sizes and len(product.sizes.split(',')) > 1
    has_multiple_colors = hasattr(product, "colors") and product.colors and len(product.colors.split(',')) > 1
    
    # Если есть множественные размеры, предлагаем их выбрать
    if has_multiple_sizes:
        kb.button(text="📏 Выбрать размер", callback_data=f"show_sizes_{product.id}")
    elif product.sizes and len(product.sizes.split(',')) == 1:
        # Если размер всего один - показываем его
        size = product.sizes.split(',')[0].strip()
        kb.button(text=f"📏 Размер: {size}", callback_data="dummy")

    # Если есть множественные цвета, предлагаем их выбрать
    if has_multiple_colors:
        kb.button(text="🎨 Выбрать цвет", callback_data=f"show_colors_{product.id}")
    elif hasattr(product, "colors") and product.colors and len(product.colors.split(',')) == 1:
        # Если цвет всего один - показываем его
        color = product.colors.split(',')[0].strip()
        kb.button(text=f"🎨 Цвет: {color}", callback_data="dummy")
    
    # Выбор количества товара
    max_quantity = product.stock if hasattr(product, "stock") and product.stock is not None else 10
    kb.button(text=f"🔢 Выбрать количество (1 из {max_quantity})", callback_data=f"show_quantity_{product.id}_1")
    
    # Кнопка добавления в корзину
    kb.button(text="🛒 Добавить в корзину", callback_data=f"add_to_cart_{product.id}_1")
    
    # Кнопка отмены
    kb.button(text="🔙 Назад", callback_data=f"product_{product.id}")
    
    kb.adjust(1)
    return kb.as_markup()


def size_selection_keyboard(product: Product, selected_size=None) -> InlineKeyboardMarkup:
    """Клавиатура для выбора размера"""
    kb = InlineKeyboardBuilder()
    
    if product.sizes:
        sizes = product.sizes.split(",")
        size_buttons = []
        
        for size in sizes:
            size = size.strip()
            # Добавляем галочку если размер выбран
            button_text = f"{size} ✅" if selected_size == size else size
            size_buttons.append(InlineKeyboardButton(
                text=button_text,
                callback_data=f"select_size_{product.id}_{size}"
            ))
        
        # Выводим кнопки размеров в ряд (по несколько в ряд)
        kb.add(*size_buttons)
        kb.adjust(min(3, len(size_buttons)))
    
    # Кнопка "Назад к опциям"
    kb.button(text="🔙 Назад к параметрам", callback_data=f"buy_product_show_options_{product.id}")
    kb.adjust(1, min(3, len(product.sizes.split(","))), 1)
    
    return kb.as_markup()


def color_selection_keyboard(product: Product, selected_color=None) -> InlineKeyboardMarkup:
    """Клавиатура для выбора цвета"""
    kb = InlineKeyboardBuilder()
    
    if hasattr(product, "colors") and product.colors:
        colors = product.colors.split(",")
        color_buttons = []
        
        for color in colors:
            color = color.strip()
            # Добавляем галочку если цвет выбран
            button_text = f"{color} ✅" if selected_color == color else color
            color_buttons.append(InlineKeyboardButton(
                text=button_text,
                callback_data=f"select_color_{product.id}_{color}"
            ))
        
        # Выводим кнопки цветов в ряд (по несколько в ряд)
        kb.add(*color_buttons)
        kb.adjust(min(3, len(color_buttons)))
    
    # Кнопка "Назад к опциям"
    kb.button(text="🔙 Назад к параметрам", callback_data=f"buy_product_show_options_{product.id}")
    kb.adjust(1, min(3, len(product.colors.split(",")) if hasattr(product, "colors") and product.colors else 0), 1)
    
    return kb.as_markup()


def quantity_selection_keyboard(product: Product, current_quantity=1) -> InlineKeyboardMarkup:
    """Клавиатура для выбора количества товара"""
    kb = InlineKeyboardBuilder()
    
    max_quantity = product.stock if hasattr(product, "stock") and product.stock is not None else 10
    
    # Показываем текущее количество и доступный максимум
    kb.button(
        text=f"Количество: {current_quantity} из {max_quantity}",
        callback_data="dummy"
    )
    
    # Кнопки +/- для изменения количества
    quantity_row = []
    
    # Кнопка уменьшения количества (если не минимум)
    if current_quantity > 1:
        quantity_row.append(InlineKeyboardButton(
            text="➖",
            callback_data=f"change_quantity_{product.id}_{current_quantity-1}"
        ))
    else:
        quantity_row.append(InlineKeyboardButton(
            text="⬛",
            callback_data="dummy"
        ))
    
    # Текущее количество
    quantity_row.append(InlineKeyboardButton(
        text=f"{current_quantity}",
        callback_data="dummy"
    ))
    
    # Кнопка увеличения количества (если не максимум)
    if current_quantity < max_quantity:
        quantity_row.append(InlineKeyboardButton(
            text="➕",
            callback_data=f"change_quantity_{product.id}_{current_quantity+1}"
        ))
    else:
        quantity_row.append(InlineKeyboardButton(
            text="⬛",
            callback_data="dummy"
        ))
    
    kb.row(*quantity_row)
    
    # Кнопка подтверждения
    kb.button(
        text="✅ Подтвердить",
        callback_data=f"confirm_quantity_{product.id}_{current_quantity}"
    )
    
    # Кнопка "Назад к опциям"
    kb.button(
        text="🔙 Назад к параметрам",
        callback_data=f"buy_product_show_options_{product.id}"
    )
    
    return kb.as_markup()


def product_final_options_keyboard(product: Product, selected_size=None, selected_color=None, quantity=1) -> InlineKeyboardMarkup:
    """Финальная клавиатура для добавления товара в корзину с выбранными параметрами"""
    kb = InlineKeyboardBuilder()
    
    # Выводим выбранные параметры (если они есть)
    options_text = []
    
    if selected_size:
        options_text.append(f"Размер: {selected_size} ✅")
    elif product.sizes and len(product.sizes.split(',')) > 1:
        options_text.append("📏 Выбрать размер")
    
    if selected_color:
        options_text.append(f"Цвет: {selected_color} ✅")
    elif hasattr(product, "colors") and product.colors and len(product.colors.split(',')) > 1:
        options_text.append("🎨 Выбрать цвет")
    
    for text in options_text:
        kb.button(text=text, callback_data=f"buy_product_show_options_{product.id}")
    
    # Выбранное количество
    max_quantity = product.stock if hasattr(product, "stock") and product.stock is not None else 10
    kb.button(text=f"Количество: {quantity} из {max_quantity} ✅", callback_data=f"show_quantity_{product.id}_{quantity}")
    
    # Кнопка добавления в корзину
    kb.button(text="🛒 Добавить в корзину", callback_data=f"add_to_cart_{product.id}_{quantity}_{selected_size}_{selected_color}")
    
    # Кнопка отмены
    kb.button(text="🔙 Назад", callback_data=f"product_{product.id}")
    
    kb.adjust(1)
    return kb.as_markup()


def after_cart_add_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍 Продолжить покупки", callback_data="back_to_catalog")
    kb.button(text="🛒 Перейти в корзину", callback_data="show_cart")
    kb.adjust(1)
    return kb.as_markup()


def format_product_description(product: Product) -> str:
    desc = f"<b>{product.name}</b>\n\n"
    if product.description:
        desc += f"{product.description}\n\n"

    if product.sizes:
        sizes = product.sizes.split(",")
        desc += f"<b>Размеры:</b> {', '.join(sizes)}\n"

    if hasattr(product, "colors") and product.colors:
        colors = product.colors.split(",")
        desc += f"<b>Цвета:</b> {', '.join(colors)}\n"
        
    if hasattr(product, "stock") and product.stock is not None:
        desc += f"<b>На складе:</b> {product.stock} шт.\n"

    desc += f"\n💰 Стоимость: <b>{product.price} T-points</b>"
    return desc