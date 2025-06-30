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
                    skill_level REAL,
                    bio TEXT,
                    games_completed INTEGER DEFAULT 0,
                    created_at INTEGER NOT NULL
                )
            ''')

            # modified: id is now game_id and is TEXT instead of INTEGER
            # modified: creator_id is now TEXT instead of INTEGER
            # modified: datetime is now a integer timestamp
            # modified: skill_range is now min_skill and max_skill
            # modified: telegram_group_id is now TEXT
            # modified: added game description and game name

            conn.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    game_id TEXT PRIMARY KEY,
                    game_name TEXT NOT NULL,
                    game_description TEXT,
                    creator_id TEXT NOT NULL,
                    location TEXT NOT NULL,
                    start_time INTEGER NOT NULL,
                    end_time INTEGER NOT NULL,
                    court_cost REAL DEFAULT 0.0,
                    min_skill REAL DEFAULT 0.0,
                    max_skill REAL DEFAULT 7.0,
                    max_players INTEGER,
                    current_players INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'open',
                    telegram_group_id TEXT,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (creator_id) REFERENCES users (telegram_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS waitlist (
                    waitlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    status TEXT DEFAULT 'pending' NOT NULL,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (game_id) REFERENCES games (id),
                    FOREIGN KEY (user_id) REFERENCES users (telegram_id),
                    UNIQUE(game_id, user_id)
                )
            ''')
            
            # Set contraint that user id needs to be unique for each game -> check during adding
            conn.execute('''
                CREATE TABLE IF NOT EXISTS game_players (
                    game_id TEXT,
                    user_id TEXT,
                    joined_at INTEGER,
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

    # modified: create_game method - added new fields to insert
    def create_game(self, game: Game) -> str:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO games (game_id, game_name, game_description, creator_id, location, start_time, end_time, court_cost, min_skill, max_skill, max_players, current_players, status, created_at, telegram_group_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (game.game_id, game.game_name, game.game_description,
                  game.creator_id, game.location, game.start_time, game.end_time,
                  game.court_cost, game.min_skill, game.max_skill,
                  game.max_players, game.current_players, game.status,
                  game.created_at,
                  game.telegram_group_id))
            
            # Add creator as first player
            conn.execute('''
                INSERT INTO game_players (game_id, user_id) VALUES (?, ?)
            ''', (game.game_id, game.creator_id))
            
            return game.game_id
    
    # modified: get_open_games method - changed to return Game objects
    def get_open_games(self) -> List[Game]:
        with sqlite3.connect(self.db_path) as conn:
            # get current timestamp
            current_time = int(datetime.now().timestamp())

            cursor = conn.execute('''
                SELECT game_id, game_name, creator_id, location, start_time, end_time,
                    court_cost, min_skill, max_skill, max_players, current_players,
                    status, telegram_group_id, created_at, game_description
                FROM games 
                WHERE status = 'open' AND start_time > ?
                ORDER BY start_time
            ''', (current_time,))

            games = []
            for row in cursor.fetchall():
                game = Game(*row)
                player_cursor = conn.execute('''
                    SELECT user_id FROM game_players WHERE game_id = ?
                ''', (game.game_id,))
                player_rows = player_cursor.fetchall()
                print(player_rows)
                game.player_ids = [r[0] for r in player_rows]
                games.append(game)
            return games
    
    def get_game(self, game_id: str) -> Optional[Game]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT game_id, game_name, creator_id, location, start_time, end_time,
                    court_cost, min_skill, max_skill, max_players, current_players,
                    status, telegram_group_id, created_at, game_description
                FROM games WHERE game_id = ?
            ''', (game_id,))
            row = cursor.fetchone()
            # Fetch players IDs
            if row:
                game = Game(*row)
                player_cursor = conn.execute('''
                    SELECT user_id FROM game_players WHERE game_id = ?
                ''', (game_id,))
                player_rows = player_cursor.fetchall()
                game.player_ids = [r[0] for r in player_rows]
                return game
            return None
        
    def check_user_in_game(self, game_id: str, user_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT 1 FROM game_players WHERE game_id = ? AND user_id = ?
            ''', (game_id, user_id))
            return cursor.fetchone() is not None
        
    def check_user_on_waitlist(self, game_id: str, user_id: str) -> bool:
        """Fixed parameter types to match database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT 1 FROM waitlist WHERE game_id = ? AND user_id = ? AND status = 'pending'
            ''', (game_id, user_id))
            return cursor.fetchone() is not None
    
    def add_to_waitlist(self, game_id: str, user_id: str) -> bool:
        """Fixed parameter types and added timestamp"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                current_timestamp = int(dt.now().timestamp())
                conn.execute('''
                    INSERT INTO waitlist (game_id, user_id, created_at) VALUES (?, ?, ?)
                ''', (game_id, user_id, current_timestamp))
                return True
        except sqlite3.IntegrityError:
            return False  # Already in waitlist
        
    def cancel_game(self, game_id: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete from game_players
                conn.execute('''
                    DELETE FROM game_players WHERE game_id = ?
                ''', (game_id,))
                
                # Delete from waitlist
                conn.execute('''
                    DELETE FROM waitlist WHERE game_id = ?
                ''', (game_id,))
                
                # Delete from games
                conn.execute('''
                    DELETE FROM games WHERE game_id = ?
                ''', (game_id,))
                
                return True
        except:
            return False
        
    
        
    # WAITLIST
    
    def get_waitlist_for_game(self, game_id: str) -> List[WaitlistEntry]:
        """Fixed parameter type and query to match database schema"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT w.waitlist_id, w.game_id, w.user_id, w.status, w.created_at,
                    u.username, u.display_name, u.skill_level
                FROM waitlist w
                JOIN users u ON w.user_id = u.telegram_id
                WHERE w.game_id = ? AND w.status = 'pending'
                ORDER BY w.created_at
            ''', (game_id,))
            
            entries = []
            for row in cursor.fetchall():
                entry = WaitlistEntry(
                    waitlist_id=row[0],
                    game_id=row[1], 
                    user_id=row[2],
                    status=row[3],
                    created_at=row[4],
                    username=row[5],
                    display_name=row[6],
                    skill_level=row[7]
                )
                entries.append(entry)
            return entries
    
    def approve_waitlist_entry(self, game_id: str, user_id: str) -> bool:
        """Fixed parameter types and table references"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update waitlist status
                conn.execute('''
                    UPDATE waitlist SET status = 'approved' 
                    WHERE game_id = ? AND user_id = ?
                ''', (game_id, user_id))
                
                # Add to game players with timestamp
                current_timestamp = int(dt.now().timestamp())
                conn.execute('''
                    INSERT INTO game_players (game_id, user_id, joined_at) VALUES (?, ?, ?)
                ''', (game_id, user_id, current_timestamp))
                
                # Update current players count - Fixed table reference
                conn.execute('''
                    UPDATE games SET current_players = current_players + 1
                    WHERE game_id = ?
                ''', (game_id,))
                
                # Check if game is now full - Fixed table reference
                cursor = conn.execute('''
                    SELECT current_players, max_players FROM games WHERE game_id = ?
                ''', (game_id,))
                row = cursor.fetchone()
                if row:
                    current, max_players = row
                    if current >= max_players:
                        conn.execute('''
                            UPDATE games SET status = 'full' WHERE game_id = ?
                        ''', (game_id,))
                
                return True
        except Exception as e:
            print(f"Error approving waitlist entry: {e}")
            return False
    
    def reject_waitlist_entry(self, game_id: str, user_id: str):
        """Fixed parameter types"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE waitlist SET status = 'rejected' 
                WHERE game_id = ? AND user_id = ?
            ''', (game_id, user_id))

    # Add a method to remove from the waitlist -> leave the waitlist
    
    # modified: get_user_games method - changed user_id to str, return type is List[Game]
    # modified: changed query to return Game objects
    def get_user_games(self, user_id: str) -> List[Game]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT g.game_id, g.game_name, g.creator_id, g.location, g.start_time, g.end_time,
                    g.court_cost, g.min_skill, g.max_skill, g.max_players, g.current_players,
                    g.status, g.telegram_group_id, g.created_at, g.game_description
                FROM games g
                JOIN game_players gp ON g.game_id = gp.game_id
                WHERE gp.user_id = ? AND g.status IN ('open', 'full')
                ORDER BY g.start_time
            ''', (user_id,))
            games = []
            for row in cursor.fetchall():
                game = Game(*row)
                # Fetch players IDs

                player_cursor = conn.execute('''
                    SELECT user_id FROM game_players WHERE game_id = ?
                ''', (game.game_id,))
                player_rows = player_cursor.fetchall()
                game.player_ids = [r[0] for r in player_rows]

                games.append(game)
            return games
        
    # modified: remove_player_from_game method - changed game_id to str, user_id to str
    def remove_player_from_game(self, game_id: str, user_id: str) -> bool:
        """Fixed table reference in UPDATE statement"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Remove from game players
                conn.execute('''
                    DELETE FROM game_players WHERE game_id = ? AND user_id = ?
                ''', (game_id, user_id))
                
                # Update current players count - Fixed table reference
                conn.execute('''
                    UPDATE games SET current_players = current_players - 1
                    WHERE game_id = ?
                ''', (game_id,))
                
                # If game was full, make it open again - Fixed table reference
                conn.execute('''
                    UPDATE games SET status = 'open' 
                    WHERE game_id = ? AND status = 'full'
                ''', (game_id,))
                
                return True
        except Exception as e:
            print(f"Error removing player from game: {e}")
            return False
        
    def remove_from_waitlist(self, game_id: str, user_id: str) -> bool:
        """New method to remove user from waitlist entirely"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    DELETE FROM waitlist WHERE game_id = ? AND user_id = ?
                ''', (game_id, user_id))
                return True
        except:
            return False
    
    # modified: update_game_group method - changed to accept game_id as str, telegram_group_id as str
    def update_game_group(self, game_id: str, telegram_group_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE games SET telegram_group_id = ? WHERE game_id = ?
            ''', (telegram_group_id, game_id))

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