from database.db_manager import DatabaseManager
from models.game import Game
from typing import List
from datetime import datetime, timedelta

class GameService:
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_game(self, creator_id: int, location: str, game_datetime: datetime, 
                   skill_range: str, max_players: int) -> int:
        game = Game(
            id=None,
            creator_id=creator_id,
            location=location,
            datetime=game_datetime,
            skill_range=skill_range,
            max_players=max_players,
            current_players=1,  # Creator is first player
            status='open'
        )
        return self.db.create_game(game)
    
    def get_available_games(self) -> List[Game]:
        return self.db.get_open_games()
    
    def get_game(self, game_id: int) -> Game:
        return self.db.get_game(game_id)
    
    def join_waitlist(self, game_id: int, user_id: int) -> bool:
        # Check if user is already in the game
        game = self.db.get_game(game_id)
        if not game:
            return False
        
        return self.db.add_to_waitlist(game_id, user_id)
    
    def get_game_waitlist(self, game_id: int):
        return self.db.get_waitlist_for_game(game_id)
    
    def approve_player(self, game_id: int, user_id: int) -> bool:
        return self.db.approve_waitlist_entry(game_id, user_id)
    
    def reject_player(self, game_id: int, user_id: int):
        self.db.reject_waitlist_entry(game_id, user_id)
    
    def get_user_games(self, user_id: int) -> List[Game]:
        return self.db.get_user_games(user_id)
    
    def leave_game(self, game_id: int, user_id: int) -> bool:
        return self.db.remove_player_from_game(game_id, user_id)
    
    def update_game_group(self, game_id: int, group_id: int):
        self.db.update_game_group(game_id, group_id)