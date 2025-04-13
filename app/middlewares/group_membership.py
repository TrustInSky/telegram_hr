from aiogram.types import TelegramObject, User, Message
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from app.database.database import SessionLocal
from app.database.models import User as DBUser
from sqlalchemy import update

class GroupMembershipMiddleware(BaseMiddleware):
    def __init__(self, target_group_id: int):
        super().__init__()
        self.target_group_id = target_group_id

    async def __call__(self, handler, event: TelegramObject, data: dict):
        # Проверяем только для сообщений или колбэков
        if hasattr(event, "from_user"):
            tg_user = event.from_user
            bot = data.get("bot")
            
            # Проверяем, является ли пользователь членом группы
            try:
                member = await bot.get_chat_member(chat_id=self.target_group_id, user_id=tg_user.id)
                is_member = member.status not in ["left", "kicked", "banned"]
            except Exception as e:
                print(f"Ошибка при проверке членства: {e}")
                is_member = False
                
            async with SessionLocal() as session:
                user = await session.get(DBUser, tg_user.id)
                
                if not user:
                    # Создаем нового пользователя
                    new_user = DBUser(
                        telegram_id=tg_user.id,
                        username=tg_user.username,
                        fullname=tg_user.full_name,
                        birth_date=None,
                        hire_date=None,
                        is_active=is_member,  # Активен только если член группы
                        tpoints=0,
                        role="user" if is_member else "inactive_user"  # Роль зависит от членства
                    )
                    session.add(new_user)
                    await session.commit()
                    user = new_user
                elif user.is_active and not is_member:
                    # Если пользователь был активен, но теперь не в группе - обновляем статус
                    user.is_active = False
                    user.role = "inactive_user"
                    await session.commit()
                    print(f"Пользователь {tg_user.id} деактивирован: исключен из группы")
                elif not user.is_active and is_member:
                    # Если пользователь был неактивен, но теперь в группе - активируем его
                    user.is_active = True
                    if user.role == "inactive_user":
                        user.role = "user"
                    await session.commit()
                    print(f"Пользователь {tg_user.id} активирован: присоединился к группе")
            
            # Добавляем информацию о пользователе в data
            data["is_group_member"] = is_member
            data["user_db"] = user
            
            # Если не член группы, отправляем сообщение и прерываем обработку
            if not is_member and hasattr(event, "answer"):
                await event.answer("Вы должны быть участником группы, чтобы использовать этого бота. Пожалуйста, вступите в группу и попробуйте снова.")
                return None
            
        # Продолжаем обработку, только если прошли все проверки
        return await handler(event, data)