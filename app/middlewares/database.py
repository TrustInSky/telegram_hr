from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, session_pool: sessionmaker):
        self.session_pool = session_pool
        super().__init__()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Create a new session for each request
        async with self.session_pool() as session:
            # Add session to the data dictionary so handlers can access it
            data["session"] = session
            
            # Log that we're adding session to data (for debugging)
            print(f"Database middleware: added session to data dictionary")
            
            # Call the next handler in the chain
            return await handler(event, data)