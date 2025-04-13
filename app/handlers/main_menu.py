from aiogram import Router, F
from aiogram.types import CallbackQuery,Message
from app.repositories.user_repo import UserRepo
from app.services.catalog import CatalogService
from app.keyboards.main_menu_keyboard import user_main_menu,back_to_main_menu
from app.utils.message_editor import update_message
from aiogram.filters import Command
from app.repositories.user_repo import UserRepo
from app.services.catalog import CatalogService
from app.decorator.injectors import inject_services


main_menu_router = Router()




@main_menu_router.message(Command("start"))
@inject_services(UserRepo)
async def start_command(message: Message, userrepo: UserRepo):
    user = await userrepo.get_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("❌ Вы не зарегистрированы в системе. Обратитесь к HR.")
        return

    role_label = {
        "hr": " (HR)",
        "admin": " (Администратор)"
    }.get(user.role, "")

    greeting = (
        f"👋 Привет, {user.fullname} {role_label}!\n"
        f"Добро пожаловать в корпоративный бот. Выберите действие из меню ниже:"
    )

    await message.answer(
        text=greeting,
        reply_markup=user_main_menu(user.role),
        parse_mode="HTML"
    )

@main_menu_router.callback_query(F.data == "menu:main")
@inject_services(UserRepo)
async def back_to_main_menu_handler(callback: CallbackQuery, userrepo: UserRepo):
    await callback.answer()
    
    # Получаем пользователя из базы данных с использованием репозитория
    user = await userrepo.get_by_telegram_id(callback.from_user.id)
    
    # Получаем роль пользователя
    user_role = user.role if user else "user"  # По умолчанию "user", если пользователь не найден
    
    await update_message(
        callback,
        text="Главное меню:", 
        reply_markup=user_main_menu(role=user_role)  # Передаем роль в функцию клавиатуры
    )