from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
from app.keyboards.user_manage_menu import hr_user_management_keyboard
from app.services.user import UserService
from app.utils.exel import parse_excel_file
from app.decorator.injectors import inject_services
from app.utils.message_editor import update_message

import tempfile
import os

user_manage_router = Router()

# Определение состояний
class UserStates(StatesGroup):
    awaiting_excel_upload = State()


@user_manage_router.callback_query(F.data == "user_management")
async def open_user_management(callback: CallbackQuery):
    await callback.message.edit_text(
        "Управление сотрудниками:",
        reply_markup=hr_user_management_keyboard()
    )


@user_manage_router.callback_query(F.data == "export_users")
@inject_services(UserService)
async def export_users(callback: CallbackQuery, userservice: UserService):
    # Удаляем inline-кнопки у исходного сообщения
    await callback.message.edit_reply_markup(reply_markup=None)

    # Генерируем Excel
    excel_bytes = await userservice.export_users_to_excel()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
        temp_file.write(excel_bytes)
        temp_file_path = temp_file.name

    # Отправляем Excel-файл
    await callback.message.answer_document(
        document=FSInputFile(temp_file_path, filename="employees.xlsx")
    )

    # Удаляем файл
    os.remove(temp_file_path)

    # Возвращаем пользователю прежние кнопки (например, меню управления)
    await callback.message.answer(
        text="⬇️ Файл выгружен. Что дальше?",
        reply_markup=hr_user_management_keyboard()  # <- вставь сюда свою клавиатуру
    )


@user_manage_router.callback_query(F.data == "import_users")
@inject_services(UserService)
async def request_excel_upload(callback: CallbackQuery, state: FSMContext, userservice: UserService):
    print(f"Обработка callback import_users, user_id: {callback.from_user.id}")
    try:
        # Сохраним ID сообщения с меню, чтобы потом вернуться к нему
        await state.update_data(menu_message_id=callback.message.message_id)
        
        # Удаляем меню и меняем текст
        print("Обновляем сообщение и удаляем меню")
        await update_message(callback, text="Пришлите Excel-файл с данными сотрудников (.xlsx)", reply_markup=None)
        
        print("Устанавливаем состояние awaiting_excel_upload")
        await state.set_state(UserStates.awaiting_excel_upload)
        print("Состояние установлено успешно")
    except Exception as e:
        print(f"Ошибка в request_excel_upload: {str(e)}")
        # Отправляем пользователю уведомление об ошибке
        await callback.answer(f"Произошла ошибка: {str(e)}", show_alert=True)


@user_manage_router.message(F.document, StateFilter(UserStates.awaiting_excel_upload))
@inject_services(UserService)
async def handle_excel_upload(message: Message, userservice: UserService, state: FSMContext):
    try:
        file = message.document
        
        print(f"Получен файл: {file.file_name}")

        if not file.file_name.endswith(".xlsx"):
            await message.answer("Пожалуйста, отправьте файл в формате .xlsx")
            return

        file_path = f"/tmp/{file.file_name}"
        print(f"Сохраняем файл по пути: {file_path}")
        
        try:
            await message.bot.download(file, destination=file_path)
            print(f"Файл успешно сохранен по пути: {file_path}")
            
            # Check if file actually exists after download
            if os.path.exists(file_path):
                print(f"Подтверждено: файл существует на диске, размер: {os.path.getsize(file_path)} байт")
            else:
                print(f"ОШИБКА: Файл не найден на диске после скачивания!")
                await message.answer("Ошибка: не удалось сохранить файл")
                return
        except Exception as download_error:
            print(f"Ошибка при скачивании файла: {str(download_error)}")
            await message.answer(f"Ошибка при загрузке файла: {str(download_error)}")
            return

        # Получаем сессию базы данных из репозитория пользователей
        db_session = userservice.user_repo.session
        print(f"Получена сессия БД: {db_session}")
        
        print(f"Начинаем вызов parse_excel_file с путем: {file_path}")
        # Call your function
        result = await parse_excel_file(file_path, db_session)
        print(f"Функция parse_excel_file завершена с результатом: {result}")

        if result.get("success", False):
            status_message = f"Сотрудники успешно загружены в базу. Обновлено: {result.get('updated', 0)} записей."
            if result.get("errors", 0) > 0:
                status_message += f"\nОшибок: {result.get('errors', 0)}"
                if result.get("error_messages"):
                    status_message += f"\nДетали ошибок: {', '.join(result.get('error_messages')[:3])}"
                    if len(result.get("error_messages")) > 3:
                        status_message += "... и другие"
        else:
            status_message = f"Ошибка при импорте: {result.get('message', 'Неизвестная ошибка')}"
        
        # Отправляем сообщение о результате
        await message.answer(status_message)
        
        print(f"Удаляем временный файл")
        os.remove(file_path)
        print(f"Временный файл удален")
        
        # Восстанавливаем меню в новом сообщении
        await message.answer("Панель управления пользователями:", reply_markup=hr_user_management_keyboard())
        
        await state.clear()
    except Exception as e:
        print(f"Критическая ошибка при обработке Excel-файла: {str(e)}")
        await message.answer(f"Произошла ошибка при обработке файла: {str(e)}")
        await state.clear()