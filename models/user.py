from dataclasses import dataclass
from datetime import datetime as dt
from typing import Optional

# modified: User model - skill_level is now a float
@dataclass
class User:
    telegram_id: str
    username: str
    display_name: str
    created_at: int
    skill_level: Optional[float] = None
    bio: Optional[str] = None
    games_completed: int = 0