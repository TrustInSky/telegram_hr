from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup
from app.database.models import Product


def catalog_keyboard(products: list[Product]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for product in products:
        kb.button(
            text=f"{product.name} ({product.price} T)",
            callback_data=f"product_{product.id}"
        )
    kb.button(text="🔙 Назад", callback_data="menu:main")
    kb.adjust(1)
    return kb.as_markup()


def buy_product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Купить", callback_data=f"buy_{product_id}")
    kb.button(text="🔙 Назад", callback_data="back_to_catalog")
    return kb.as_markup()

def buy_or_select_keyboard(product: Product) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    if product.sizes:
        kb.button(text="📏 Выбрать размер", callback_data=f"choose_size_{product.id}")
    elif hasattr(product, "colors") and product.colors:
        kb.button(text="🎨 Выбрать цвет", callback_data=f"choose_color_{product.id}")
    else:
        kb.button(text="✅ Купить", callback_data=f"buy_{product.id}")

    kb.button(text="🔙 Назад", callback_data="back_to_catalog")
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

    desc += f"\n💰 Стоимость: <b>{product.price} T-points</b>"
    return desc