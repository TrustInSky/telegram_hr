import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from app.middlewares.group_membership import GroupMembershipMiddleware
from app.middlewares.database import DatabaseMiddleware
from app.database.database import init_db, SessionLocal

# Import models to register them with Base
from app.database.models import User, TPointsTransaction, Product, Order, AnonymousQuestion

# Routers

from app.handlers.main_menu import main_menu_router
from app.handlers.catalog import catalog_router
from app.handlers.orders import order_router
from app.handlers.user_manage import user_manage_router
from app.handlers.anon_questions import anon_questions_router
from app.handlers.catalog_manage import catalog_manage_router

async def on_startup(dispatcher: Dispatcher):
    print("✅ Бот запущен")

async def on_shutdown(dispatcher: Dispatcher):
    print("❌ Бот остановлен")

async def main():
    load_dotenv()
    # Initialize database
    await init_db()
    bot = Bot(token=os.getenv("TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DatabaseMiddleware(SessionLocal))

    # middlewares
    dp.callback_query.middleware(GroupMembershipMiddleware(target_group_id=os.getenv("GROUP_ID")))

    dp.message.middleware(GroupMembershipMiddleware( target_group_id=os.getenv("GROUP_ID")))


    # routers
    dp.include_routers(
        main_menu_router,
        catalog_router,
        order_router,
        user_manage_router,
        anon_questions_router,
        catalog_manage_router
    )

    # события
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⛔️ Остановлено вручную")
