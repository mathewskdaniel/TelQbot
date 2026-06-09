from dataclasses import dataclass
from typing import Union


@dataclass
class Torrent:
    hash: str
    name: str
    progress: int
    dlspeed: int
    upspeed: int
    state: str
    size: int
    eta: int
    ratio: float
    seeding_time: int
    category: Union[str, None]
