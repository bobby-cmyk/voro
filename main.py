import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
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
        
        # Callback query handlers
        self.app.add_handler(CallbackQueryHandler(
            self.waitlist_handler.handle_join_waitlist, 
            pattern=r"^join_\d+$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.waitlist_handler.handle_approve_reject, 
            pattern=r"^(approve|reject)_\d+_\d+$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.waitlist_handler.show_waitlist, 
            pattern=r"^waitlist_\d+$"
        ))
        self.app.add_handler(CallbackQueryHandler(
            self.waitlist_handler.handle_leave_game, 
            pattern=r"^leave_\d+$"
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