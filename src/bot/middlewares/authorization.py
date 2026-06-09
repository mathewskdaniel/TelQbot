from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.settings import Settings


class AuthorizationMiddleware(BaseMiddleware):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user_id = None

        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id

        if user_id is not None:
            allowed_ids = {user.user_id for user in self.settings.users}
            if user_id not in allowed_ids:
                if isinstance(event, CallbackQuery):
                    await event.answer()
                return None

        return await handler(event, data)
