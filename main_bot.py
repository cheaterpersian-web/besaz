import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode
from datetime import datetime, timedelta
import os
from config import Config
from database import db
from bot_manager import bot_manager
from payment_handler import payment_handler
from monitor import monitor
from error_handler import handle_telegram_errors
from logger import logger

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_BOT_TOKEN, WAITING_FOR_PAYMENT_PROOF = range(2)

class MainBot:
    def __init__(self):
        self.application = None
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all command and callback handlers"""
        self.application = Application.builder().token(Config.MAIN_BOT_TOKEN).build()
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CommandHandler("mybots", self.my_bots_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("payments", self.payments_command))
        
        # Admin command handlers
        self.application.add_handler(CommandHandler("setup", self.setup_command))
        self.application.add_handler(CommandHandler("users", self.users_command))
        self.application.add_handler(CommandHandler("broadcast", self.broadcast_command))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Conversation handlers
        bot_creation_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_bot_creation, pattern="^create_bot$")],
            states={
                WAITING_FOR_BOT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_bot_token)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
            per_message=False,
        )
        self.application.add_handler(bot_creation_conv)
        
        payment_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_payment, pattern="^payment_")],
            states={
                WAITING_FOR_PAYMENT_PROOF: [MessageHandler(filters.PHOTO | filters.TEXT, self.handle_payment_proof)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
            per_message=False,
        )
        self.application.add_handler(payment_conv)
    
    @handle_telegram_errors
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        # Add user to database
        await db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Check if user is admin
        is_admin = await db.is_admin(user.id)
        
        # Check if user is in the locked channel
        try:
            member = await context.bot.get_chat_member(Config.LOCKED_CHANNEL_ID, user.id)
            if member.status in ['left', 'kicked']:
                await update.message.reply_text(
                    "🔒 You must join our channel first to use this bot.\\n"
                    f"Please join: {Config.LOCKED_CHANNEL_ID}"
                )
                return
        except Exception as e:
            logger.error(f"Error checking channel membership: {e}")
        
        # Welcome message
        welcome_text = f"""
🤖 **Welcome to Bot Manager System!**

Hello {user.first_name}! I'm your bot management assistant.

