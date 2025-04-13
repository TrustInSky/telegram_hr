from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def confirm_question_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="submit_question")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit_question")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main")]
    ])


def anon_questions_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Посмотреть новые вопросы", callback_data="view_new_questions")],
        [InlineKeyboardButton(text="📊 Выгрузить все в Excel", callback_data="export_questions_excel")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main")]
    ])

def mark_status_keyboard(question_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Прочитано", callback_data=f"mark_read:{question_id}")],
        [InlineKeyboardButton(text="⏱ Прочитать позже", callback_data=f"mark_later:{question_id}")],
        [InlineKeyboardButton(text="🔙 К меню вопросов", callback_data="get_question")]
    ])

def no_questions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К меню вопросов", callback_data="get_question")]
    ])