import asyncio
import json
import qbittorrentapi
from typing import Any, Callable

_client_pool: dict[str, qbittorrentapi.Client] = {}
_pool_lock = asyncio.Lock()


class AsyncQbittorrentClient:
    """
    Async wrapper around qbittorrentapi.Client using asyncio.to_thread.
    """

    def __init__(self, **connection_kwargs):
        self._connection_kwargs = connection_kwargs
        self._client: qbittorrentapi.Client | None = None

    async def __aenter__(self) -> "AsyncQbittorrentClient":
        pool_key = json.dumps(self._connection_kwargs, sort_keys=True)

        async with _pool_lock:
            if pool_key not in _client_pool:
                client = qbittorrentapi.Client(**self._connection_kwargs)
                await asyncio.to_thread(client.auth_log_in)
                _client_pool[pool_key] = client

            self._client = _client_pool[pool_key]

        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def call(self, fn: Callable[..., Any], /, *args, **kwargs) -> Any:
        """
        Run a qbittorrentapi call in a thread.
        """
        if not self._client:
            raise RuntimeError("Client not initialized, use 'async with'")

        return await asyncio.to_thread(fn, *args, **kwargs)

    @property
    def client(self) -> qbittorrentapi.Client:
        if not self._client:
            raise RuntimeError("Client not initialized, use 'async with'")
        return self._client
