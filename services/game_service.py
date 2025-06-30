from database.db_manager import DatabaseManager
from models.game import Game
from typing import List
from datetime import datetime, timedelta
from uuid import uuid4

class GameService:
    def __init__(self):
        self.db = DatabaseManager()
    
    # modified: create_game method to handle new game creation
    def create_game(self, game_name: str, creator_id: int, location: str, 
                    start_time: int, end_time: int,
                    court_cost: float, 
                    min_skill: float, max_skill: float,
                    max_players:int, game_description: str) -> str:
        
        game_id = str(uuid4()).replace("-", "")[:8]
        # get the current timestamp
        created_at = int(datetime.now().timestamp())

        game = Game(
            game_id=game_id,
            game_name=game_name,
            creator_id=creator_id,
            location=location,
            start_time=start_time,
            end_time=end_time,
            court_cost=court_cost,
            min_skill=min_skill,
            max_skill=max_skill,
            max_players=max_players,
            current_players=1,
            status='open',
            created_at=created_at,
            telegram_group_id='',  # TODO Initially empty, can be updated later
            game_description=game_description
        )
        return self.db.create_game(game)
    
    def get_available_games(self) -> List[Game]:
        return self.db.get_open_games()
    
    def get_game(self, game_id: str) -> Game:
        return self.db.get_game(game_id)
    
    def join_waitlist(self, game_id: str, user_id: str) -> bool:
        # Check if user is already in the game
        game = self.db.get_game(game_id)
        if not game:
            return False
        
        return self.db.add_to_waitlist(game_id, user_id)
    
    def get_game_waitlist(self, game_id: str):
        return self.db.get_waitlist_for_game(game_id)
    
    def approve_player(self, game_id: str, user_id: str) -> bool:
        return self.db.approve_waitlist_entry(game_id, user_id)
    
    def reject_player(self, game_id: str, user_id: str):
        self.db.reject_waitlist_entry(game_id, user_id)
    
    def get_user_games(self, user_id: str) -> List[Game]:
        return self.db.get_user_games(user_id)
    
    def leave_game(self, game_id: str, user_id: str) -> bool:
        return self.db.remove_player_from_game(game_id, user_id)
    
    def update_game_group(self, game_id: str, group_id: str):
        self.db.update_game_group(game_id, group_id)

    def check_user_on_waitlist(self, game_id: str, user_id: str) -> bool:
        return self.db.check_user_on_waitlist(game_id, user_id)
    
    def cancel_game(self, game_id: str) -> bool:
        return self.db.cancel_game(game_id)