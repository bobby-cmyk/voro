from dataclasses import dataclass
from datetime import datetime as dt
from typing import Optional

@dataclass
class WaitlistEntry:
    waitlist_id: Optional[int]  # Changed from 'id' to match database column
    game_id: str              # Changed from int to str to match database
    user_id: str              # Changed from int to str to match database  
    status: str               # 'pending', 'approved', 'rejected'
    created_at: int           # Changed to int timestamp to match database
    
    # Additional fields that appear to be used in get_waitlist_for_game method
    username: Optional[str] = None
    display_name: Optional[str] = None  
    skill_level: Optional[float] = None