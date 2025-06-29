from database.db_manager import DatabaseManager
from models.user import User

class UserService:
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_or_update_user(self, telegram_id: int, username: str, first_name: str) -> bool:
        return self.db.create_user(telegram_id, username, first_name)
    
    def get_user(self, telegram_id: int) -> User:
        return self.db.get_user(telegram_id)
    
    def update_skill_level(self, telegram_id: int, skill_level: str):
        self.db.update_user_skill(telegram_id, skill_level)