**What I can do:**
• Create and manage your own Telegram bots
• Handle subscriptions and payments
• Monitor bot status and performance
• Provide admin controls (if you're an admin)

Use /help to see all available commands.
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 My Bots", callback_data="my_bots")],
            [InlineKeyboardButton("➕ Create New Bot", callback_data="create_bot")],
            [InlineKeyboardButton("💳 Subscribe", callback_data="subscribe")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 **Bot Manager System - Help**

**User Commands:**
/start - Start the bot and see main menu
/mybots - View your bots and their status
/subscribe - Subscribe to a plan
/payments - View payment history
/help - Show this help message

**Admin Commands:**
/setup - Initial bot setup (admin only)
/admin - Admin panel
/users - Manage users
/broadcast - Send message to all users

**How to create a bot:**
1. Get a bot token from @BotFather
2. Use "Create New Bot" button
3. Provide your bot token
4. Subscribe to a plan
5. Your bot will be deployed automatically!

**Subscription Plans:**
• 1 Month: ${:.2f}
• 2 Months: ${:.2f} (Save ${:.2f}!)
• 3 Months: ${:.2f} (Save ${:.2f}!)

**Payment Methods:**
• Bank Transfer (Card-to-Card)
• Cryptocurrency

Need help? Contact the admin!
        """.format(
            Config.PRICE_1_MONTH,
            Config.PRICE_2_MONTHS,
            Config.PRICE_1_MONTH * 2 - Config.PRICE_2_MONTHS,
            Config.PRICE_3_MONTHS,
            Config.PRICE_1_MONTH * 3 - Config.PRICE_3_MONTHS
        )
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    @handle_telegram_errors
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user_id = update.effective_user.id
        
        if not await db.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        await self.show_admin_panel(update, context)
    
    async def my_bots_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mybots command"""
        user_id = update.effective_user.id
        await self.show_user_bots(update, context, user_id)
    
    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /subscribe command"""
        await self.show_subscription_plans(update, context)
    
    async def payments_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /payments command"""
        user_id = update.effective_user.id
        await self.show_payment_history(update, context, user_id)
    
    async def setup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /setup command (admin only)"""
        user_id = update.effective_user.id
        
        if not await db.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        await self.show_setup_panel(update, context)
    
    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /users command (admin only)"""
        user_id = update.effective_user.id
        
        if not await db.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        await self.show_users_management(update, context)
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /broadcast command (admin only)"""
        user_id = update.effective_user.id
        
        if not await db.is_admin(user_id):
            await update.message.reply_text("❌ Access denied. Admin privileges required.")
            return
        
        # This would be implemented to send messages to all users
        await update.message.reply_text("📢 Broadcast functionality will be implemented here.")
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "my_bots":
            await self.show_user_bots(update, context, query.from_user.id)
        elif data == "create_bot":
            await self.start_bot_creation(update, context)
        elif data == "subscribe":
            await self.show_subscription_plans(update, context)
        elif data == "help":
            await self.help_command(update, context)
        elif data == "admin_panel":
            await self.show_admin_panel(update, context)
        elif data.startswith("bot_"):
            await self.handle_bot_callback(update, context, data)
        elif data.startswith("plan_"):
            await self.handle_plan_callback(update, context, data)
        elif data.startswith("payment_"):
            await self.handle_payment_callback(update, context, data)
        elif data.startswith("method_"):
            await self.handle_payment_method_callback(update, context, data)
        elif data.startswith("submit_proof_"):
            await self.handle_submit_proof_callback(update, context, data)
        elif data.startswith("admin_"):
            await self.handle_admin_callback(update, context, data)
    
    async def start_bot_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start bot creation conversation"""
        query = update.callback_query
        await query.edit_message_text(
            "🤖 **Create New Bot**\\n\\n"
            "To create a new bot, you need a bot token from @BotFather.\\n\\n"
            "**Steps:**\\n"
            "1. Go to @BotFather on Telegram\\n"
            "2. Send /newbot command\\n"
            "3. Follow the instructions\\n"
            "4. Copy the bot token\\n"
            "5. Send the token here\\n\\n"
            "**Send your bot token now:**",
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_FOR_BOT_TOKEN
    
    @handle_telegram_errors
    async def handle_bot_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot token input"""
        bot_token = update.message.text.strip()
        user_id = update.effective_user.id
        
        # Validate token format (basic validation)
        if not bot_token or len(bot_token) < 40:
            await update.message.reply_text(
                "❌ Invalid bot token format. Please check and try again.\\n"
                "Send /cancel to cancel this operation."
            )
            return WAITING_FOR_BOT_TOKEN
        
        try:
            # Test the token by getting bot info
            bot_info = await context.bot.get_me()
            
            # Add bot to database
            bot_id = await db.add_bot(
                owner_id=user_id,
                bot_token=bot_token,
                bot_username=bot_info.username,
                bot_name=bot_info.first_name
            )
            
            await update.message.reply_text(
                f"✅ Bot created successfully!\\n"
                f"Bot ID: {bot_id}\\n"
                f"Username: @{bot_info.username}\\n\\n"
                f"Now you need to subscribe to a plan to activate your bot.\\n"
                f"Use /subscribe to choose a plan."
            )
            
        except Exception as e:
            logger.error(f"Error creating bot: {e}")
            await update.message.reply_text(
                "❌ Error creating bot. Please check your token and try again.\\n"
                "Send /cancel to cancel this operation."
            )
            return WAITING_FOR_BOT_TOKEN
        
        return ConversationHandler.END
    
    async def show_subscription_plans(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show subscription plans"""
        plans_text = """
💳 **Subscription Plans**

Choose a plan to activate your bot:

**1 Month Plan**
💰 Price: ${:.2f}
⏰ Duration: {} days
🆔 Plan ID: plan_1_month

**2 Months Plan** (Best Value!)
💰 Price: ${:.2f} (Save ${:.2f}!)
⏰ Duration: {} days
🆔 Plan ID: plan_2_months

**3 Months Plan** (Maximum Savings!)
💰 Price: ${:.2f} (Save ${:.2f}!)
⏰ Duration: {} days
🆔 Plan ID: plan_3_months

**Payment Methods:**
• Bank Transfer (Card-to-Card)
• Cryptocurrency

Click on a plan to proceed with payment.
        """.format(
            Config.PRICE_1_MONTH, Config.PLAN_1_MONTH,
            Config.PRICE_2_MONTHS, Config.PRICE_1_MONTH * 2 - Config.PRICE_2_MONTHS, Config.PLAN_2_MONTHS,
            Config.PRICE_3_MONTHS, Config.PRICE_1_MONTH * 3 - Config.PRICE_3_MONTHS, Config.PLAN_3_MONTHS
        )
        
        keyboard = [
            [
                InlineKeyboardButton("1 Month - ${:.2f}".format(Config.PRICE_1_MONTH), callback_data="plan_1_month"),
                InlineKeyboardButton("2 Months - ${:.2f}".format(Config.PRICE_2_MONTHS), callback_data="plan_2_months")
            ],
            [InlineKeyboardButton("3 Months - ${:.2f}".format(Config.PRICE_3_MONTHS), callback_data="plan_3_months")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                plans_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                plans_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def show_user_bots(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Show user's bots"""
        bots = await db.get_user_bots(user_id)
        
        if not bots:
            text = "🤖 **Your Bots**\\n\\nYou don't have any bots yet.\\n\\nClick 'Create New Bot' to get started!"
            keyboard = [[InlineKeyboardButton("➕ Create New Bot", callback_data="create_bot")]]
        else:
            text = "🤖 **Your Bots**\\n\\n"
            keyboard = []
            
            for bot in bots:
                subscription = await db.get_bot_subscription(bot['id'])
                is_active = await db.is_subscription_active(bot['id'])
                is_running = await bot_manager.is_bot_running(bot['id'])
                
                status_emoji = "🟢" if is_running and is_active else "🔴"
                status_text = "Active" if is_running and is_active else "Inactive"
                
                if subscription:
                    end_date = datetime.fromisoformat(subscription['end_date'])
                    days_left = (end_date - datetime.now()).days
                    text += f"{status_emoji} **@{bot['bot_username']}**\\n"
                    text += f"Status: {status_text}\\n"
                    text += f"Plan: {subscription['plan_type']}\\n"
                    text += f"Days left: {days_left}\\n\\n"
                else:
                    text += f"🔴 **@{bot['bot_username']}**\\n"
                    text += f"Status: No subscription\\n\\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"Manage @{bot['bot_username']}", 
                    callback_data=f"bot_{bot['id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("➕ Create New Bot", callback_data="create_bot")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin panel"""
        # Get statistics
        all_bots = await db.get_all_bots()
        pending_payments = await db.get_pending_payments()
        
        active_bots = sum(1 for bot in all_bots if await db.is_subscription_active(bot['id']))
        
        text = f"""
⚙️ **Admin Panel**

📊 **Statistics:**
• Total Bots: {len(all_bots)}
• Active Bots: {active_bots}
• Pending Payments: {len(pending_payments)}

**Admin Actions:**
        """
        
        keyboard = [
            [InlineKeyboardButton("👥 Manage Users", callback_data="admin_users")],
            [InlineKeyboardButton("💳 Pending Payments", callback_data="admin_payments")],
            [InlineKeyboardButton("🤖 All Bots", callback_data="admin_bots")],
            [InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")],
            [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def handle_plan_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle plan selection callback"""
        plan_type = data.replace("plan_", "")
        await payment_handler.handle_plan_selection(update, context, plan_type)
    
    async def handle_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle payment selection callback"""
        parts = data.split("_")
        if len(parts) >= 3:
            plan_type = f"plan_{parts[1]}_{parts[2]}"
            bot_id = int(parts[3])
            await payment_handler.handle_payment_selection(update, context, plan_type, bot_id)
    
    async def handle_payment_method_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle payment method selection callback"""
        parts = data.split("_")
        if len(parts) >= 4:
            payment_method = parts[1]
            plan_type = f"plan_{parts[2]}_{parts[3]}"
            bot_id = int(parts[4])
            await payment_handler.show_payment_instructions(update, context, payment_method, plan_type, bot_id)
    
    async def start_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start payment conversation"""
        query = update.callback_query
        data = query.data
        
        # Extract payment info from callback data
        parts = data.split("_")
        if len(parts) >= 3:
            plan_type = f"plan_{parts[1]}_{parts[2]}"
            bot_id = int(parts[3])
            await payment_handler.handle_plan_selection(update, context, plan_type)
        else:
            await query.edit_message_text("❌ Invalid payment data.")
    
    async def handle_payment_proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment proof submission"""
        return await payment_handler.handle_payment_proof(update, context)
    
    async def handle_submit_proof_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle payment proof submission callback"""
        parts = data.split("_")
        if len(parts) >= 5:
            payment_method = parts[2]
            plan_type = f"plan_{parts[3]}_{parts[4]}"
            bot_id = int(parts[5])
            await payment_handler.start_payment_proof_submission(update, context, payment_method, plan_type, bot_id)
    
    async def handle_bot_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle bot management callback"""
        bot_id = int(data.replace("bot_", ""))
        user_id = update.callback_query.from_user.id
        
        # Get bot info
        bot = await db.get_bot(bot_id)
        if not bot or bot['owner_id'] != user_id:
            await update.callback_query.edit_message_text("❌ Bot not found or access denied.")
            return
        
        # Get bot status
        status = await bot_manager.get_bot_status(bot_id)
        subscription = await db.get_bot_subscription(bot_id)
        
        text = f"""
🤖 **Bot Management: @{bot['bot_username']}**

**Status:** {status['status'].title()}
**Running:** {'✅ Yes' if status['is_running'] else '❌ No'}
**Subscription:** {'✅ Active' if status['subscription_active'] else '❌ Inactive'}

**Bot Details:**
• Created: {status['created_at']}
• Last Activity: {status['last_activity'] or 'Never'}
        """
        
        if subscription:
            end_date = datetime.fromisoformat(subscription['end_date'])
            days_left = (end_date - datetime.now()).days
            text += f"• Plan: {subscription['plan_type']}\\n"
            text += f"• Expires: {end_date.strftime('%Y-%m-%d')}\\n"
            text += f"• Days Left: {days_left}\\n"
        
        keyboard = []
        
        if status['subscription_active']:
            if status['is_running']:
                keyboard.append([InlineKeyboardButton("⏹️ Stop Bot", callback_data=f"stop_bot_{bot_id}")])
            else:
                keyboard.append([InlineKeyboardButton("▶️ Start Bot", callback_data=f"start_bot_{bot_id}")])
            keyboard.append([InlineKeyboardButton("🔄 Restart Bot", callback_data=f"restart_bot_{bot_id}")])
        else:
            keyboard.append([InlineKeyboardButton("💳 Subscribe", callback_data="subscribe")])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to My Bots", callback_data="my_bots")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def handle_admin_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle admin panel callbacks"""
        user_id = update.callback_query.from_user.id
        
        if not await db.is_admin(user_id):
            await update.callback_query.edit_message_text("❌ Access denied. Admin privileges required.")
            return
        
        if data == "admin_users":
            await self.show_users_management(update, context)
        elif data == "admin_payments":
            await self.show_pending_payments(update, context)
        elif data == "admin_bots":
            await self.show_all_bots(update, context)
        elif data == "admin_settings":
            await self.show_admin_settings(update, context)
        elif data == "admin_broadcast":
            await self.show_broadcast_panel(update, context)
    
    async def show_pending_payments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show pending payments for admin"""
        payments = await db.get_pending_payments()
        
        if not payments:
            text = "💳 **Pending Payments**\\n\\nNo pending payments found."
            keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        else:
            text = "💳 **Pending Payments**\\n\\n"
            keyboard = []
            
            for payment in payments:
                text += f"**Payment #{payment['id']}**\\n"
                text += f"User: @{payment['username'] or payment['first_name']}\\n"
                text += f"Amount: ${payment['amount']:.2f}\\n"
                text += f"Plan: {payment['plan_type']}\\n"
                text += f"Method: {payment['payment_method']}\\n"
                text += f"Date: {payment['created_at']}\\n\\n"
                
                keyboard.append([
                    InlineKeyboardButton(f"✅ Approve #{payment['id']}", callback_data=f"approve_payment_{payment['id']}"),
                    InlineKeyboardButton(f"❌ Reject #{payment['id']}", callback_data=f"reject_payment_{payment['id']}")
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_all_bots(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all bots for admin"""
        bots = await db.get_all_bots()
        
        if not bots:
            text = "🤖 **All Bots**\\n\\nNo bots found."
        else:
            text = "🤖 **All Bots**\\n\\n"
            
            for bot in bots:
                subscription = await db.get_bot_subscription(bot['id'])
                is_active = await db.is_subscription_active(bot['id'])
                is_running = await bot_manager.is_bot_running(bot['id'])
                
                status_emoji = "🟢" if is_running and is_active else "🔴"
                text += f"{status_emoji} **@{bot['bot_username']}**\\n"
                text += f"Owner: {bot['owner_id']}\\n"
                text += f"Status: {bot['status']}\\n"
                text += f"Running: {'Yes' if is_running else 'No'}\\n"
                text += f"Subscription: {'Active' if is_active else 'Inactive'}\\n\\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_users_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show users management for admin"""
        # This would require implementing get_all_users in database.py
        text = "👥 **Users Management**\\n\\nUser management functionality will be implemented here."
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_admin_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin settings"""
        text = f"""
⚙️ **Admin Settings**

**Current Configuration:**
• 1 Month Plan: ${Config.PRICE_1_MONTH:.2f} ({Config.PLAN_1_MONTH} days)
• 2 Months Plan: ${Config.PRICE_2_MONTHS:.2f} ({Config.PLAN_2_MONTHS} days)
• 3 Months Plan: ${Config.PRICE_3_MONTHS:.2f} ({Config.PLAN_3_MONTHS} days)

**Payment Methods:**
• Bank Card: {Config.BANK_CARD_NUMBER}
• Crypto Wallet: {Config.CRYPTO_WALLET_ADDRESS}

**System Info:**
• Bot Repository: {Config.BOT_REPO_URL}
• Deployment Dir: {Config.BOT_DEPLOYMENT_DIR}
        """
        
        keyboard = [
            [InlineKeyboardButton("💰 Update Prices", callback_data="update_prices")],
            [InlineKeyboardButton("💳 Update Payment Info", callback_data="update_payment_info")],
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_broadcast_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show broadcast panel for admin"""
        text = "📢 **Broadcast Panel**\\n\\nBroadcast functionality will be implemented here."
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_setup_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show setup panel for admin"""
        text = f"""
⚙️ **Bot Setup Panel**

**Current Configuration:**
• Main Bot Token: {'✅ Set' if Config.MAIN_BOT_TOKEN else '❌ Not Set'}
• Admin User ID: {'✅ Set' if Config.ADMIN_USER_ID else '❌ Not Set'}
• Main Bot ID: {'✅ Set' if Config.MAIN_BOT_ID else '❌ Not Set'}
• Locked Channel: {'✅ Set' if Config.LOCKED_CHANNEL_ID else '❌ Not Set'}

**Database:**
• Status: {'✅ Connected' if await db.init_db() else '❌ Error'}

**Bot Repository:**
• URL: {Config.BOT_REPO_URL}
• Deployment Dir: {Config.BOT_DEPLOYMENT_DIR}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 Restart All Bots", callback_data="restart_all_bots")],
            [InlineKeyboardButton("🧹 Cleanup Expired Bots", callback_data="cleanup_expired")],
            [InlineKeyboardButton("📊 System Stats", callback_data="system_stats")],
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel current conversation"""
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END
    
    async def run(self):
        """Run the main bot"""
        # Initialize database
        await db.init_db()
        
        # Setup deployment directory
        await bot_manager.setup_deployment_directory()
        
        # Start monitoring in background
        monitor_task = asyncio.create_task(monitor.start_monitoring())
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Main bot started successfully!")
        
        try:
            # Keep the bot running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            await monitor.stop_monitoring()
            await self.application.stop()

# Create and run the main bot
if __name__ == '__main__':
    main_bot = MainBot()
    asyncio.run(main_bot.run())