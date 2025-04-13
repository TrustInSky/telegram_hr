from aiogram.types import CallbackQuery
from aiogram import Router, F
from app.repositories.user_repo import UserRepo
from app.keyboards.main_menu_keyboard import user_main_menu
from app.utils.message_editor import update_message

tpoint_router = Router()


@tpoint_router.callback_query(F.data == "check_balance")
async def check_balance(callback: CallbackQuery, user_repo: UserRepo):
    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    await update_message(
        callback,
        text=f"💰 Ваш баланс: <b>{user.tpoints} T-points</b>",
        reply_markup=user_main_menu()
    )