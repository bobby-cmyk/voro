from database.db_manager import DatabaseManager
from models.user import User
from datetime import datetime

class UserService:
    def __init__(self):
        self.db = DatabaseManager()
    
    # modified: create_or_update_user method - changed first_name to display_name
    def create_or_update_user(self, telegram_id: str, username: str, first_name: str) -> bool:
        created_at = int(datetime.now().timestamp())
        return self.db.create_user(telegram_id, username, first_name, created_at)
    
    def get_user(self, telegram_id: str) -> User:
        return self.db.get_user(telegram_id)
    
    # modified: update_skill_level method - changed skill_level to float
    def update_skill_level(self, telegram_id: str, skill_level: float):
        self.db.update_user_skill(telegram_id, skill_level)

    # added: update_display_name method
    def update_display_name(self, telegram_id: str, display_name: str):
        self.db.update_user_display_name(telegram_id, display_name)

    # added: update_bio method
    def update_bio(self, telegram_id: str, bio: str):
        self.db.update_user_bio(telegram_id, bio)

    # added: delete_profile method
    def delete_profile(self, telegram_id: str):
        self.db.delete_user(telegram_id)