from dataclasses import dataclass
from datetime import datetime as dt
from typing import Optional

@dataclass
class Game:
    id: Optional[int]
    creator_id: int
    location: str
    datetime: dt
    skill_range: str
    max_players: int
    current_players: int
    status: str  # 'open', 'full', 'completed'
    telegram_group_id: Optional[int] = None
    created_at: Optional[dt] = None