import html
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.game_service import GameService
from services.user_service import UserService
from models.user import User
from models.game import Game

class WaitlistHandler:
    def __init__(self):
        self.game_service = GameService()
        self.user_service = UserService()
    
    async def handle_join_waitlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_id: str):
        
        user_id = str(update.effective_user.id)
        user = self.user_service.get_user(user_id)

        if not user:
            await update.message.reply_text(
                "⚠️ You need to create an account first! Use /start to get started."
            )
            return
        
        if not user.skill_level:
            await update.message.reply_text(
                "❌ Please set your skill level first!\n\n"
                "Use /setskill command to set your tennis level before joining games."
            )
            return
        
        game = self.game_service.get_game(game_id)

        if not game:
            await update.message.reply_text("❌ Game not found or has expired.")
            return

        if self.game_service.check_user_on_waitlist(game_id, user_id):
            await update.message.reply_text("🙂 You're already on the waitlist for this game.")
            return
        
        if user_id in game.player_ids:
            await update.message.reply_text("👀 You're already in the game.")
            return
        
        if len(game.player_ids) >= game.max_players:
            await update.message.reply_text("😢 Sorry, the game is full.")
            return
        
        success = self.game_service.join_waitlist(game_id, user_id)
        
        if success:
            await update.message.reply_text(
                "✅ <b>Added to waitlist!</b>\n\n"
                "I'll notify you once the game host make a decision! 🎾",
                parse_mode='HTML'
            )

            # Notify game host of new waitlist request
            await self.notify_creator_of_waitlist_request(context, game, user)

        else:
            await update.message.reply_text(
                "❌ Error occured: Could not join waitlist\n"
            )

    async def get_waitlist_for_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        game_id = re.search(r'waitlist_(\w+)', update.message.text).group(1)

        # Get the game to verify ownership
        game = self.game_service.get_game(game_id)
        
        if not game:
            await update.message.reply_text("❌ Game not found.")
            return

        if game.creator_id != user_id:
            await update.message.reply_text("❌ You can only view the waitlist for games you created.")
            return

        # Get waitlist entries
        waitlist_entries = self.game_service.get_game_waitlist(game_id)
        
        if not waitlist_entries:
            await update.message.reply_text(
                f"📋 <b>Waitlist for {html.escape(game.game_name)}</b>\n\n"
                f"No players are currently on the waitlist.\n\n"
                f"Current players: {game.current_players}/{game.max_players}",
                parse_mode='HTML'
            )
            return

        # Format game time
        game_time = self.format_start_end_time(game.start_time, game.end_time)
        
        text = f"📋 <b>Waitlist for {html.escape(game.game_name)}</b>\n\n"
        text += f"📅 {game_time}\n"
        text += f"📍 {html.escape(game.location)}\n"
        text += f"👥 Current players: {game.current_players}/{game.max_players}\n\n"
        text += f"<b>Players waiting to join ({len(waitlist_entries)}):</b>\n\n"

        for i, entry in enumerate(waitlist_entries, 1):
            # Format skill level display
            skill_display = f"{entry.skill_level}" if entry.skill_level is not None else "Not set"
            
            # Create player info with profile link
            text += f"{i}. <a href='tg://user?id={entry.user_id}'>{html.escape(entry.display_name)}</a>\n"
            text += f"   👤 @{entry.username}\n" if entry.username else f"   👤 User ID: {entry.user_id}\n"
            text += f"   ⭐ Skill Level: {skill_display}\n"
            text += f"   📋 <b>View Profile:</b> /profile_{entry.user_id}\n"
            text += f"   ✅ <b>Approve:</b> /approve_{entry.user_id}_{game_id}\n"
            text += f"   ❌ <b>Reject:</b> /reject_{entry.user_id}_{game_id}\n\n"

        text += f"💡 <i>Tip: Check players' profiles before approving to ensure they're a good fit for your game!</i>"

        await update.message.reply_text(text, parse_mode='HTML')

    async def approve_waitlist_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        creator_id = str(update.effective_user.id)
        
        # Extract user_id and game_id from the command
        match = re.search(r'approve_(\w+)_(\w+)', update.message.text)
        if not match:
            await update.message.reply_text("❌ Invalid command format.")
            return
        
        user_id, game_id = match.groups()

        # Verify game exists and user is the creator
        game = self.game_service.get_game(game_id)
        if not game:
            await update.message.reply_text("❌ Game not found.")
            return

        if game.creator_id != creator_id:
            await update.message.reply_text("❌ You can only approve players for games you created.")
            return

        # Check if game is already full
        if game.current_players >= game.max_players:
            await update.message.reply_text("❌ This game is already full!")
            return

        # Approve the player
        success = self.game_service.approve_waitlist_entry(game_id, user_id)
        
        if success:
            # Get user info for notification
            user = self.user_service.get_user(user_id)
            game_time = self.format_start_end_time(game.start_time, game.end_time)
            
            await update.message.reply_text(
                f"✅ <b>Player Approved!</b>\n\n"
                f"<a href='tg://user?id={user_id}'>{html.escape(user.display_name)}</a> has been added to your game.\n\n"
                f"🎾 {html.escape(game.game_name)}\n"
                f"👥 Players: {game.current_players + 1}/{game.max_players}",
                parse_mode='HTML'
            )
            
            # Notify the approved player
            if user:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 <b>You've been approved!</b>\n\n"
                        f"You've been added to the game:\n"
                        f"🎾 <b>{html.escape(game.game_name)}</b>\n"
                        f"📅 {game_time}\n"
                        f"📍 {html.escape(game.location)}\n"
                        f"💰 Court Cost: ${game.court_cost}\n\n"
                        f"Host: <a href='tg://user?id={game.creator_id}'>Game Creator</a>\n\n"
                        f"See you on the court! 🎾",
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text("❌ Could not approve player. They may have already been processed or an error occurred.")

    async def reject_waitlist_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        creator_id = str(update.effective_user.id)
        
        # Extract user_id and game_id from the command
        match = re.search(r'reject_(\w+)_(\w+)', update.message.text)
        if not match:
            await update.message.reply_text("❌ Invalid command format.")
            return
        
        user_id, game_id = match.groups()

        # Verify game exists and user is the creator
        game = self.game_service.get_game(game_id)
        if not game:
            await update.message.reply_text("❌ Game not found.")
            return

        if game.creator_id != creator_id:
            await update.message.reply_text("❌ You can only reject players for games you created.")
            return

        # Reject the player
        success = self.game_service.reject_waitlist_entry(game_id, user_id)
        
        if success:
            # Get user info
            user = self.user_service.get_user(user_id)
            
            await update.message.reply_text(
                f"❌ <b>Player Rejected</b>\n\n"
                f"<a href='tg://user?id={user_id}'>{html.escape(user.display_name) if user else 'Player'}</a> has been removed from the waitlist.",
                parse_mode='HTML'
            )
            
            # Optionally notify the rejected player (you might want to make this configurable)
            if user:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"😔 <b>Waitlist Update</b>\n\n"
                        f"Unfortunately, you weren't selected for:\n"
                        f"🎾 <b>{html.escape(game.game_name)}</b>\n\n"
                        f"Don't worry! Use /find to discover other games that might be a great fit. 🎾",
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text("❌ Could not reject player. Please try again.")