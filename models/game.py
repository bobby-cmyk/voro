from dataclasses import dataclass, field
from datetime import datetime as dt
from typing import Optional

@dataclass
class Game:
    game_id: str
    game_name: str
    creator_id: str
    location: str
    start_time: int
    end_time: int
    court_cost: float
    min_skill: float
    max_skill: float
    max_players: int
    current_players: int
    status: str  # 'open', 'full', 'completed'
    telegram_group_id: str
    created_at: int
    game_description: str
    player_ids: list[str] = field(default_factory=list)