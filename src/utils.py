from math import log, floor
import datetime
import re

import psutil

from src.settings.user import User


def get_user_from_config(user_id: int, settings: "Settings") -> User:
    return next(
        iter(
            [i for i in settings.users if i.user_id == user_id]
        ), None
    )


def convert_size(size_bytes) -> str:
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(floor(log(size_bytes, 1024)))
    p = pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def convert_eta(n) -> str:
    return str(datetime.timedelta(seconds=n))


def format_ratio(ratio: float | int) -> str:
    return f"{float(ratio):.2f}"


def format_seeding_days(seconds: int) -> str:
    from aiogram.utils.i18n import ngettext

    if seconds <= 0:
        return ngettext("{days} day", "{days} days", 0).format(days=0)

    days = seconds / 86400
    if days < 1:
        return ngettext("{days} day", "{days} days", 0).format(days=0)

    whole_days = int(days)
    return ngettext("{days} day", "{days} days", whole_days).format(days=whole_days)


def get_stats_text() -> str:
    from aiogram.utils.i18n import gettext as _

    try:
        cpu_temp = psutil.sensors_temperatures()['coretemp'][0].current
    except KeyError:
        cpu_temp = 0

    return _(
        "**============SYSTEM============**\n**CPU Usage:** {cpu_usage}%\n"
        "**CPU Temp:** {cpu_temp}°C\n**Free Memory:** {free_memory} of {total_memory} ({memory_percent}%)\n"
        "**Disks usage:** {disk_used} of {disk_total} ({disk_percent}%)"
        .format(
            cpu_usage=psutil.cpu_percent(interval=None),
            cpu_temp=cpu_temp,
            free_memory=convert_size(psutil.virtual_memory().available),
            total_memory=convert_size(psutil.virtual_memory().total),
            memory_percent=psutil.virtual_memory().percent,
            disk_used=convert_size(psutil.disk_usage('/mnt').used),
            disk_total=convert_size(psutil.disk_usage('/mnt').total),
            disk_percent=psutil.disk_usage('/mnt').percent
        )
    )


def format_progress(progress: float, width: int = 20) -> str:
    """
    progress: float from 0.0 to 1.0
    """
    progress = max(0.0, min(progress, 1.0))
    filled = int(progress * width)

    bar = "█" * filled + "░" * (width - filled)
    percent = int(progress * 100)

    return f"{percent:3d}%|{bar}|\n"


def inejct_new_config_data(json_data: dict):
    json_data['redis'] = {
        'url': None
    }

    for index, i in enumerate(json_data['users']):
        i['notification_filter'] = []
        json_data['users'][index] = i


def escape_markdown(text: str):
    # Characters that need escaping in Telegram MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)
