from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.services.catalog_service import CatalogService
from app.services.order_service import OrderService
from app.repositories.order_repo import OrderRepo
from app.services.user_service import UserService
from app.repositories.user_repo import UserRepo
from app.keyboards.catalog_keyboard import buy_options_keyboard
from app.database.models import Product
from app.utils.message_editor import update_message
from aiogram.enums.parse_mode import ParseMode
from app.keyboards.order_manage_keyboard import order_management_keyboard,order_manage_back

from app.decorator.injectors import inject_services

order_router = Router()


@order_router.callback_query(F.data == "manage_orders")
@inject_services(OrderService)
async def show_order_management(callback: CallbackQuery, orderservice: OrderService):
    stats = await orderservice.get_order_summary()

    stat_text = (
        "📊 <b>Статистика заказов</b>\n\n"
        f"🆕 Новые заказы: {stats['pending']}\n"
        f"✅ Выполненные: {stats['completed']}\n"
        f"❌ Отмененные: {stats['cancelled']}\n\n"
    )

    if stats["by_departments"]:
        stat_text += "<b>Заказы по отделам:</b>\n"
        for department, count in stats["by_departments"]:
            dept_name = department if department else "Без отдела"
            stat_text += f"- {dept_name}: {count}\n"

    try:
        await callback.message.edit_text(
            stat_text,
            reply_markup=order_management_keyboard(stats["pending"]),
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            stat_text,
            reply_markup=order_management_keyboard(stats["pending"]),
            parse_mode="HTML"
        )

    await callback.answer()
    
@order_router.callback_query(F.data == "view_pending_orders")
@inject_services(OrderService)
async def view_pending_orders(callback: CallbackQuery, orderservice: OrderService):
    orders = await orderservice.get_orders_by_status("pending")

    if not orders:
        await callback.message.edit_text(
            "📭 Новых заказов нет.",
            reply_markup=order_manage_back()
            )
        return

    message_text = "🆕 <b>Новые заказы</b>:\n\n"
    for order in orders:
        message_text += (
            f"🛒 <b>Товар:</b> {order.product.name}\n"
            f"👤 <b>Сотрудник:</b> {order.user.full_name}\n"
            f"🔢 <b>Количество:</b> {order.quantity}\n"
            f"🕒 <b>Дата:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📦 <b>Статус:</b> {order.status}\n"
            f"—" * 10 + "\n"
        )
    
    await callback.message.edit_text(message_text, reply_markup=order_manage_back())
 
@order_router.callback_query(F.data == "order_manage_back")
@inject_services(OrderService)
async def back_to_order_management(callback: CallbackQuery, orderservice: OrderService):
    await callback.message.edit_reply_markup(reply_markup=order_management_keyboard(orderservice))