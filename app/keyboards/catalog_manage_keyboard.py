

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def catalog_manage(include_cancel: bool = False):
    """Keyboard for catalog management"""
    buttons = [
        [
            InlineKeyboardButton(text="📤 Выгрузить список товаров", callback_data="upload_catalog"),
            InlineKeyboardButton(text="📥 Загрузить список товаров", callback_data="download_catalog")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="menu:main")
        ]
    ]
    
    if include_cancel:
        buttons.insert(1, [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_action")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)