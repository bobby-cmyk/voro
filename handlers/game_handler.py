from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.game_service import GameService
from services.user_service import UserService
from datetime import datetime, timedelta
import re

class GameHandler:
    def __init__(self):
        self.game_service = GameService()
        self.user_service = UserService()
    
    async def find_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show available games"""
        games = self.game_service.get_available_games()
        
        if not games:
            await update.message.reply_text(
                "No games available right now! 🎾\n\n"
                "Be the first to create one with /create"
            )
            return
        
        text = "🎾 **Available Tennis Games:**\n\n"
        keyboard = []
        
        for game in games:
            game_time = game.datetime.strftime("%d/%m %I:%M %p")
            spots_left = game.max_players - game.current_players
            
            text += f'Hosted by {game.creator_name}\n'
            text += f"📍 **{game.location}**\n"
            text += f"📅 {game_time}\n" 
            text += f"⭐ Skill: {game.skill_range}\n"
            text += f"👥 {game.current_players}/{game.max_players} players\n"
            
            keyboard.append([InlineKeyboardButton(
                f"Join Waitlist - {game.location[:20]}", 
                callback_data=f"join_{game.id}"
            )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def create_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create a new game"""
        if not context.args:
            await update.message.reply_text(
                "Let's create a tennis game! 🎾\n\n"
                "**Format:**\n"
                "`/create Marina Bay Courts, Tomorrow 7PM, 3.0-4.0, 4`\n\n"
                "**Parameters:**\n"
                "1. Location\n"
                "2. Date/Time (Tomorrow 7PM, Friday 6PM, etc.)\n"
                "3. Skill Range\n"
                "4. Max Players (2-4)\n\n"
                "**Example:**\n"
                "`/create Jurong East Courts, Today 8PM, 3.5-4.0, 4`",
                parse_mode='Markdown'
            )
            return
        
        try:
            # Parse the input
            full_text = " ".join(context.args)
            parts = [part.strip() for part in full_text.split(",")]
            
            if len(parts) != 4:
                raise ValueError("Invalid format")
            
            location = parts[0]
            time_str = parts[1]
            skill_range = parts[2]
            max_players = int(parts[3])
            
            if max_players < 2 or max_players > 4:
                raise ValueError("Max players must be between 2 and 4")
            
            # Parse time (simplified - you might want to use a proper date parser)
            game_datetime = self.parse_time_string(time_str)
            
            if game_datetime <= datetime.now():
                raise ValueError("Game time must be in the future")
            
            # Create the game
            user_id = update.effective_user.id
            game_id = self.game_service.create_game(
                creator_id=user_id,
                location=location,
                game_datetime=game_datetime,
                skill_range=skill_range,
                max_players=max_players
            )
            
            formatted_time = game_datetime.strftime("%d/%m/%Y at %I:%M %p")
            
            await update.message.reply_text(
                f"✅ **Game Created Successfully!**\n\n"
                f"🎾 **Game #{game_id}**\n"
                f"📍 {location}\n"
                f"📅 {formatted_time}\n"
                f"⭐ Skill Level: {skill_range}\n"
                f"👥 Players: 1/{max_players} (You're in!)\n\n"
                f"Your game is now visible to other players. "
                f"I'll notify you when someone joins the waitlist!",
                parse_mode='Markdown'
            )
            
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Error creating game: {str(e)}\n\n"
                f"Please use the correct format:\n"
                f"`/create Location, Time, Skill Range, Max Players`",
                parse_mode='Markdown'
            )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Something went wrong. Please try again.\n"
                f"Error: {str(e)}"
            )
    
    def parse_time_string(self, time_str: str) -> datetime:
        """Parse time strings like 'Tomorrow 7PM', 'Today 8PM', 'Friday 6PM'"""
        time_str = time_str.lower().strip()
        now = datetime.now()
        
        # Extract time part (e.g., "7pm", "8:30pm")
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', time_str)
        if not time_match:
            raise ValueError("Invalid time format. Use format like '7PM' or '8:30AM'")
        
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        period = time_match.group(3)
        
        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0
        
        # Determine date
        if 'today' in time_str:
            target_date = now.date()
        elif 'tomorrow' in time_str:
            target_date = (now + timedelta(days=1)).date()
        else:
            # For now, assume it's today if no date specified
            target_date = now.date()
        
        target_datetime = datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))
        
        # If the time has already passed today, assume it's for tomorrow
        if target_datetime <= now and target_date == now.date():
            target_datetime += timedelta(days=1)
        
        return target_datetime
    
    async def my_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's games"""
        user_id = update.effective_user.id
        games = self.game_service.get_user_games(user_id)
        
        if not games:
            await update.message.reply_text(
                "You don't have any upcoming games! 🎾\n\n"
                "Use /find to join some games or /create to organize one."
            )
            return
        
        text = "🎾 **Your Upcoming Games:**\n\n"
        keyboard = []
        
        for game in games:
            game_time = game.datetime.strftime("%d/%m %I:%M %p")
            creator_text = "👑 Your game" if game.creator_id == user_id else "🎾 Joined"
            
            text += f"{creator_text}\n"
            text += f"📍 {game.location}\n"
            text += f"📅 {game_time}\n"
            text += f"👥 {game.current_players}/{game.max_players} players\n"
            text += f"📊 Status: {game.status.title()}\n\n"
            
            # Add manage button for creators, leave button for others
            if game.creator_id == user_id:
                keyboard.append([InlineKeyboardButton(
                    f"Manage Game #{game.id}", 
                    callback_data=f"manage_{game.id}"
                )])
            else:
                keyboard.append([InlineKeyboardButton(
                    f"Leave Game #{game.id}", 
                    callback_data=f"leave_{game.id}"
                )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')