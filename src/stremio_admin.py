import json
import logging

import aiohttp

from src.settings import Settings

logger = logging.getLogger(__name__)

ACTION_STREMIO_TOKEN = "stremio_admin_token"


def mask_token(token: str) -> str:
    if len(token) <= 4:
        return "****"
    return f"{'*' * (len(token) - 4)}{token[-4:]}"


def update_admin_scan_token(settings: Settings, token: str) -> None:
    settings.stremio.admin_scan_token = token.strip()
    settings.export_settings()


async def post_admin_action(settings: Settings, path: str) -> tuple[bool, str]:
    token = settings.stremio.admin_scan_token
    if not token:
        return False, "Admin scan token is not configured"

    url = f"{settings.stremio.admin_base_url.unicode_string().rstrip('/')}{path}"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers) as response:
                body = await response.text()

                if response.status >= 400:
                    return False, f"HTTP {response.status}: {body}"

                try:
                    payload = json.loads(body)
                    return True, json.dumps(payload, indent=2)
                except json.JSONDecodeError:
                    return True, body or "OK"

    except Exception as exc:
        logger.exception("Stremio admin request failed")
        return False, str(exc)
