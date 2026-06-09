from aiogram import Bot, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

from src.bot.filters.callbacks import List, ListByStatus, Menu, Stats
from src.bot.handlers.common import list_active_torrents, send_menu
from src.settings import Settings
from src.redis_helper.wrapper import RedisWrapper
from src.utils import get_stats_text


def get_router():
    router = Router()

    @router.callback_query(Stats.filter())
    async def stats_callback(callback_query: CallbackQuery, bot: Bot) -> None:
        await callback_query.answer()
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=get_stats_text(),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=_("🔙 Menu"), callback_data=Menu().pack())]
                ]
            )
        )

    @router.callback_query(List.filter())
    async def list_callback(callback_query: CallbackQuery, callback_data: List, settings: Settings, bot: Bot) -> None:
        await callback_query.answer()
        await list_active_torrents(bot, callback_query.from_user.id, callback_query.message.message_id, settings)


    @router.callback_query(ListByStatus.filter())
    async def list_by_status_callback(callback_query: CallbackQuery, callback_data: ListByStatus, settings: Settings, bot: Bot) -> None:
        await callback_query.answer()
        status_filter = callback_data.status
        await list_active_torrents(bot, callback_query.from_user.id, callback_query.message.message_id, settings, status_filter=status_filter)


    @router.callback_query(Menu.filter())
    async def menu_callback(callback_query: CallbackQuery, callback_data: Menu, bot: Bot, redis: RedisWrapper, settings: Settings) -> None:
        await callback_query.answer()
        await send_menu(bot, redis, settings, callback_query.from_user.id, callback_query.message.message_id)

    return router
