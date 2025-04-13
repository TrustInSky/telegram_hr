from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def hr_user_management_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📤 Выгрузить список", callback_data="export_users")
    builder.button(text="📥 Загрузить список", callback_data="import_users")
    builder.button(text="Назад в меню", callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()
