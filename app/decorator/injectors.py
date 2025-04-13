from functools import wraps
from typing import Callable, Type
from app.repositories.catalog_repo import CatalogRepo
from app.repositories.user_repo import UserRepo
from app.repositories.order_repo import OrderRepo
from app.repositories.anon_question_repo import AnonymousQuestionRepo
from app.services.catalog_service import CatalogService
from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.services.question_service import AnonymousQuestionService
from app.database.database import SessionLocal

def inject_services(*service_classes: Type):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Создаем сессию напрямую внутри декоратора
            async with SessionLocal() as session:
                # Создаем репозитории и сервисы с необходимыми зависимостями
                for service_class in service_classes:
                    service_name = service_class.__name__.lower()
                    
                    if service_class == CatalogRepo:
                        kwargs[service_name] = CatalogRepo(session)
                    elif service_class == UserRepo:
                        kwargs[service_name] = UserRepo(session)
                    elif service_class == OrderRepo:
                        kwargs[service_name] = OrderRepo(session)
                    elif service_class == AnonymousQuestionRepo:
                        kwargs[service_name] = AnonymousQuestionRepo(session)
                    elif service_class == CatalogService:
                        catalog_repo = CatalogRepo(session)
                        kwargs[service_name] = CatalogService(catalog_repo)
                    elif service_class == UserService:
                        user_repo = UserRepo(session)
                        kwargs[service_name] = UserService(user_repo)
                    elif service_class == OrderService:
                        order_repo = OrderRepo(session)
                        user_repo = UserRepo(session)
                        catalog_repo = CatalogRepo(session)
                        kwargs[service_name] = OrderService(order_repo, user_repo, catalog_repo)
                    elif service_class == AnonymousQuestionService:
                        anon_question_repo = AnonymousQuestionRepo(session)
                        kwargs[service_name] = AnonymousQuestionService(anon_question_repo)

                # Проверяем, что все необходимые сервисы созданы
                missing_args = [service_class.__name__.lower() for service_class in service_classes if service_class.__name__.lower() not in kwargs]
                if missing_args:
                    raise ValueError(f"Failed to create services: {', '.join(missing_args)}")
                
                # Вызов оригинального обработчика
                return await func(*args, **kwargs)
        return wrapper
    return decorator
