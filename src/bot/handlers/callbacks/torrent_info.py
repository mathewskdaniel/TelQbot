from aiogram import Bot, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import BufferedInputFile, CallbackQuery
from aiogram.utils.i18n import gettext as _

from src.client_manager.client_repo import ClientRepo
from src.settings import Settings
from src.utils import convert_size, convert_eta, format_progress, escape_markdown, format_ratio, format_seeding_days

from src.bot.filters.callbacks import TorrentInfo, RefreshTorrentInfo, Export, Pause, Resume, DeleteOne, Menu, EditTorrentCategory
from src.bot.handlers.common import list_categories


def build_torrent_info_text(torrent) -> str:
    text_to_send = f"{escape_markdown(torrent.name)}\n"

    if torrent.progress == 1:
        text_to_send += _("**COMPLETED**\n")
    else:
        text_to_send += format_progress(torrent.progress)

    if "stalled" not in torrent.state:
        text_to_send += _("**State:** {current_state} \n**Download Speed:** {download_speed}/s\n**Upload Speed:** {upload_speed}/s\n"
            .format(
                current_state=torrent.state.capitalize(),
                download_speed=convert_size(torrent.dlspeed),
                upload_speed=convert_size(torrent.upspeed),
            )
        )

    text_to_send += _("**Size:** {torrent_size}\n"
        .format(
            torrent_size=convert_size(torrent.size)
        )
    )

    if "stalled" not in torrent.state:
        text_to_send += _("**ETA:** {torrent_eta}\n"
            .format(
                torrent_eta=convert_eta(int(torrent.eta))
            )
        )

    text_to_send += _("**Ratio:** {ratio}\n").format(ratio=format_ratio(torrent.ratio))
    text_to_send += _("**Seeded:** {seeded}\n").format(seeded=format_seeding_days(torrent.seeding_time))

    if torrent.category:
        text_to_send += _("**Category:** {torrent_category}\n"
            .format(
                torrent_category=torrent.category
            )
        )

    return text_to_send


def build_torrent_info_keyboard(torrent_hash: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("🔄 Refresh"),
                    callback_data=RefreshTorrentInfo(torrent_hash=torrent_hash).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("💾 Export torrent"),
                    callback_data=Export(torrent_hash=torrent_hash).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("📝 Edit Category"),
                    callback_data=EditTorrentCategory(torrent_hash=torrent_hash).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("⏸ Pause"),
                    callback_data=Pause(torrent_hash=torrent_hash).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("▶️ Resume"),
                    callback_data=Resume(torrent_hash=torrent_hash).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("🗑 Delete"),
                    callback_data=DeleteOne(torrent_hash=torrent_hash).pack()
                )
            ],
            [
                InlineKeyboardButton(
                    text=_("🔙 Menu"),
                    callback_data=Menu().pack()
                )
            ]
        ]
    )


async def show_torrent_info(bot: Bot, chat_id: int, message_id: int, settings: Settings, torrent_hash: str) -> None:
    repository_class = ClientRepo.get_client_manager(settings.client.type)
    torrent = await repository_class(settings).get_torrent(torrent_hash)

    if torrent is None:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=_("Torrent not found"),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=_("🔙 Menu"), callback_data=Menu().pack())]
                ]
            ),
        )
        return

    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=build_torrent_info_text(torrent),
            reply_markup=build_torrent_info_keyboard(torrent_hash),
        )
    except TelegramBadRequest as exc:
        if "message is not modified" not in str(exc).lower():
            raise


def get_router():
    router = Router()

    @router.callback_query(TorrentInfo.filter())
    async def torrent_info_callback(callback_query: CallbackQuery, callback_data: TorrentInfo, settings: Settings, bot: Bot) -> None:
        await callback_query.answer()
        await show_torrent_info(
            bot,
            callback_query.from_user.id,
            callback_query.message.message_id,
            settings,
            callback_data.torrent_hash,
        )


    @router.callback_query(RefreshTorrentInfo.filter())
    async def refresh_torrent_info_callback(
        callback_query: CallbackQuery,
        callback_data: RefreshTorrentInfo,
        settings: Settings,
        bot: Bot,
    ) -> None:
        await callback_query.answer()
        await show_torrent_info(
            bot,
            callback_query.from_user.id,
            callback_query.message.message_id,
            settings,
            callback_data.torrent_hash,
        )


    @router.callback_query(Export.filter())
    async def export_callback(callback_query: CallbackQuery, callback_data: Export, settings: Settings, bot: Bot) -> None:
        await callback_query.answer()
        repository_class = ClientRepo.get_client_manager(settings.client.type)
        file_bytes = await repository_class(settings).export_torrent(callback_data.torrent_hash)

        await bot.send_document(
            callback_query.from_user.id,
            BufferedInputFile(file_bytes.read(), file_bytes.name)
        )


    @router.callback_query(EditTorrentCategory.filter())
    async def edit_torrent_cateogry(callback_query: CallbackQuery, callback_data: EditTorrentCategory, settings: Settings, bot: Bot):
        await callback_query.answer()
        await list_categories(bot, callback_query.from_user.id, callback_query.message.message_id, settings, f"torrent_cat:{callback_data.torrent_hash}")

    return router
