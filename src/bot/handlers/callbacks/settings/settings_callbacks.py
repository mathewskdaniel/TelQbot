from aiogram import Bot, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

from src.settings import Settings
from src.settings.enums import UserRolesEnum

from src.bot.filters import HasRole
from src.bot.filters.callbacks import (
    SettingsMenu,
    Menu,
    EditClientMenu,
    ReloadSettingsMenu,
    ToggleSpeedLimit,
    CheckConnection,
    ContentCategoriesMenu,
    EditContentCategoryPath,
)
from src.bot.handlers.content_add import ACTION_EDIT_PATH_PREFIX
from src.content_categories import format_content_categories_summary, sync_content_categories
from src.client_manager.client_repo import ClientRepo
from src.redis_helper.wrapper import RedisWrapper


def get_router():
    router = Router()

    @router.callback_query(SettingsMenu.filter(), HasRole(UserRolesEnum.Administrator))
    async def settings_callback(callback_query: CallbackQuery, callback_data: SettingsMenu, bot: Bot) -> None:
        await callback_query.answer()
        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=_("TelQbot Settings"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=_("📥 Client Settings"), callback_data=EditClientMenu().pack())
                    ],
                    [
                        InlineKeyboardButton(text=_("📁 Content Folders"), callback_data=ContentCategoriesMenu().pack())
                    ],
                    [
                        InlineKeyboardButton(text=_("🔄 Reload Settings"), callback_data=ReloadSettingsMenu().pack())
                    ],
                    [
                        InlineKeyboardButton(text=_("🔙 Menu"), callback_data=Menu().pack())
                    ]
                ]
            )
        )


    @router.callback_query(ContentCategoriesMenu.filter(), HasRole(UserRolesEnum.Administrator))
    async def content_categories_menu_callback(
        callback_query: CallbackQuery,
        bot: Bot,
        settings: Settings,
        redis: RedisWrapper,
    ) -> None:
        await callback_query.answer()
        buttons = [
            [
                InlineKeyboardButton(
                    text=_("✏️ Change {label} folder").format(label=_(category.label)),
                    callback_data=EditContentCategoryPath(category_id=category.id).pack(),
                )
            ]
            for category in settings.content_categories
        ]
        buttons.append([InlineKeyboardButton(text=_("🔙 Settings"), callback_data=SettingsMenu().pack())])

        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=format_content_categories_summary(settings),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )


    @router.callback_query(EditContentCategoryPath.filter(), HasRole(UserRolesEnum.Administrator))
    async def edit_content_category_path_callback(
        callback_query: CallbackQuery,
        callback_data: EditContentCategoryPath,
        bot: Bot,
        redis: RedisWrapper,
        settings: Settings,
    ) -> None:
        from src.content_categories import get_content_category

        category = get_content_category(settings, callback_data.category_id)
        if not category:
            await callback_query.answer(_("Unknown category"), show_alert=True)
            return

        await callback_query.answer()
        await redis.set(
            f"action:{callback_query.from_user.id}",
            f"{ACTION_EDIT_PATH_PREFIX}{callback_data.category_id}",
        )

        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=_("Send the new folder path for {label}").format(label=_(category.label)),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=_("🔙 Content Folders"), callback_data=ContentCategoriesMenu().pack())]
                ]
            ),
        )


    @router.callback_query(EditClientMenu.filter(), HasRole(UserRolesEnum.Administrator))
    async def edit_client_settings_callback(callback_query: CallbackQuery, callback_data: EditClientMenu, bot: Bot, settings: Settings) -> None:
        await callback_query.answer()
        repository_class = ClientRepo.get_client_manager(settings.client.type)
        speed_limit = await repository_class(settings).get_speed_limit_mode()

        speed_limit_status = _("✅ Enabled") if speed_limit else _("❌ Disabled")

        confs = _("**Speed Limit**: {speed_limit_status}"
            .format(
                speed_limit_status=speed_limit_status
            )
        )

        text = _("Edit {client_type} client settings \n\n{configs}"
            .format(
                client_type=settings.client.type.value.title(),
                configs=confs
            )
        )

        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=_("🐢 Toggle Speed Limit"), callback_data=ToggleSpeedLimit().pack())
                    ],
                    [
                        InlineKeyboardButton(text=_("✅ Check Client connection"), callback_data=CheckConnection().pack())
                    ],
                    [
                        InlineKeyboardButton(text=_("🔙 Settings"), callback_data=SettingsMenu().pack())
                    ]
                ]
            )
        )


    @router.callback_query(ToggleSpeedLimit.filter(), HasRole(UserRolesEnum.Administrator))
    async def toggle_speed_limit_callback(callback_query: CallbackQuery, callback_data: ToggleSpeedLimit, bot: Bot, settings: Settings) -> None:
        await callback_query.answer()
        repository_class = ClientRepo.get_client_manager(settings.client.type)
        speed_limit = await repository_class(settings).toggle_speed_limit()

        speed_limit_status = _("✅ Enabled") if speed_limit else _("❌ Disabled")

        confs = _("**Speed Limit**: {speed_limit_status}"
            .format(
                speed_limit_status=speed_limit_status
            )
        )

        text = _("Edit {client_type} client settings \n\n{configs}"
            .format(
                client_type=settings.client.type.value.title(),
                configs=confs
            )
        )

        await bot.edit_message_text(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            text=text,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=_("🐢 Toggle Speed Limit"), callback_data=ToggleSpeedLimit().pack())
                    ],
                    [
                        InlineKeyboardButton(text=_("✅ Check Client connection"), callback_data=CheckConnection().pack())
                    ],
                    [
                        InlineKeyboardButton(text=_("🔙 Settings"), callback_data=SettingsMenu().pack())
                    ]
                ]
            )
        )


    @router.callback_query(CheckConnection.filter(), HasRole(UserRolesEnum.Administrator))
    async def check_connection_callback(callback_query: CallbackQuery, callback_data: CheckConnection, bot: Bot, settings: Settings) -> None:
        try:
            repository_class = ClientRepo.get_client_manager(settings.client.type)
            version = await repository_class(settings).check_connection()

            await callback_query.answer(
                _(
                    "✅ The connection works. QBittorrent version: {version}"
                        .format(
                            version=version
                        )
                ), show_alert=True
            )
        except Exception:
            await callback_query.answer(_("❌ Unable to establish connection with QBittorrent"), show_alert=True)


    @router.callback_query(ReloadSettingsMenu.filter(), HasRole(UserRolesEnum.Administrator))
    async def reload_settings_callback(callback_query: CallbackQuery, callback_data: ReloadSettingsMenu, bot: Bot, settings: Settings) -> None:
        new_settings = Settings.load_settings()
        settings.update_from(new_settings)
        await sync_content_categories(settings)
        await callback_query.answer(_("✅ Settings Reloaded"), show_alert=True)


    return router
