from aiogram.filters.callback_data import CallbackData


class TorrentInfo(CallbackData, prefix="torrentInfo"):
    torrent_hash: str


class RefreshTorrentInfo(CallbackData, prefix="refresh_torrent"):
    torrent_hash: str


class Export(CallbackData, prefix="export"):
    torrent_hash: str

class EditTorrentCategory(CallbackData, prefix="edit_torrent_cat"):
    torrent_hash: str
