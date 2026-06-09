from aiogram import Bot, Router
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _

from src.bot.filters import HasRole
from src.bot.filters.callbacks import PickContentCategory
from src.bot.handlers.content_add import (
    ACTION_CONTENT_PREFIX,
    get_pending,
    send_content_prompt,
    process_pending_download,
)
from src.content_categories import get_content_category
from src.redis_helper.wrapper import RedisWrapper
from src.settings import Settings
from src.settings.enums import UserRolesEnum


def get_router():
    router = Router()

    @router.callback_query(PickContentCategory.filter(), HasRole(UserRolesEnum.Administrator))
    @router.callback_query(PickContentCategory.filter(), HasRole(UserRolesEnum.Manager))
    async def pick_content_category_callback(
        callback_query: CallbackQuery,
        callback_data: PickContentCategory,
        bot: Bot,
        redis: RedisWrapper,
        settings: Settings,
    ) -> None:
        category = get_content_category(settings, callback_data.category_id)
        if not category:
            await callback_query.answer(_("Unknown category"), show_alert=True)
            return

        await callback_query.answer()

        user_id = callback_query.from_user.id
        if await get_pending(redis, user_id):
            await process_pending_download(
                bot,
                redis,
                settings,
                user_id,
                callback_query.message.chat.id,
                callback_data.category_id,
                message_id=callback_query.message.message_id,
            )
            return

        await redis.set(f"action:{user_id}", f"{ACTION_CONTENT_PREFIX}{callback_data.category_id}")
        await send_content_prompt(
            bot,
            callback_query.message.chat.id,
            callback_query.message.message_id,
            settings,
            callback_data.category_id,
        )

    return router
