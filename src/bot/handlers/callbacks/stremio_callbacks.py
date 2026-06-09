from aiogram import Bot, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

from src.bot.filters import HasRole
from src.bot.filters.callbacks import Menu, StremioMenu, StremioScan, StremioRebuild, StremioRebuildConfirm, StremioUpdateToken
from src.stremio_admin import ACTION_STREMIO_TOKEN
from src.redis_helper.wrapper import RedisWrapper
from src.settings import Settings
from src.settings.enums import UserRolesEnum
from src.stremio_admin import mask_token, post_admin_action


def stremio_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=_("🔍 Scan Library"), callback_data=StremioScan().pack())],
            [InlineKeyboardButton(text=_("♻️ Full Rebuild"), callback_data=StremioRebuild().pack())],
            [InlineKeyboardButton(text=_("🔑 Update Admin Token"), callback_data=StremioUpdateToken().pack())],
            [InlineKeyboardButton(text=_("🔙 Menu"), callback_data=Menu().pack())],
        ]
    )


def stremio_menu_text(settings: Settings) -> str:
    return _(
        "📺 **Stremio Library**\n\n"
        "Admin URL: `{admin_url}`\n"
        "Token: `{token}`"
    ).format(
        admin_url=settings.stremio.admin_base_url.unicode_string(),
        token=mask_token(settings.stremio.admin_scan_token),
    )


def get_router():
    router = Router()

    @router.callback_query(StremioMenu.filter(), HasRole(UserRolesEnum.Administrator))
    async def stremio_menu_callback(callback_query: CallbackQuery, bot: Bot, settings: Settings) -> None:
        await callback_query.answer()
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=stremio_menu_text(settings),
            reply_markup=stremio_menu_keyboard(),
        )

    @router.callback_query(StremioScan.filter(), HasRole(UserRolesEnum.Administrator))
    async def stremio_scan_callback(callback_query: CallbackQuery, bot: Bot, settings: Settings) -> None:
        await callback_query.answer(_("Scanning library..."))
        ok, message = await post_admin_action(settings, "/admin/scan")
        text = _("✅ Scan complete:\n```\n{result}\n```") if ok else _("❌ Scan failed:\n{error}").format(error=message)
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=text.format(result=message) if ok else text,
            reply_markup=stremio_menu_keyboard(),
        )

    @router.callback_query(StremioRebuild.filter(), HasRole(UserRolesEnum.Administrator))
    async def stremio_rebuild_callback(callback_query: CallbackQuery, bot: Bot) -> None:
        await callback_query.answer()
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=_("⚠️ Full rebuild clears the Stremio database and rescans everything.\n\nContinue?"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=_("✅ Yes, rebuild"), callback_data=StremioRebuildConfirm().pack())],
                    [InlineKeyboardButton(text=_("🔙 Back"), callback_data=StremioMenu().pack())],
                ]
            ),
        )

    @router.callback_query(StremioRebuildConfirm.filter(), HasRole(UserRolesEnum.Administrator))
    async def stremio_rebuild_confirm_callback(callback_query: CallbackQuery, bot: Bot, settings: Settings) -> None:
        await callback_query.answer(_("Rebuilding library..."))
        ok, message = await post_admin_action(settings, "/admin/scan/rebuild")
        text = _("✅ Rebuild complete:\n```\n{result}\n```") if ok else _("❌ Rebuild failed:\n{error}").format(error=message)
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=text.format(result=message) if ok else text,
            reply_markup=stremio_menu_keyboard(),
        )

    @router.callback_query(StremioUpdateToken.filter(), HasRole(UserRolesEnum.Administrator))
    async def stremio_update_token_callback(callback_query: CallbackQuery, bot: Bot, redis: RedisWrapper) -> None:
        await callback_query.answer()
        await redis.set(f"action:{callback_query.from_user.id}", ACTION_STREMIO_TOKEN)
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=_("Send the new Stremio admin scan token"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=_("🔙 Back"), callback_data=StremioMenu().pack())]
                ]
            ),
        )

    return router
