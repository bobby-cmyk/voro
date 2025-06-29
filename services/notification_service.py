from telegram.ext import ContextTypes
from database.db_manager import DatabaseManager
from datetime import datetime, timedelta

class NotificationService:
    def __init__(self):
        self.db = DatabaseManager()
    
    async def send_game_reminders(self, context: ContextTypes.DEFAULT_TYPE):
        """Send reminders for games happening in 24 hours"""
        try:
            games_dict = self.db.get_upcoming_games_with_players()

            for game_id, game_info in games_dict.items():
                game_time = datetime.fromisoformat(game_info['datetime'])
                formatted_time = game_time.strftime('%d/%m/%Y at %I:%M %p')

                reminder_text = (
                    f"⏰ **Game Reminder!**\n\n"
                    f"Your tennis game is in 24 hours:\n"
                    f"📍 {game_info['location']}\n"
                    f"📅 {formatted_time}\n\n"
                    f"Don't forget to:\n"
                    f"☐ Check the weather\n"
                    f"☐ Bring your racket\n"
                    f"☐ Arrive 10 minutes early\n\n"
                    f"See you on the court! 🎾"
                )

                for user_id, first_name in game_info['players']:
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=reminder_text,
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        print(f"Failed to send reminder to {user_id}: {e}")

        except Exception as e:
            print(f"Error sending game reminders: {e}")
