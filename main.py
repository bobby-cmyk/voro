import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from handlers.user_handler import UserHandler
from handlers.game_handler import GameHandler
from handlers.waitlist_handler import WaitlistHandler
from services.notification_service import NotificationService
from datetime import datetime as dt
from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class Voro:
    def __init__(self, token: str):
        self.token = token
        self.app = Application.builder().token(token).build()
        
        # Initialize handlers
        self.user_handler = UserHandler()
        self.game_handler = GameHandler()
        self.waitlist_handler = WaitlistHandler()
        self.notification_service = NotificationService()
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup command and callback handlers"""
        
        # Command handlers
        self.app.add_handler(CommandHandler("start", self.user_handler.start))
        self.app.add_handler(CommandHandler("setskill", self.user_handler.setskill))
        self.app.add_handler(CommandHandler("setdisplayname", self.user_handler.setdisplayname))
        self.app.add_handler(CommandHandler("setbio", self.user_handler.setbio))
        self.app.add_handler(CommandHandler("deleteprofile", self.user_handler.deleteprofile))
        self.app.add_handler(CommandHandler("profile", self.user_handler.profile))
        self.app.add_handler(CommandHandler("find", self.game_handler.find_games))
        self.app.add_handler(CommandHandler("create", self.game_handler.create_game))
        self.app.add_handler(CommandHandler("mygames", self.game_handler.my_games))

         # Pattern-based handlers for dynamic commands (these need MessageHandler with regex)
        # Game-related pattern handlers
        self.app.add_handler(MessageHandler(
            filters.Regex(r'^/cancel_\w+$'), 
            self.game_handler.cancel_game
        ))
        
        self.app.add_handler(MessageHandler(
            filters.Regex(r'^/leave_\w+$'), 
            self.game_handler.leave_game
        ))
        
        # Waitlist-related pattern handlers
        self.app.add_handler(MessageHandler(
            filters.Regex(r'^/waitlist_\w+$'), 
            self.waitlist_handler.get_waitlist_for_game
        ))
        
        self.app.add_handler(MessageHandler(
            filters.Regex(r'^/approve_\w+_\w+$'), 
            self.waitlist_handler.approve_waitlist_player
        ))
        
        self.app.add_handler(MessageHandler(
            filters.Regex(r'^/reject_\w+_\w+$'), 
            self.waitlist_handler.reject_waitlist_player
        ))

        # Profile viewing pattern handler
        self.app.add_handler(MessageHandler(
            filters.Regex(r'^/profile_\w+$'), 
            self.user_handler.view_user_profile  # You'll need this method
        ))
        
        # Job queue for reminders (runs daily at 10 AM)
        job_queue = self.app.job_queue
        job_queue.run_daily(
            self.notification_service.send_game_reminders,
            time=dt.strptime("10:00", "%H:%M").time(),
            name="daily_reminders"
        )
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Voro...")
        self.app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    bot = Voro(BOT_TOKEN)
    bot.run()