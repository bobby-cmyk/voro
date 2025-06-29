from telegram import Update
from telegram.ext import ContextTypes
from services.user_service import UserService
from datetime import datetime as dt

class UserHandler:
    def __init__(self):
        self.user_service = UserService()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user

        # Check if user already exists in database
        existing_user = self.user_service.get_user(user.id)

        if existing_user:
            # User already exists, no need to create again
            await update.message.reply_text(
                f"<b>👋 Hey, {existing_user.display_name}!</b>\n\n"
                f"/find - <i>Find available games</i>\n"
                f"/create - <i>Create a new game</i>\n"
                f"/mygames - <i>View your upcoming games</i>\n"
                f"/profile - <i>View your profile</i>\n",
                parse_mode='HTML'
            )
            return
        
        # Create/update user in database
        self.user_service.create_or_update_user(
            str(user.id), user.username, user.first_name
        )
        
        await update.message.reply_text(
            f"<b>🎾 Welcome to Voro, {user.first_name}!</b>\n\n"
            f"<i>Find tennis games, create your own, and connect with players in your area.</i>\n\n"
            f"<b>Get started by setting up your profile!</b>\n\n"
            f"/setskill - <i>Set your skill level</i>\n"
            f"/setbio - <i>Set your bio</i>\n"
            f"/setdisplayname - <i>Set your display name</i>\n",
            parse_mode='HTML'
        )

    # added: profile method to view user profile
    async def profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = str(update.effective_user.id)
        user_data = self.user_service.get_user(telegram_id)

        if not user_data:
            await update.message.reply_text("⚠️ No account found. /start to create account.")
            return
        

        await update.message.reply_text(
            f"<b>Your Profile</b>\n"
            f"👤 Display Name: {user_data.display_name}\n"
            f"⭐ Skill Level: {user_data.skill_level}\n"
            f"📋 Bio: {user_data.bio or "No bio set"}\n"
            f"🎾 Games Completed: {user_data.games_completed}\n"
            f"📅 Joined Since: {dt.fromtimestamp(user_data.created_at).strftime("%d %b %Y")}\n\n"
            f"<b>To update your profile:</b>\n"
            f"/setskill  - <i>Set your skill level</i>\n"
            f"/setbio - <i>Set your bio</i>\n"
            f"/setdisplayname - <i>Set your display name</i>\n"           
            f"/deleteprofile - <i>Delete your profile</i>\n",
            parse_mode='HTML'
        )

    # modified: setskill method to validate skill level input between 1.0 and 7.0
    async def setskill(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                f"Please set your skill level.\n\nExample: /setskill 3.5"
            )
            return
        
        try: 

            skill_level = float(context.args[0])
            if 1.0 <= skill_level <= 7.0:
                telegram_id = str(update.effective_user.id)
                self.user_service.update_skill_level(telegram_id, skill_level)
                await update.message.reply_text(
                    f"✅ Skill level has been set to: <b>{skill_level}</b>!\n\n"
                    f"Return to your /profile\n",
                    parse_mode='HTML'
                )
            else:
                raise ValueError()
            
        except ValueError:
            await update.message.reply_text(
                f"⚠️ Please enter a valid number between 1.0 and 7.0.\n\n"
                f"Example: /setskill 3.5\n",
                parse_mode='HTML'
            )

    # added: setdisplayname method to update user's display name
    async def setdisplayname(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                f"Please provide a display name.\n\n"
                f"Example: /setdisplayname jacob\n",
                parse_mode='HTML'
            )
            return
        
        display_name = ' '.join(context.args)

        telegram_id = str(update.effective_user.id)

        self.user_service.update_display_name(telegram_id, display_name)
        
        await update.message.reply_text(
            f"✅ Display name has been set to: <b>{display_name}</b>!\n\n"
            f"Return to your /profile\n",
            parse_mode='HTML'
        )

    # added: setbio method to update user's bio
    async def setbio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                f"Please provide a bio.\n\n"
                f"Example: /setbio Tennis addict!\n",
                parse_mode='HTML'
            )
            return
        
        bio = ' '.join(context.args)

        telegram_id = str(update.effective_user.id)

        self.user_service.update_bio(telegram_id, bio)
        
        await update.message.reply_text(
            f"✅ Bio has been set to: <b>{bio}</b>\n\n"
            f"Return to your /profile\n",
            parse_mode='HTML'
        )
    
    # added: deleteprofile method to delete user's profile
    async def deleteprofile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text(
                "⛔️ Confirm delete with '<b>/deleteprofile yes</b>'.",
                parse_mode='HTML'
            )
            return
        
        try: 

            confirmation = context.args[0]
            if confirmation == 'yes':
                telegram_id = str(update.effective_user.id)
                self.user_service.delete_profile(telegram_id)
                await update.message.reply_text(
                    f"Your profile has been deleted successfully. Goodbye! 👋"
                )
            else:
                raise ValueError()
            
        except ValueError:
            await update.message.reply_text(
                f"⚠️ Unsuccessful. Profile was <b>not</b> deleted.\n\n"
                f"To delete your profile, please confirm with '<b>/deleteprofile yes</b>'\n",
                parse_mode='HTML'
            )
    
    
