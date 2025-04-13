from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode
import os
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession

from app.states.states import CatalogStates
from app.keyboards.catalog_manage_keyboard import catalog_manage
from app.keyboards.main_menu_keyboard import user_main_menu
from app.services.catalog_service import CatalogService
from app.decorator.injectors import inject_services

catalog_manage_router = Router()


@catalog_manage_router.callback_query(F.data == "catalog_management")
async def handle_catalog_management(callback: CallbackQuery):
    await callback.message.edit_text(
        text="🛍 <b>Управление каталогом</b>\n\nВыберите действие:",
        reply_markup=catalog_manage(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@catalog_manage_router.callback_query(F.data == "upload_catalog")
@inject_services(CatalogService)
async def upload_catalog_handler(callback: CallbackQuery, catalogservice: CatalogService):
    await callback.answer("Подготавливаю выгрузку...")

    try:
        await callback.message.edit_text("⏳ Генерация Excel-файла...", parse_mode=ParseMode.HTML)

        # Генерация Excel
        file_path = await catalogservice.create_catalog_excel()
        excel_file = FSInputFile(file_path)

        # Удаляем сообщение с клавиатурой
        try:
            await callback.message.delete()
        except:
            pass

        # Отправка Excel без клавиатуры
        await callback.message.answer_document(
            document=excel_file,
            caption="📊 Текущий каталог товаров в формате Excel."
        )

        # Клавиатура отправляется отдельно
        await callback.message.answer(
            "✅ Выгрузка каталога успешно выполнена.",
            reply_markup=catalog_manage()
        )

    except Exception as e:
        print(f"Error exporting catalog: {e}")
        await callback.message.edit_text(
            f"❌ Произошла ошибка при выгрузке каталога:\n{str(e)}",
            reply_markup=catalog_manage(),
            parse_mode=ParseMode.HTML
        )


@catalog_manage_router.callback_query(F.data == "download_catalog")
async def download_catalog_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(CatalogStates.waiting_for_excel)

    # Отправляем справку и сохраняем ID в FSM
    msg = await callback.message.edit_text(
        "📥 <b>Загрузка товаров из Excel</b>\n\n"
        "Пожалуйста, отправьте Excel файл с товарами.\n\n"
        "<b>Требуемые колонки:</b>\n"
        "• <b>name</b> (обязательно)\n"
        "• <b>price</b> (обязательно)\n"
        "• <b>description</b>\n"
        "• <b>image_url</b>\n"
        "• <b>is_available</b>\n"
        "• <b>sizes</b>\n"
        "• <b>colors</b>\n\n"
        "📝 <i>Если указан id — товар будет обновлён.</i>\n"
        "<i>Для отмены нажмите кнопку «Назад»</i>",
        reply_markup=catalog_manage(include_cancel=True),
        parse_mode=ParseMode.HTML
    )

    await state.update_data(hint_msg_id=msg.message_id)


@catalog_manage_router.callback_query(CatalogStates.waiting_for_excel, F.data == "cancel_action")
async def cancel_excel_upload(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Загрузка отменена")
    await callback.message.edit_text(
        "🛍 <b>Управление каталогом</b>\n\nВыберите действие:",
        reply_markup=catalog_manage(),
        parse_mode=ParseMode.HTML
    )


@catalog_manage_router.message(CatalogStates.waiting_for_excel)
@inject_services(CatalogService)
async def process_excel_file(
    message: Message,
    state: FSMContext,
    catalogservice: CatalogService,
    bot: Bot,
    session: AsyncSession
):
    if not message.document:
        await message.answer(
            "❌ Пожалуйста, отправьте Excel файл.",
            reply_markup=catalog_manage(include_cancel=True)
        )
        return

    file_name = message.document.file_name
    ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
    if ext not in ['xlsx', 'xls']:
        await message.answer(
            "❌ Поддерживаются только .xlsx или .xls файлы.",
            reply_markup=catalog_manage(include_cancel=True)
        )
        return

    # Удаляем справку
    data = await state.get_data()
    hint_msg_id = data.get("hint_msg_id")
    if hint_msg_id:
        try:
            await bot.delete_message(message.chat.id, hint_msg_id)
        except:
            pass

    # Сообщение о загрузке
    wait_message = await message.answer("⏳ Загружаю файл и обрабатываю данные...")

    try:
        os.makedirs(catalogservice.excel_folder, exist_ok=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file_name}", dir=catalogservice.excel_folder) as tmp:
            temp_path = tmp.name

        file = await bot.get_file(message.document.file_id)
        await bot.download_file(file.file_path, temp_path)

        result = await catalogservice.import_catalog_from_excel(temp_path)

        try:
            os.unlink(temp_path)
        except:
            pass

        await state.clear()
        await wait_message.delete()

        if result and result.get("success"):
            updated_count = result.get("updated", 0)
            await message.answer(
                f"✅ Каталог успешно обновлён.\nОбновлено товаров: {updated_count}",
                reply_markup=catalog_manage()
            )
        else:
            msg = result.get("message", "Не удалось обработать файл")
            await message.answer(
                f"❌ Ошибка при загрузке:\n{msg}",
                reply_markup=catalog_manage()
            )

    except Exception as e:
        print(f"Error processing Excel file: {e}")
        await state.clear()
        await wait_message.delete()
        await message.answer(
            f"❌ Ошибка обработки:\n{str(e)}",
            reply_markup=catalog_manage()
        )


@catalog_manage_router.callback_query(F.data == "menu:main")
async def back_to_main_menu(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "👋 <b>Главное меню</b>",
        reply_markup=user_main_menu(role="hr"),
        parse_mode=ParseMode.HTML
    )
