import logging
import tempfile

from aiogram import F
from aiogram import Bot
from aiogram.types import Message
from aiogram.dispatcher.router import Router
from aiogram.utils.i18n import gettext as _

from src.client_manager.client_repo import ClientRepo
from src.settings import Settings
from src.bot.filters import IsAuthorizedUser, IsCommand
from src.redis_helper.wrapper import RedisWrapper
from src.bot.handlers.content_add import (
    ACTION_CONTENT_PREFIX,
    ACTION_EDIT_PATH_PREFIX,
    is_magnet,
    store_pending_magnet,
    store_pending_torrent,
    send_category_picker,
    process_active_content_message,
)
from src.content_categories import get_content_category, sync_content_categories, update_content_category_path
from src.stremio_admin import ACTION_STREMIO_TOKEN, update_admin_scan_token

from .common import send_menu


logger = logging.getLogger(__name__)


def get_router():
    router = Router()

    async def on_category_name(message: Message, redis: RedisWrapper):
        await redis.set(f"action:{message.from_user.id}", f"category_dir#{message.text}")
        await message.reply(
            _("Please, send the path for the category {category_name}"
                .format(
                    category_name=message.text
                )
            )
        )


    async def on_category_directory(message: Message, action, redis: RedisWrapper, bot: Bot, settings: Settings):
        name: str = (await redis.get(f"action:{message.from_user.id}")).split("#")[1]

        repository_class = ClientRepo.get_client_manager(settings.client.type)

        if "modify" in action:
            await repository_class(settings).edit_category(name=name, save_path=message.text.replace("\\", ""))
            await send_menu(bot, redis, settings, message.chat.id, message.message_id)
            return

        await repository_class(settings).create_category(name=name, save_path=message.text.replace("\\", ""))
        await send_menu(bot, redis, settings, message.chat.id, message.message_id)


    async def on_edit_content_path(message: Message, redis: RedisWrapper, bot: Bot, settings: Settings, category_id: str):
        if not update_content_category_path(settings, category_id, message.text.strip()):
            await message.reply(_("Unknown category"))
            return

        await sync_content_categories(settings)
        await redis.set(f"action:{message.from_user.id}", None)

        category = get_content_category(settings, category_id)
        await message.reply(
            _("Updated folder for {label} to:\n`{save_path}`").format(
                label=_(category.label),
                save_path=category.save_path,
            )
        )


    @router.message(~F.from_user.is_bot, ~IsCommand(), IsAuthorizedUser())
    async def on_message(message: Message, redis: RedisWrapper, bot: Bot, settings: Settings) -> None:
        action = await redis.get(f"action:{message.from_user.id}") or ""

        if action.startswith(ACTION_CONTENT_PREFIX):
            category_id = action.removeprefix(ACTION_CONTENT_PREFIX)
            handled = await process_active_content_message(message, redis, bot, settings, category_id)
            if handled:
                await send_menu(bot, redis, settings, message.chat.id, message.message_id)
            return

        if action.startswith(ACTION_EDIT_PATH_PREFIX):
            category_id = action.removeprefix(ACTION_EDIT_PATH_PREFIX)
            await on_edit_content_path(message, redis, bot, settings, category_id)
            return

        if action == ACTION_STREMIO_TOKEN:
            token = (message.text or "").strip()
            if not token:
                await message.reply(_("Token cannot be empty"))
                return

            update_admin_scan_token(settings, token)
            await redis.set(f"action:{message.from_user.id}", None)
            await message.reply(_("Stremio admin token updated"))
            return

        if is_magnet(message.text):
            await store_pending_magnet(redis, message.from_user.id, message.text)
            await send_category_picker(bot, message.chat.id, settings)
            return

        if message.document and message.document.file_name and ".torrent" in message.document.file_name:
            await store_pending_torrent(
                redis,
                message.from_user.id,
                message.document.file_id,
                message.document.file_name,
            )
            await send_category_picker(bot, message.chat.id, settings)
            return

        if action == "category_name":
            await on_category_name(message, redis)
            return

        if "category_dir" in action:
            await on_category_directory(message, action, redis, bot, settings)
            return

        await message.reply(_("The command does not exist"))

    return router
