import sqlite3
from typing import List, Optional
from datetime import datetime
from models.game import Game
from models.user import User
from models.waitlist import WaitlistEntry
from datetime import datetime as dt

class DatabaseManager:
    def __init__(self, db_path: str = "voro.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:

            # modified: created_at is now a timestamp with no default value
            # modified: skill_level is now a float
            # modified: first_name is now display_name
            # modified: telegram_id is now a TEXT data type
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    skill_level REAL DEFAULT 0.0,
                    bio TEXT,
                    games_completed INTEGER DEFAULT 0,
                    created_at INTEGER NOT NULL
                )
            ''')

            # change skill range to min_skill and max_skill
            # change datetime to timestamp
            # Add column for game_name
            # Add column for game description
            # Add column for telegram group id
            conn.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER,
                    location TEXT NOT NULL,
                    datetime TEXT NOT NULL,
                    skill_range TEXT,
                    max_players INTEGER,
                    current_players INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'open',
                    telegram_group_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (creator_id) REFERENCES users (telegram_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS waitlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER,
                    user_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_id) REFERENCES games (id),
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                    UNIQUE(game_id, user_id)
                )
            ''')
            
            # Set contraint that user id needs to be unique for each game -> check during adding
            conn.execute('''
                CREATE TABLE IF NOT EXISTS game_players (
                    game_id INTEGER,
                    user_id INTEGER,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (game_id, user_id),
                    FOREIGN KEY (game_id) REFERENCES games (id),
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
                )
            ''')

    # USER 
    
    # modified: create_user method - changed first_name to display_name
    def create_user(self, telegram_id: str, username: str, first_name: str, created_at: int) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO users (telegram_id, username, display_name, created_at)
                    VALUES (?, ?, ?, ?)
                ''', (telegram_id, username, first_name, created_at))
                return True
        except:
            return False
    
    # modified: get_user method - changed first_name to display_name
    def get_user(self, telegram_id: str) -> Optional[User]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT telegram_id, username, display_name, created_at, skill_level, bio, games_completed
                FROM users WHERE telegram_id = ?
            ''', (telegram_id,))
            row = cursor.fetchone()
            return User(*row) if row else None
    
    def update_user_skill(self, telegram_id: str, skill_level: float):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE users SET skill_level = ? WHERE telegram_id = ?
            ''', (skill_level, telegram_id))

    def update_user_display_name(self, telegram_id: str, display_name: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE users SET display_name = ? WHERE telegram_id = ?
            ''', (display_name, telegram_id))

    def update_user_bio(self, telegram_id: str, bio: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE users SET bio = ? WHERE telegram_id = ?
            ''', (bio, telegram_id))

    def delete_user(self, telegram_id: str):
        with sqlite3.connect(self.db_path) as conn:
            # Delete from game_players first to avoid foreign key constraint error
            conn.execute('''
                DELETE FROM game_players WHERE user_id = ?
            ''', (telegram_id,))
            
            # Delete from waitlist
            conn.execute('''
                DELETE FROM waitlist WHERE user_id = ?
            ''', (telegram_id,))
            
            # Finally delete from users
            conn.execute('''
                DELETE FROM users WHERE telegram_id = ?
            ''', (telegram_id,))

    # GAME

    def create_game(self, game: Game) -> int:
        # change to min_skill and max_skill
        # find out what ".isoformat" does to the datetime -> find out more about how they determine the isoformat
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO games (creator_id, location, datetime, skill_range, max_players)
                VALUES (?, ?, ?, ?, ?)
            ''', (game.creator_id, game.location, game.datetime.isoformat(), 
                  game.skill_range, game.max_players))
            game_id = cursor.lastrowid
            # Check what does the lastrowid do
            
            # Add creator as first player
            conn.execute('''
                INSERT INTO game_players (game_id, user_id) VALUES (?, ?)
            ''', (game_id, game.creator_id))
            
            return game_id
    
    def get_open_games(self) -> List[Game]:
        with sqlite3.connect(self.db_path) as conn:
            # Get creator display name
            # Get game title and description
            cursor = conn.execute('''
                SELECT id, creator_id, location, datetime, skill_range, max_players, 
                       current_players, status, telegram_group_id, created_at
                FROM games 
                WHERE status = 'open' AND datetime > datetime('now')
                ORDER BY datetime
            ''')
            games = []
            for row in cursor.fetchall():
                game = Game(*row)
                game.datetime = datetime.fromisoformat(game.datetime) if isinstance(game.datetime, str) else game.datetime
                games.append(game)
            return games
    
    def get_game(self, game_id: int) -> Optional[Game]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, creator_id, location, datetime, skill_range, max_players,
                       current_players, status, telegram_group_id, created_at
                FROM games WHERE id = ?
            ''', (game_id,))
            row = cursor.fetchone()
            if row:
                game = Game(*row)
                game.datetime = datetime.fromisoformat(game.datetime) if isinstance(game.datetime, str) else game.datetime
                return game
            return None
    
    def add_to_waitlist(self, game_id: int, user_id: int) -> bool:
        # Check if the user_id is already on the waitlist -> Done
        # Check if user is already in the game
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO waitlist (game_id, user_id) VALUES (?, ?)
                ''', (game_id, user_id))
                return True
        except sqlite3.IntegrityError:
            return False  # Already in waitlist
    
    def get_waitlist_for_game(self, game_id: int) -> List[WaitlistEntry]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT w.user_id, u.first_name, u.username, u.skill_level, w.created_at
                FROM waitlist w
                JOIN users u ON w.user_id = u.telegram_id
                WHERE w.game_id = ? AND w.status = 'pending'
                ORDER BY w.created_at
            ''', (game_id,))
            return [WaitlistEntry(*row) for row in cursor.fetchall()]
    
    def approve_waitlist_entry(self, game_id: int, user_id: int) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update waitlist status
                conn.execute('''
                    UPDATE waitlist SET status = 'approved' 
                    WHERE game_id = ? AND user_id = ?
                ''', (game_id, user_id))
                
                # Add to game players
                conn.execute('''
                    INSERT INTO game_players (game_id, user_id) VALUES (?, ?)
                ''', (game_id, user_id))
                
                # Update current players count
                conn.execute('''
                    UPDATE games SET current_players = current_players + 1
                    WHERE id = ?
                ''', (game_id,))
                
                # Check if game is now full
                cursor = conn.execute('''
                    SELECT current_players, max_players FROM games WHERE id = ?
                ''', (game_id,))
                current, max_players = cursor.fetchone()
                
                if current >= max_players:
                    conn.execute('''
                        UPDATE games SET status = 'full' WHERE id = ?
                    ''', (game_id,))
                
                return True
        except:
            return False
    
    def reject_waitlist_entry(self, game_id: int, user_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE waitlist SET status = 'rejected' 
                WHERE game_id = ? AND user_id = ?
            ''', (game_id, user_id))

    # Add a method to remove from the waitlist -> leave the waitlist
    
    def get_user_games(self, user_id: int) -> List[Game]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT g.id, g.creator_id, g.location, g.datetime, g.skill_range, 
                       g.max_players, g.current_players, g.status, g.telegram_group_id, g.created_at
                FROM games g
                JOIN game_players gp ON g.id = gp.game_id
                WHERE gp.user_id = ? AND g.status IN ('open', 'full')
                ORDER BY g.datetime
            ''', (user_id,))
            games = []
            for row in cursor.fetchall():
                game = Game(*row)
                game.datetime = datetime.fromisoformat(game.datetime) if isinstance(game.datetime, str) else game.datetime
                games.append(game)
            return games
    
    def remove_player_from_game(self, game_id: int, user_id: int) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Remove from game players
                conn.execute('''
                    DELETE FROM game_players WHERE game_id = ? AND user_id = ?
                ''', (game_id, user_id))
                
                # Update current players count
                conn.execute('''
                    UPDATE games SET current_players = current_players - 1
                    WHERE id = ?
                ''', (game_id,))
                
                # If game was full, make it open again
                conn.execute('''
                    UPDATE games SET status = 'open' 
                    WHERE id = ? AND status = 'full'
                ''', (game_id,))
                
                return True
        except:
            return False
    
    # Remove this method and add telegram group id method
    def update_game_group(self, game_id: int, group_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE games SET telegram_group_id = ? WHERE id = ?
            ''', (group_id, game_id))

    def get_upcoming_games_with_players(self, hours_start=23, hours_end=25) -> List[dict]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f'''
                SELECT g.id, g.location, g.datetime, g.creator_id, gp.user_id, u.first_name
                FROM games g
                JOIN game_players gp ON g.id = gp.game_id
                JOIN users u ON gp.user_id = u.telegram_id
                WHERE g.datetime BETWEEN datetime('now', '+{hours_start} hours') AND datetime('now', '+{hours_end} hours')
                AND g.status IN ('open', 'full')
            ''')
            
            games_players = cursor.fetchall()

            # Group into structured dict
            games_dict = {}
            for game_id, location, datetime_str, creator_id, user_id, first_name in games_players:
                if game_id not in games_dict:
                    games_dict[game_id] = {
                        'location': location,
                        'datetime': datetime_str,
                        'creator_id': creator_id,
                        'players': []
                    }
                games_dict[game_id]['players'].append((user_id, first_name))
            return games_dict