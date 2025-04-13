from app.repositories.user_repo import UserRepo
from app.utils.exel import user_create_excel_file


class UserService:
    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

    async def get_hr_by_telegram_id(self, telegram_id: int):
        return await self.user_repo.get_hr_by_telegram_id(telegram_id)
    
    async def bulk_import_users(self, users_data: list[dict]) -> None:
        for user in users_data:
            telegram_id = int(user["Telegram ID"])
            existing = await self.user_repo.get_by_telegram_id(telegram_id)

            is_active = str(user.get("Active", "1")).strip() in ["1", "True", "true"]

            if existing:
                existing.fullname = user["Full Name"]
                existing.username = user.get("Username", "")
                existing.tpoints = int(user.get("T-Points", 0))
                existing.role = user.get("Role", "user")
                existing.department = user["Department"]
                existing.post = user["Post"]
                existing.is_active = is_active
            else:
                await self.user_repo.create_user(
                    telegram_id=telegram_id,
                    fullname=user["Full Name"],
                    username=user.get("Username", ""),
                    tpoints=int(user.get("T-Points", 0)),
                    role=user.get("Role", "user"),
                    is_active=is_active,
                )

        await self.user_repo.session.commit()
            
    async def export_users_to_excel(self) -> bytes:
        users = await self.user_repo.get_all_users()
        return user_create_excel_file(users)