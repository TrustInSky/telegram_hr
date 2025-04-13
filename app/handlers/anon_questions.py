from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from app.keyboards.anonymous_question_keyboard import anon_questions_menu_keyboard,mark_status_keyboard,anon_questions_menu_keyboard,confirm_question_keyboard
from app.keyboards.main_menu_keyboard import user_main_menu
from app.states.states import AnonymousQuestionStates
from app.repositories.anon_question_repo import AnonymousQuestionRepo
from app.services.question_service import AnonymousQuestionService
from app.repositories.user_repo import UserRepo
from app.utils.text import anonymous_block_description
from app.utils.exel import anon_question_create_excel_file
from app.decorator.injectors import inject_services
import asyncio
import tempfile
import os
from aiogram.types import FSInputFile


anon_questions_router = Router()

@anon_questions_router.callback_query(F.data == "ask_question")
async def start_anonymous_question(callback: CallbackQuery, state: FSMContext):
    msg = await callback.message.edit_text(
        anonymous_block_description(),
        reply_markup=None,
        parse_mode="HTML"
    )
    # Сохраняем ID сообщения с описанием
    await state.update_data(description_msg_id=msg.message_id)

    await state.set_state(AnonymousQuestionStates.waiting_for_text)


@anon_questions_router.message(AnonymousQuestionStates.waiting_for_text)
async def receive_question_text(message: Message, state: FSMContext):
    data = await state.get_data()
    description_msg_id = data.get("description_msg_id")

    if description_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=description_msg_id)
        except Exception as e:
            print(f"Не удалось удалить описание вопроса: {e}")

    question_text = message.text.strip()
    await state.update_data(question_text=question_text)

    sent_msg = await message.answer(
        f"📝 Ваш вопрос:\n\n<code>{question_text}</code>\n\n"
        f"Проверьте текст и выберите действие ниже:",
        reply_markup=confirm_question_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(confirm_message_id=sent_msg.message_id)

    await state.set_state(AnonymousQuestionStates.confirmation)


@anon_questions_router.callback_query(StateFilter(AnonymousQuestionStates.confirmation), F.data == "edit_question")
async def edit_question(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ Введите новый текст вопроса:")
    await state.set_state(AnonymousQuestionStates.waiting_for_text)


@anon_questions_router.callback_query(StateFilter(AnonymousQuestionStates.confirmation), F.data == "cancel_question")
async def cancel_question(callback: CallbackQuery, state: FSMContext, userrepo: UserRepo):
    user = await userrepo.get_by_telegram_id(callback.from_user.id)
    await callback.message.edit_text("🔙 Возвращаюсь в главное меню.", reply_markup=user_main_menu(user.role))
    await state.clear()


@anon_questions_router.callback_query(F.data == "submit_question")
@inject_services(AnonymousQuestionService, UserRepo)
async def submit_question(
    callback: CallbackQuery,
    state: FSMContext,
    anonymousquestionservice: AnonymousQuestionService,
    userrepo: UserRepo,
   
):
    data = await state.get_data()
    text = data.get("question_text")
    user = await userrepo.get_by_telegram_id(callback.from_user.id)
    if not text:
        await callback.answer("❗ Не удалось отправить вопрос. Попробуйте заново.", show_alert=True)
        await callback.message.edit_text("Что-то пошло не так. Пожалуйста, введите текст вопроса ещё раз:")
        await state.set_state(AnonymousQuestionStates.waiting_for_text)
        return

    # ✅ 1. Сохраняем вопрос в базу
    question = await anonymousquestionservice.create_question(text)

    # ✅ 2. Уведомляем пользователя сразу
    await callback.message.edit_text(
        "✅ Ваш анонимный вопрос отправлен.",
        reply_markup=user_main_menu(user.role)
    )
    await state.clear()



@anon_questions_router.callback_query(F.data == "get_question")
async def handle_anon_questions_menu(callback: CallbackQuery, as_new_message: bool = False):
   
    kb = anon_questions_menu_keyboard()

    text = "📋 Меню управления анонимными вопросами"

    if as_new_message:
        await callback.message.answer(text, reply_markup=kb)
    else:
        await callback.message.edit_text(text, reply_markup=kb)


@anon_questions_router.callback_query(F.data == "view_new_questions")
@inject_services(AnonymousQuestionRepo)
async def handle_view_new_questions(callback: CallbackQuery, anonymousquestionrepo: AnonymousQuestionRepo):
    question = await anonymousquestionrepo.get_next_unread()
    if not question:
        await callback.answer("Нет новых непрочитанных вопросов.", show_alert=True)
        await callback.message.edit_text(
            "📭 <b>Нет новых непрочитанных вопросов</b>\n\n"
            "Выберите другое действие:",
            reply_markup=anon_questions_menu_keyboard(), 
            parse_mode="HTML"
        )
        return

    await callback.message.edit_text(
        f"📨 <b>Анонимный вопрос</b>:\n\n<code>{question.question_text}</code>",
        reply_markup=mark_status_keyboard(question.id),
        parse_mode="HTML"
    )
    
@anon_questions_router.callback_query(F.data.startswith("mark_read:"))
@inject_services(AnonymousQuestionRepo)
async def mark_question_read(callback: CallbackQuery, anonymousquestionrepo: AnonymousQuestionRepo):
    question_id = int(callback.data.split(":")[1])
    await anonymousquestionrepo.update_status(question_id, "read")
    await callback.answer("Отмечено как прочитано.")
    
    # Возвращаемся к меню вопросов
    await handle_anon_questions_menu(callback)

@anon_questions_router.callback_query(F.data.startswith("mark_later:"))
@inject_services(AnonymousQuestionRepo)
async def mark_question_later(callback: CallbackQuery, anonymousquestionrepo: AnonymousQuestionRepo):
    question_id = int(callback.data.split(":")[1])
    await anonymousquestionrepo.update_status(question_id, "later")
    await callback.answer("Отложено.")
    
    # Возвращаемся к меню вопросов
    await handle_anon_questions_menu(callback)

@anon_questions_router.callback_query(F.data == "export_questions_excel")
@inject_services(AnonymousQuestionRepo)
async def handle_export_excel(callback: CallbackQuery, anonymousquestionrepo: AnonymousQuestionRepo):
    try:
        # Получаем все вопросы
        questions = await anonymousquestionrepo.get_all_questions()

        if not questions:
            await callback.answer("Нет вопросов для выгрузки.", show_alert=True)
            return

        # Генерируем Excel
        excel_data = anon_question_create_excel_file(questions)

        if not isinstance(excel_data, bytes):
            await callback.answer("Ошибка: неверный формат данных", show_alert=True)
            return

        # Сохраняем временно
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            temp_file.write(excel_data)
            temp_path = temp_file.name

        # Удаляем старое сообщение с кнопками (если не важно сохранять)
        await callback.message.delete()

        # Отправляем Excel
        document = FSInputFile(temp_path, filename="anonymous_questions.xlsx")
        await callback.message.answer_document(
            document,
            caption=f"📥 Выгрузка всех анонимных вопросов ({len(questions)} шт.)"
        )

        await callback.answer("Файл успешно создан ✅")

    except Exception as e:
        print(f"[Ошибка выгрузки Excel] {str(e)}")
        await callback.answer("Ошибка при создании Excel-файла 😕", show_alert=True)

    finally:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)

        # Отправляем новое меню с клавиатурой
        await callback.message.answer(
            "📋 <b>Меню анонимных вопросов</b>\n\n"
            "Выберите действие:",
            reply_markup=anon_questions_menu_keyboard(),
            parse_mode="HTML"
        )