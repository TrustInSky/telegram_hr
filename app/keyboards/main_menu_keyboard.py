from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.repositories.anon_question_repo import AnonymousQuestionRepo

def user_main_menu(role: str = "user") -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    # Common buttons for all users
    kb.button(text="🛍 ТОРГИ 223 Shop", callback_data="open_catalog")
    kb.button(text="Корзина", callback_data="show_cart")
    kb.button(text="❓Задать анонимный вопрос", callback_data="ask_question")

    # Buttons for admins and HR
    if role in ("admin", "hr"):
        kb.button(text='Управление Магазином', callback_data="catalog_management")
        kb.button(text="📋 Заказы", callback_data="manage_orders")
        kb.button(text='Просмотр вопросов и предложений', callback_data='get_question')
        kb.button(text="Управление сотрудниками", callback_data='user_management')
        
        
        
    # Additional admin-only buttons
    if role == "admin":
        kb.button(text="⚙️ Настройки", callback_data="admin_settings")
    
    return kb.adjust(1).as_markup()


def back_to_main_menu(role):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="↩️ Назад", callback_data="menu:main")]
])
    return keyboard