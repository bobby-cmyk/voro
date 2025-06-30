from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.game_service import GameService
from services.user_service import UserService
from datetime import datetime, timedelta
import re
import html

class GameHandler:
    def __init__(self):
        self.game_service = GameService()
        self.user_service = UserService()
    
    async def find_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        user_id = update.effective_user.id
        user = self.user_service.get_user(user_id)

        if not user:
            await update.message.reply_text(
                "⚠️ You need to create an account first! Use /start to get started."
            )
            return

        games = self.game_service.get_available_games()
        
        if not games:
            await update.message.reply_text(
                "No games available right now! 🎾\n\n"
                "Be the first to create one with /create"
            )
            return
        
        text = "🎾 <b>Available Tennis Games:</b>\n\n"
        
        for game in games:
            game_time = self.format_start_end_time(game.start_time, game.end_time)

            # Get creator's display name
            creator = self.user_service.get_user(game.creator_id)
            creator_name = html.escape(creator.display_name if creator else "Unknown Creator")
            join_link = f'https://t.me/voro_tennis_bot?start=joinwaitlist_{game.game_id}'

            game_name = html.escape(game.game_name)
            location = html.escape(game.location)
            game_description = html.escape(game.game_description)

            text += f"{game_name}\n"
            # link to the creator's profile
            text += f"👤 Hosted by: <a href='tg://user?id={game.creator_id}'>{creator_name}</a>\n"
            text += f"📅 {game_time}\n" 
            text += f"📍 {location}\n"
            text += f"💰 Court Cost: ${game.court_cost}\n"
            text += f"⭐ Skill: {game.min_skill} to {game.max_skill}\n"
            text += f"👥 {game.current_players}/{game.max_players} players\n"
            text += f"📋 Description: {game_description}\n"
            # List all players and link to their profiles
            if game.player_ids:
                players = []
                for player_id in game.player_ids:
                    player = self.user_service.get_user(player_id)
                    if player:
                        players.append(f"<a href='tg://user?id={player_id}'>{html.escape(player.display_name)}</a>")
                text += "👥 Players: " + ", ".join(players) + "\n"
            text += f"<a href=\"{join_link}\">[Join Game 🔗]</a>\n\n"
            
        await update.message.reply_text(text, parse_mode='HTML', disable_web_page_preview=True)
    
    # modified: create_game method to handle new game creation
    async def create_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Check if user is registered
        user_id = update.effective_user.id
        user = self.user_service.get_user(user_id)

        if not user:
            await update.message.reply_text(
                "⚠️ You need to create an account first! Use /start to get started."
            )
            return

        if not context.args:
            await update.message.reply_text(
                "Let's create a tennis game! 🎾\n\n"
                "Please provide the details in this <b>EXACT</b> format:\n\n"
                "<i>COPY and PASTE example below:</i>\n\n",
                parse_mode='HTML'
            )
            await update.message.reply_text(
                "/create\n"
                "Name: chillax doubles rally\n"
                "Location: Pasir Ris Sports Center\n"
                "Start Time: 30/06/2025, 1900\n"
                "End Time: 30/06/2025, 2000\n"
                "Min Skill: 3.0\n"
                "Max Skill: 4.0\n"
                "Max Players: 4\n"
                "Court Cost: 10\n"
                "Description: rally, then match. will provide balls but please bring balls too.\n\n",
            )
            return
        
        try:
            data = self.parse_structured_input(update.message.text.replace("/create", "").strip())

            self.game_service.create_game(
                game_name=data["name"],
                creator_id=user_id,
                location=data["location"],
                start_time=data["start_time"],
                end_time=data["end_time"],
                court_cost=data["court_cost"],
                min_skill=data["min_skill"],
                max_skill=data["max_skill"],
                max_players=data["max_players"],
                game_description=data["description"]        
            )
            
            # Calculate duration
            formatted_time = self.format_start_end_time(data["start_time"], data["end_time"])
            
            await update.message.reply_text(
                f"✅ <b>Game Created Successfully!</b>\n\n"
                f"<b>{html.escape(data['name'])}</b>\n"
                f"📍 {html.escape(data['location'])}\n"
                f"📅 {formatted_time}\n"
                f"⭐ Skill Level: {data['min_skill']} to {data['max_skill']}\n"
                f"💰 Court Cost: ${data['court_cost']}\n"
                f"👥 Players: 1/{data['max_players']} (You're in!)\n"
                f"📋 Description: {html.escape(data['description'])}\n\n"
                f"Your game is now visible to other players.\n\n"
                f"I'll notify you when someone joins the waitlist!",
                parse_mode='HTML'
            )
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ Something went wrong. Please try again.\n"
                f"Error: {str(e)}"
            )
    
    def format_start_end_time(self, start_time: int, end_time: int) -> str:
        # Calculate the duration, if less 1 hour, show minutes, else show hours
        duration = end_time - start_time
        if duration < 3600:  # Less than 1 hour
            duration_str = f"{duration // 60} min"
        # if duration is exactly hours whole number, show as hours, else show as hours and minutes
        elif duration % 3600 == 0:
            duration_str = f"{duration // 3600} hr"
        else:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            duration_str = f"{hours} hr {minutes} min"

        """Format start and end time for display"""
        start_dt = datetime.fromtimestamp(start_time)
        end_dt = datetime.fromtimestamp(end_time)
        return f"{start_dt.strftime('%a, %d %b %Y, %I:%M %p')} - {end_dt.strftime('%I:%M %p')} | Duration: {duration_str}"

    def parse_structured_input(self, text: str) -> dict:
        # Split and clean
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        fields = {}

        expected_keys = [
            "Name", "Location", "Start Time", "End Time", "Min Skill",
            "Max Skill", "Max Players", "Court Cost", "Description"
        ]
        if len(lines) != len(expected_keys):
            raise ValueError("Please fill in all fields using the template. One or more fields are missing.")

        # Line-by-line parsing
        for i, key in enumerate(expected_keys):
            if ":" not in lines[i]:
                raise ValueError(f"Field '{key}' is missing or malformed.")
            k, v = lines[i].split(":", 1)
            if k.strip() != key:
                raise ValueError(f"Expected field '{key}' but got '{k.strip()}'. Please follow the exact template.")
            fields[key] = v.strip()

        # Validation
        if not fields["Name"]:
            raise ValueError("Name cannot be empty.")
        if not fields["Location"]:
            raise ValueError("Location cannot be empty.")

        # Start and End Time
        try:
            start_datetime = datetime.strptime(fields["Start Time"], "%d/%m/%Y, %H%M")
        except:
            raise ValueError("Invalid Start Time format. Please use: `DD/MM/YYYY, HHMM`.")

        try:
            end_datetime = datetime.strptime(fields["End Time"], "%d/%m/%Y, %H%M")
        except:
            raise ValueError("Invalid End Time format. Please use: `DD/MM/YYYY, HHMM`.")

        if start_datetime <= datetime.now():
            raise ValueError("Start Time must be in the future.")
        if end_datetime <= start_datetime:
            raise ValueError("End Time must be after Start Time.")

        # Skill validation
        try:
            min_skill = float(fields["Min Skill"])
            max_skill = float(fields["Max Skill"])
            if not (0.0 <= min_skill <= 7.0):
                raise ValueError("Min Skill must be between 0.0 and 7.0.")
            if not (0.0 <= max_skill <= 7.0):
                raise ValueError("Max Skill must be between 0.0 and 7.0.")
            if min_skill > max_skill:
                raise ValueError("Min Skill cannot be greater than Max Skill.")
        except:
            raise ValueError("Min and Max Skill must be valid numbers between 0.0 and 7.0.")

        # Max Players
        try:
            max_players = int(fields["Max Players"])
            if not (2 <= max_players <= 4):
                raise ValueError("Max Players must be between 2 and 4.")
        except:
            raise ValueError("Max Players must be a number.")

        # Court Cost
        try:
            court_cost = float(fields["Court Cost"])
            if court_cost < 0:
                raise ValueError("Court Cost must be 0 or more.")
        except:
            raise ValueError("Court Cost must be a number.")

        if not fields["Description"]:
            raise ValueError("Description cannot be empty.")

        return {
            "name": fields["Name"],
            "location": fields["Location"],
            # Conver start and end times to datetime objects
            "start_time": int(start_datetime.timestamp()),
            "end_time": int(end_datetime.timestamp()),
            "min_skill": min_skill,
            "max_skill": max_skill,
            "max_players": max_players,
            "court_cost": court_cost,
            "description": fields["Description"]
        }

    async def my_games(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        games = self.game_service.get_user_games(user_id)
        
        if not games:
            await update.message.reply_text(
                "You don't have any upcoming games! 🎾\n\n"
                "Use /find to join some games or /create to organize one."
            )
            return
        
        text = "🎾 <b>Your Upcoming Games:</b>\n\n"
        
        for game in games:
            game_time = self.format_start_end_time(game.start_time, game.end_time)
            # Get creator's display name
            creator = self.user_service.get_user(game.creator_id)
            creator_name = creator.display_name if creator else "Unknown Creator"
            
            creator_text = "👑 Your game" if game.creator_id == user_id else f"🎾 Joined <a href='tg://user?id={game.creator_id}'>{creator_name}</a>'s game"
            
            text += f"{creator_text}\n"
            text += f"{html.escape(game.game_name)}\n"
            # link to the creator's profile
            text += f"📅 {game_time}\n" 
            text += f"📍 {html.escape(game.location)}\n"
            text += f"💰 Court Cost: ${game.court_cost}\n"
            text += f"⭐ Skill: {game.min_skill} to {game.max_skill}\n"
            text += f"👥 {game.current_players}/{game.max_players} players\n"
            text += f"📋 Description: {html.escape(game.game_description)}\n"
            # List all players and link to their profiles
            if game.player_ids:
                players = []
                for player_id in game.player_ids:
                    player = self.user_service.get_user(player_id)
                    if player:
                        players.append(f"<a href='tg://user?id={player_id}'>{html.escape(player.display_name)}</a>")
                text += "👥 Players: " + ", ".join(players) + "\n"
            text += f"📊 Status: {game.status.title()}\n"

            # If the user is the creator, provide a delete option
            if game.creator_id == user_id:
                text += f"⏳ <b>View Waitlist</b> [/waitlist_{game.game_id}]\n"
                text += f"❌ <b>Cancel</b> [/cancel_{game.game_id}]\n\n"
                
            else:
                text += f"[🚪 <b>Leave</b> /leave_{game.game_id}]\n\n"

        await update.message.reply_text(text, parse_mode='HTML')

    async def cancel_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        game_id = re.search(r'cancel_(\w+)', update.message.text).group(1)

        game = self.game_service.get_game(game_id)

        if not game:
            await update.message.reply_text("❌ Game not found or has already been cancelled.")
            return

        if game.creator_id != user_id:
            await update.message.reply_text("❌ You can only cancel games you created.")
            return

        success = self.game_service.cancel_game(game_id)
        
        if success:
            await update.message.reply_text(
                f"✅ <b>Game Cancelled Successfully!</b>\n\n"
                f"{html.escape(game.game_name)} has been cancelled. All players have been notified.",
                parse_mode='HTML'
            )
            
            # Notify all players in the game
            for player_id in game.player_ids:
                
                # skip the creator since they are already notified
                if player_id == user_id:
                    continue

                player = self.user_service.get_user(player_id)
                if player:
                    await context.bot.send_message(
                        chat_id=player.telegram_id,
                        text=f"📢 <b>Game Cancelled</b>\n\n"
                             f"The game <b>{html.escape(game.game_name)}</b> you joined has been cancelled by the host.\n"
                             f"Please check /find for other available games.",
                        parse_mode='HTML'
                    )
        else:
            await update.message.reply_text("❌ Could not cancel the game. Please try again.")


    async def leave_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        game_id = re.search(r'leave_(\w+)', update.message.text).group(1)

        success = self.game_service.leave_game(game_id, user_id)
        
        if success:
            await update.message.reply_text(
                f"<b>Left the game successfully</b>\n\n"
                f"Only join games you can attend! 🎾",
                parse_mode='HTML'
            )
            game = self.game_service.get_game(game_id)
            user = self.user_service.get_user(user_id)

            # formatted start and end time
            game_time = self.format_start_end_time(game.start_time, game.end_time)
            
            # Notify game creator
            await context.bot.send_message(
                # get the game object
                
                chat_id=game.creator_id,
                text=f"📢 <b>Player Left Your Game</b>\n\n"
                     f"👤 <a href='tg://user?id={user.telegram_id}'>{html.escape(user.display_name)}</a> has left the game:\n"
                     f"🎾 {html.escape(game.game_name)}\n"
                     f"📍 {html.escape(game.location)}\n"
                     f"📅 {game_time}\n\n"
                     f"Current players: {game.current_players}/{game.max_players}\n"
                     f"Your game is now open for new players!"
            )
        else:
            await update.message.reply_text("❌ Could not leave the game. Please try again.")

    