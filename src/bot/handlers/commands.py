from aiogram import Bot
from aiogram.types import Message
from aiogram.dispatcher.router import Router
from aiogram.filters import CommandStart, Command

from src.redis_helper.wrapper import RedisWrapper
from src.utils import get_stats_text
from src.settings import Settings

from ..filters import IsAuthorizedUser
from .common import send_menu


def get_router():
    router = Router()

    @router.message(CommandStart(), IsAuthorizedUser())
    async def start_command(message: Message, redis: RedisWrapper, bot: Bot, settings: Settings) -> None:
        """Start the bot."""
        await redis.set(f"action:{message.from_user.id}", None)
        await send_menu(bot, redis, settings, message.chat.id, message.message_id)

    @router.message(Command("stats"), IsAuthorizedUser())
    async def stats_command(message: Message) -> None:
        await message.reply(get_stats_text())

    return router
