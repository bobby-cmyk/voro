from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.game_service import GameService
from services.user_service import UserService

class WaitlistHandler:
    def __init__(self):
        self.game_service = GameService()
        self.user_service = UserService()
    
    async def handle_join_waitlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle waitlist join button press"""
        query = update.callback_query
        await query.answer()
        
        game_id = int(query.data.split('_')[1])
        user_id = query.from_user.id
        
        # Check if user has set skill level
        user = self.user_service.get_user(user_id)
        if not user or not user.skill_level:
            await query.edit_message_text(
                "❌ Please set your skill level first!\n\n"
                "Use /skill command to set your tennis level before joining games."
            )
            return
        
        success = self.game_service.join_waitlist(game_id, user_id)
        
        if success:
            await query.edit_message_text(
                "✅ **Added to waitlist!**\n\n"
                "The game creator will review your request and approve/reject based on skill level match. "
                "I'll notify you once they make a decision! 🎾"
            )
            
            # Notify game creator
            game = self.game_service.get_game(game_id)
            if game:
                await self.notify_creator_of_waitlist_request(context, game, query.from_user)
        else:
            await query.edit_message_text(
                "❌ **Could not join waitlist**\n\n"
                "You might already be on the waitlist for this game, or the game might be full."
            )
    
    async def notify_creator_of_waitlist_request(self, context: ContextTypes.DEFAULT_TYPE, game, requesting_user):
        """Notify game creator of new waitlist request"""
        user = self.user_service.get_user(requesting_user.id)
        game_time = game.datetime.strftime("%d/%m %I:%M %p")
        
        text = f"🎾 **New Waitlist Request!**\n\n"
        text += f"**Game:** {game.location}\n"
        text += f"**Time:** {game_time}\n"
        text += f"**Current Players:** {game.current_players}/{game.max_players}\n\n"
        text += f"**Player Request:**\n"
        text += f"👤 {requesting_user.first_name}"
        if requesting_user.username:
            text += f" (@{requesting_user.username})"
        text += f"\n📊 Skill Level: {user.skill_level if user and user.skill_level else 'Not set'}\n"
        text += f"🏆 Games Completed: {user.games_completed if user else 0}\n\n"
        text += "Please review and approve/reject:"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{game.id}_{requesting_user.id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{game.id}_{requesting_user.id}")
            ],
            [InlineKeyboardButton("👥 View All Waitlist", callback_data=f"waitlist_{game.id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        try:
            await context.bot.send_message(
                chat_id=game.creator_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error notifying creator: {e}")
    
    async def handle_approve_reject(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle approve/reject button presses"""
        query = update.callback_query
        await query.answer()
        
        action, game_id, user_id = query.data.split('_')
        game_id, user_id = int(game_id), int(user_id)
        
        game = self.game_service.get_game(game_id)
        approved_user = self.user_service.get_user(user_id)
        
        if action == "approve":
            success = self.game_service.approve_player(game_id, user_id)
            
            if success:
                await query.edit_message_text(
                    f"✅ **Player Approved!**\n\n"
                    f"👤 {approved_user.first_name} has been added to your game.\n"
                    f"📍 {game.location}\n\n"
                    f"Current players: {game.current_players + 1}/{game.max_players}\n\n"
                    f"I'll notify them and create a group chat if this is the final player!"
                )
                
                # Notify approved player
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 **You've been approved!**\n\n"
                         f"You're now confirmed for:\n"
                         f"📍 {game.location}\n"
                         f"📅 {game.datetime.strftime('%d/%m %I:%M %p')}\n\n"
                         f"Check /mygames to see all your upcoming games!"
                )
                
                # Check if game is now full and create group if needed
                updated_game = self.game_service.get_game(game_id)
                if updated_game.current_players >= updated_game.max_players:
                    await self.create_game_group(context, updated_game)
            else:
                await query.edit_message_text("❌ Failed to approve player. They might already be in the game.")
        
        elif action == "reject":
            self.game_service.reject_player(game_id, user_id)
            
            await query.edit_message_text(
                f"❌ **Player Rejected**\n\n"
                f"👤 {approved_user.first_name} has been removed from the waitlist.\n"
                f"📍 {game.location}"
            )
            
            # Notify rejected player
            await context.bot.send_message(
                chat_id=user_id,
                text=f"😔 **Waitlist Request Not Approved**\n\n"
                     f"Unfortunately, you weren't selected for:\n"
                     f"📍 {game.location}\n"
                     f"📅 {game.datetime.strftime('%d/%m %I:%M %p')}\n\n"
                     f"Don't worry! Use /find to see other available games. 🎾"
            )
    
    async def show_waitlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show full waitlist for a game"""
        query = update.callback_query
        await query.answer()
        
        game_id = int(query.data.split('_')[1])
        waitlist = self.game_service.get_game_waitlist(game_id)
        game = self.game_service.get_game(game_id)
        
        if not waitlist:
            await query.edit_message_text(
                f"📋 **Waitlist for {game.location}**\n\n"
                f"No players currently on waitlist."
            )
            return
        
        text = f"📋 **Waitlist for {game.location}**\n"
        text += f"📅 {game.datetime.strftime('%d/%m %I:%M %p')}\n\n"
        
        keyboard = []
        for i, entry in enumerate(waitlist, 1):
            text += f"{i}. {entry.first_name}"
            if entry.username:
                text += f" (@{entry.username})"
            text += f" - Skill: {entry.skill_level or 'Not set'}\n"

            keyboard.append([
                InlineKeyboardButton(f"✅ Approve {entry.first_name}", callback_data=f"approve_{game_id}_{entry.user_id}"),
                InlineKeyboardButton(f"❌ Reject {entry.first_name}", callback_data=f"reject_{game_id}_{entry.user_id}")
            ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    async def create_game_group(self, context: ContextTypes.DEFAULT_TYPE, game):
        """Create a Telegram group for the game"""
        try:
            # Note: This requires the bot to have permission to create groups
            # In a real implementation, you might want to handle this differently
            group_name = f"🎾 {game.location} - {game.datetime.strftime('%d/%m %I:%M %p')}"
            
            # This is a placeholder - actual group creation requires more setup
            game_info = (
                f"🎾 **Game Details**\n\n"
                f"📍 **Location:** {game.location}\n"
                f"📅 **Date/Time:** {game.datetime.strftime('%d/%m/%Y at %I:%M %p')}\n"
                f"⭐ **Skill Level:** {game.skill_range}\n"
                f"👥 **Players:** {game.current_players}/{game.max_players}\n\n"
                f"**Pre-game Checklist:**\n"
                f"☐ Confirm attendance 24h before\n"
                f"☐ Bring racket and balls\n"
                f"☐ Check weather conditions\n"
                f"☐ Exchange contact info\n\n"
                f"Have a great game! 🏆"
            )
            
            # Send game details to creator
            await context.bot.send_message(
                chat_id=game.creator_id,
                text=f"🎉 **Your game is now full!**\n\n{game_info}",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            print(f"Error creating game group: {e}")
    
    async def handle_leave_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle player leaving a game"""
        query = update.callback_query
        await query.answer()
        
        game_id = int(query.data.split('_')[1])
        user_id = query.from_user.id
        
        game = self.game_service.get_game(game_id)
        success = self.game_service.leave_game(game_id, user_id)
        
        if success:
            await query.edit_message_text(
                f"✅ **Left the game successfully**\n\n"
                f"You've been removed from:\n"
                f"📍 {game.location}\n"
                f"📅 {game.datetime.strftime('%d/%m %I:%M %p')}\n\n"
                f"The game is now open for new players."
            )
            
            # Notify game creator
            await context.bot.send_message(
                chat_id=game.creator_id,
                text=f"📢 **Player Left Your Game**\n\n"
                     f"👤 {query.from_user.first_name} has left the game:\n"
                     f"📍 {game.location}\n"
                     f"📅 {game.datetime.strftime('%d/%m %I:%M %p')}\n\n"
                     f"Current players: {game.current_players - 1}/{game.max_players}\n"
                     f"Your game is now open for new players!"
            )
        else:
            await query.edit_message_text("❌ Could not leave the game. Please try again.")