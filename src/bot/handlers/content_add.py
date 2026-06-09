import logging
import tempfile

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.i18n import gettext as _

from src.bot.filters.callbacks import Menu
from src.client_manager.client_repo import ClientRepo
from src.content_categories import (
    build_content_category_keyboard,
    get_content_category,
    resolve_content_save_path,
    resolve_qbittorrent_category,
)
from src.redis_helper.wrapper import RedisWrapper
from src.settings import Settings

logger = logging.getLogger(__name__)

PENDING_PREFIX = "pending:"
ACTION_CONTENT_PREFIX = "content:"
ACTION_EDIT_PATH_PREFIX = "edit_content_path:"


def is_magnet(text: str | None) -> bool:
    return bool(text and text.startswith("magnet:?xt"))


async def store_pending_magnet(redis: RedisWrapper, user_id: int, magnet_text: str) -> None:
    await redis.set(f"{PENDING_PREFIX}{user_id}", f"magnet|{magnet_text}")


async def store_pending_torrent(redis: RedisWrapper, user_id: int, file_id: str, file_name: str) -> None:
    await redis.set(f"{PENDING_PREFIX}{user_id}", f"torrent|{file_id}|{file_name}")


async def get_pending(redis: RedisWrapper, user_id: int) -> tuple[str, list[str]] | None:
    pending = await redis.get(f"{PENDING_PREFIX}{user_id}")
    if not pending:
        return None

    kind, rest = pending.split("|", 1)
    if kind == "magnet":
        return kind, [line for line in rest.split("\n") if line.strip()]
    if kind == "torrent":
        file_id, file_name = rest.split("|", 1)
        return kind, [file_id, file_name]

    return None


async def clear_pending(redis: RedisWrapper, user_id: int) -> None:
    await redis.delete(f"{PENDING_PREFIX}{user_id}")


async def send_category_picker(
    bot: Bot,
    chat_id: int,
    settings: Settings,
    *,
    message_id: int | None = None,
    text: str | None = None,
) -> None:
    prompt = text or _("Where should this download go?")
    markup = build_content_category_keyboard(settings)

    if message_id:
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=prompt,
                reply_markup=markup,
            )
            return
        except Exception:
            logger.debug("Could not edit message for category picker, sending a new one")

    await bot.send_message(chat_id=chat_id, text=prompt, reply_markup=markup)


async def send_content_prompt(
    bot: Bot,
    chat_id: int,
    message_id: int,
    settings: Settings,
    category_id: str,
) -> None:
    category = get_content_category(settings, category_id)
    if not category:
        return

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("🔙 Menu"), callback_data=Menu().pack())]
        ]
    )

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=_(category.prompt),
            reply_markup=markup,
        )
    except Exception:
        await bot.send_message(chat_id=chat_id, text=_(category.prompt), reply_markup=markup)


async def add_magnet_links(settings: Settings, magnet_links: list[str], category_id: str) -> bool:
    repository_class = ClientRepo.get_client_manager(settings.client.type)
    return await repository_class(settings).add_magnet(
        magnet_link=magnet_links,
        category=resolve_qbittorrent_category(settings, category_id),
        save_path=resolve_content_save_path(settings, category_id),
    )


async def add_torrent_file(settings: Settings, bot: Bot, file_id: str, file_name: str, category_id: str) -> bool:
    with tempfile.TemporaryDirectory() as tempdir:
        local_path = f"{tempdir}/{file_name}"
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, local_path)

        repository_class = ClientRepo.get_client_manager(settings.client.type)
        return await repository_class(settings).add_torrent(
            file_name=local_path,
            category=resolve_qbittorrent_category(settings, category_id),
            save_path=resolve_content_save_path(settings, category_id),
        )


async def process_pending_download(
    bot: Bot,
    redis: RedisWrapper,
    settings: Settings,
    user_id: int,
    chat_id: int,
    category_id: str,
    *,
    message_id: int | None = None,
) -> bool:
    pending = await get_pending(redis, user_id)
    if not pending:
        return False

    kind, payload = pending
    success = False

    if kind == "magnet":
        success = await add_magnet_links(settings, payload, category_id)
    elif kind == "torrent" and len(payload) == 2:
        success = await add_torrent_file(settings, bot, payload[0], payload[1], category_id)

    await clear_pending(redis, user_id)
    await redis.set(f"action:{user_id}", None)

    category = get_content_category(settings, category_id)
    if success:
        await bot.send_message(
            chat_id,
            _("Added to {label}").format(label=_(category.label) if category else category_id),
        )
    else:
        await bot.send_message(chat_id, _("Unable to add torrent"))

    return success


async def process_active_content_message(
    message: Message,
    redis: RedisWrapper,
    bot: Bot,
    settings: Settings,
    category_id: str,
) -> bool:
    if is_magnet(message.text):
        success = await add_magnet_links(settings, message.text.split("\n"), category_id)
    elif message.document and message.document.file_name and ".torrent" in message.document.file_name:
        success = await add_torrent_file(
            settings,
            bot,
            message.document.file_id,
            message.document.file_name,
            category_id,
        )
    else:
        await message.reply(_("Send a magnet link or a .torrent file"))
        return False

    await redis.set(f"action:{message.from_user.id}", None)

    if not success:
        await message.reply(_("Unable to add torrent"))
        return False

    category = get_content_category(settings, category_id)
    await message.reply(_("Added to {label}").format(label=_(category.label) if category else category_id))
    return True
