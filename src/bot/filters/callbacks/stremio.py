from aiogram.filters.callback_data import CallbackData


class StremioMenu(CallbackData, prefix="stremio_menu"):
    pass


class StremioScan(CallbackData, prefix="stremio_scan"):
    pass


class StremioRebuild(CallbackData, prefix="stremio_rebuild"):
    pass


class StremioRebuildConfirm(CallbackData, prefix="stremio_rebuild_yes"):
    pass


class StremioUpdateToken(CallbackData, prefix="stremio_update_token"):
    pass
