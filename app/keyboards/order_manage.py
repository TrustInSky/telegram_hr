

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def order_management_keyboard(pending_count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📋 Посмотреть новые заказы ({pending_count})", callback_data="view_pending_orders")],
        [InlineKeyboardButton(text="✅ История выполненных", callback_data="view_completed_orders")],
        [InlineKeyboardButton(text="📊 Подробная статистика", callback_data="detailed_order_stats")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")]
    ])

def order_manage_back()->InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="⬅️ Назад в главное меню", callback_data="menu:main")]
    ])