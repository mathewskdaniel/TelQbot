from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.settings.content_category import ContentCategory

if TYPE_CHECKING:
    from src.settings import Settings

logger = logging.getLogger(__name__)


def get_content_category(settings: Settings, category_id: str) -> ContentCategory | None:
    return next((category for category in settings.content_categories if category.id == category_id), None)


def resolve_qbittorrent_category(settings: Settings, category_id: str) -> str | None:
    category = get_content_category(settings, category_id)
    return category.qbittorrent_category if category else None


def resolve_content_save_path(settings: Settings, category_id: str) -> str | None:
    category = get_content_category(settings, category_id)
    return category.save_path if category else None


def build_content_category_keyboard(settings: Settings) -> InlineKeyboardMarkup:
    from aiogram.utils.i18n import gettext as _

    from src.bot.filters.callbacks import PickContentCategory, Menu

    buttons = [
        [
            InlineKeyboardButton(
                text=_(category.label),
                callback_data=PickContentCategory(category_id=category.id).pack(),
            )
        ]
        for category in settings.content_categories
    ]
    buttons.append([InlineKeyboardButton(text=_("🔙 Menu"), callback_data=Menu().pack())])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_content_categories_summary(settings: Settings) -> str:
    from aiogram.utils.i18n import gettext as _

    lines = [_("📁 **Content download folders**\n")]
    for category in settings.content_categories:
        lines.append(
            _("{label} (`{qb_category}`)\n`{save_path}`").format(
                label=category.label,
                qb_category=category.qbittorrent_category,
                save_path=category.save_path,
            )
        )
        lines.append("")
    return "\n".join(lines)


async def sync_content_categories(settings: Settings) -> None:
    from src.client_manager.client_repo import ClientRepo

    repository_class = ClientRepo.get_client_manager(settings.client.type)
    manager = repository_class(settings)
    existing = set(await manager.get_categories())

    for category in settings.content_categories:
        try:
            if category.qbittorrent_category in existing:
                await manager.edit_category(category.qbittorrent_category, category.save_path)
            else:
                await manager.create_category(category.qbittorrent_category, category.save_path)
        except Exception:
            logger.exception("Failed to sync category %s", category.qbittorrent_category)

    logger.info("Synced %s content categories to qBittorrent", len(settings.content_categories))


def update_content_category_path(settings: Settings, category_id: str, save_path: str) -> bool:
    category = get_content_category(settings, category_id)
    if not category:
        return False

    category.save_path = save_path.replace("\\", "")
    settings.export_settings()
    return True
