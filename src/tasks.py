from aiogram import Bot
from aiogram.utils.i18n import gettext as _

from logging import getLogger
from pathlib import Path
from watchfiles import awatch

from src.redis_helper.wrapper import RedisWrapper
from src.client_manager.client_repo import ClientRepo
from src.content_categories import sync_content_categories
from src.settings import Settings
from src.settings.user import User
from src.bot.middlewares.custom_i18n import CustomI18nMiddleware


logger = getLogger(__name__)

DONE_KEY_PREFIX = "torrent_done:"
DONE_TTL = 10 * 86400


def user_filters(users: list[User], category: str):
    for user in users:
        if not user.notification_filter:
            yield user

        elif category in user.notification_filter:
            yield user


def _is_complete(torrent) -> bool:
    return torrent.progress >= 1


def _done_key(torrent_hash: str) -> str:
    return f"{DONE_KEY_PREFIX}{torrent_hash}"


async def seed_completed_torrents(redis: RedisWrapper, settings: Settings) -> None:
    """Record current completion state without sending notifications."""
    seeded = await _sync_torrent_completion_states(redis, settings, notify=False)
    logger.info("Initialized torrent completion tracking for %s torrents", seeded)


async def torrent_finished(bot: Bot, redis: RedisWrapper, settings: Settings, i18n_middleware: CustomI18nMiddleware):
    await _sync_torrent_completion_states(
        redis,
        settings,
        notify=True,
        bot=bot,
        i18n_middleware=i18n_middleware,
    )


async def _sync_torrent_completion_states(
    redis: RedisWrapper,
    settings: Settings,
    notify: bool = False,
    bot: Bot | None = None,
    i18n_middleware: CustomI18nMiddleware | None = None,
) -> int:
    repository_class = ClientRepo.get_client_manager(settings.client.type)
    torrents = await repository_class(settings).get_torrents()

    for torrent in torrents:
        key = _done_key(torrent.hash)
        was_done = await redis.get(key)
        now_done = _is_complete(torrent)
        now_value = "1" if now_done else "0"

        if notify and now_done and was_done == "0":
            await _notify_torrent_finished(bot, settings, i18n_middleware, torrent)

        await redis.set(key, now_value, DONE_TTL)

    return len(torrents)


async def _notify_torrent_finished(
    bot: Bot,
    settings: Settings,
    i18n_middleware: CustomI18nMiddleware,
    torrent,
) -> None:
    for user in user_filters(settings.users, torrent.category):
        if not user.notify:
            continue

        try:
            with i18n_middleware.i18n.context() as ctx:
                user_lang = user.locale if user.locale else ctx.default_locale
                ctx.use_locale(user_lang)
                await bot.send_message(
                    user.user_id,
                    _("Torrent {name} has finished downloading!".format(name=torrent.name)),
                    parse_mode=None,
                )
        except Exception as e:
            logger.exception(e)


async def watch_config(path: Path, settings: Settings):
    async for _ in awatch(path):
        try:
            new_settings = Settings.load_settings()
            settings.update_from(new_settings)
            await sync_content_categories(settings)
            logger.debug("Settings reloaded successfully")
        except Exception as e:
            logger.exception(e)
