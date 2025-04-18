from functools import wraps
from typing import Callable, Type, Any
from aiogram.fsm.context import FSMContext
from app.repositories.catalog_repo import CatalogRepo
from app.repositories.user_repo import UserRepo
from app.repositories.order_repo import OrderRepo
from app.repositories.anon_question_repo import AnonymousQuestionRepo
from app.repositories.cart_repo import CartRepository
from app.services.catalog_service import CatalogService
from app.services.user_service import UserService
from app.services.order_service import OrderService
from app.services.question_service import AnonymousQuestionService
from app.services.cart_service import CartService
from app.database.database import SessionLocal
import inspect

def inject_services(*service_classes: Type):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем сигнатуру функции для проверки требуемых аргументов
            sig = inspect.signature(func)
            
            # Обрабатываем FSMContext отдельно
            needs_state = False
            for param_name, param in sig.parameters.items():
                if param_name == "state" and param.annotation in (FSMContext, Any, inspect.Parameter.empty):
                    needs_state = True
                    # Проверяем, есть ли FSMContext в переданных аргументах
                    for arg in args:
                        if isinstance(arg, FSMContext):
                            kwargs["state"] = arg
                            break
                    # Ищем FSMContext в kwargs
                    if "state" not in kwargs:
                        for key, value in kwargs.items():
                            if isinstance(value, FSMContext):
                                kwargs["state"] = value
                                break
            
            # Создаем сессию напрямую внутри декоратора
            async with SessionLocal() as session:
                try:
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
                        elif service_class == CartRepository:
                            kwargs[service_name] = CartRepository(session)
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
                        elif service_class == CartService:
                            # Pass the session directly to CartService as it expects it
                            kwargs[service_name] = CartService(session)

                    # Проверяем, что все необходимые сервисы созданы
                    missing_args = [service_class.__name__.lower() for service_class in service_classes if service_class.__name__.lower() not in kwargs]
                    
                    # Добавляем FSMContext в список недостающих аргументов, если он нужен, но отсутствует
                    if needs_state and "state" not in kwargs:
                        missing_args.append("fsmcontext")
                    
                    if missing_args:
                        raise ValueError(f"Failed to create services: {', '.join(missing_args)}")
                    
                    # Вызов оригинального обработчика
                    result = await func(*args, **kwargs)
                    
                    # Commit the session after the handler completes
                    await session.commit()
                    
                    return result
                except Exception as e:
                    # Rollback the session in case of an error
                    await session.rollback()
                    raise e
                    
        return wrapper
    return decorator