from dataclasses import dataclass
from datetime import datetime as dt
from typing import Optional

@dataclass
class WaitlistEntry:
    id: Optional[int]
    game_id: int
    user_id: int
    status: str  # 'pending', 'approved', 'rejected'
    created_at: Optional[dt] = None