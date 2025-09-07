import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from telegram.constants import ParseMode
from datetime import datetime, timedelta
from html import escape
import os
from config import Config
from database import db
from bot_manager import bot_manager
from payment_handler import payment_handler
from monitor import monitor
from error_handler import handle_telegram_errors
from logger import logger
import os

# Conversation states
WAITING_FOR_BOT_TOKEN, WAITING_FOR_PAYMENT_PROOF = range(2)

class MainBot:
    def __init__(self):
        self.application = None
    
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
        
        # Conversation handlers (must be added BEFORE catch-all callback handler)
        bot_creation_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_bot_creation, pattern="^create_bot$")],
            states={
                WAITING_FOR_BOT_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_bot_token)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
            per_message=True,
        )
        self.application.add_handler(bot_creation_conv)
        
        payment_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_payment, pattern="^payment_"),
                CallbackQueryHandler(self.handle_submit_proof_callback, pattern="^submit_proof_")
            ],
            states={
                WAITING_FOR_PAYMENT_PROOF: [MessageHandler(filters.PHOTO | filters.TEXT, self.handle_payment_proof)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
            per_message=True,
        )
        self.application.add_handler(payment_conv)

        # Callback query handlers (catch-all) – add AFTER conversations
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

        # Generic text handler to capture admin inline edits and token fallback (non-blocking)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_messages, block=False))
    
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
                    "🔒 برای استفاده از این ربات ابتدا باید در کانال ما عضو شوید.\\n"
                    f"لطفاً عضو شوید: {Config.LOCKED_CHANNEL_ID}"
                )
                return
        except Exception as e:
            logger.error(f"Error checking channel membership: {e}")
        
        # Welcome message
        welcome_text = f"""
🤖 **به سیستم مدیریت ربات خوش آمدید!**

سلام {user.first_name}! من دستیار مدیریت ربات شما هستم.

**قابلیت‌های من:**
• ایجاد و مدیریت ربات‌های تلگرام شما
• مدیریت اشتراک‌ها و پرداخت‌ها
• نظارت بر وضعیت و عملکرد ربات‌ها
• کنترل‌های ادمین (اگر ادمین هستید)

از /help برای دیدن تمام دستورات استفاده کنید.
        """
        
        keyboard = [
            [InlineKeyboardButton("📋 ربات‌های من", callback_data="my_bots")],
            [InlineKeyboardButton("➕ ایجاد ربات جدید", callback_data="create_bot")],
            [InlineKeyboardButton("💳 اشتراک", callback_data="subscribe")],
            [InlineKeyboardButton("❓ راهنما", callback_data="help")]
        ]
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("⚙️ پنل ادمین", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 **سیستم مدیریت ربات - راهنما**

**دستورات کاربر:**
/start - شروع ربات و نمایش منوی اصلی
/mybots - مشاهده ربات‌های شما و وضعیت آن‌ها
/subscribe - اشتراک در یک پلن
/payments - مشاهده تاریخچه پرداخت‌ها
/help - نمایش این پیام راهنما

**دستورات ادمین:**
/setup - راه‌اندازی اولیه ربات (فقط ادمین)
/admin - پنل ادمین
/users - مدیریت کاربران
/broadcast - ارسال پیام به همه کاربران

**نحوه ایجاد ربات:**
1. توکن ربات را از @BotFather دریافت کنید
2. از دکمه "ایجاد ربات جدید" استفاده کنید
3. توکن ربات خود را ارائه دهید
4. در یک پلن اشتراک شوید
5. ربات شما به طور خودکار راه‌اندازی می‌شود!

**پلن‌های اشتراک:**
• 1 ماه: ${:.2f}
• 2 ماه: ${:.2f} (صرفه‌جویی ${:.2f}!)
• 3 ماه: ${:.2f} (صرفه‌جویی ${:.2f}!)

**روش‌های پرداخت:**
• انتقال بانکی (کارت به کارت)
• ارز دیجیتال

نیاز به کمک دارید؟ با ادمین تماس بگیرید!
        """.format(
            Config.PRICE_1_MONTH,
            Config.PRICE_2_MONTHS,
            Config.PRICE_1_MONTH * 2 - Config.PRICE_2_MONTHS,
            Config.PRICE_3_MONTHS,
            Config.PRICE_1_MONTH * 3 - Config.PRICE_3_MONTHS
        )
        
        # Check if it's a callback query or message
        if update.callback_query:
            await update.callback_query.edit_message_text(help_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    @handle_telegram_errors
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user_id = update.effective_user.id
        
        if not await db.is_admin(user_id):
            await update.message.reply_text("❌ دسترسی رد شد. دسترسی ادمین مورد نیاز است.")
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
        await payment_handler.show_payment_history(update, context, user_id)
    
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
        elif data == "main_menu":
            await self.start_command(update, context)
        elif data == "admin_panel":
            await self.show_admin_panel(update, context)
        elif data == "update_prices" or data == "update_payment_info":
            # Forward admin-settings actions
            await self.handle_admin_callback(update, context, data)
        elif data.startswith("bot_"):
            await self.handle_bot_callback(update, context, data)
        elif data.startswith("plan_"):
            await self.handle_plan_callback(update, context, data)
        elif data.startswith("payment_"):
            await self.handle_payment_callback(update, context, data)
        elif data.startswith("method_"):
            await self.handle_payment_method_callback(update, context, data)
        elif data.startswith("submit_proof_"):
            await self.handle_submit_proof_callback(update, context)
        elif data.startswith("admin_"):
            await self.handle_admin_callback(update, context, data)
    
    async def start_bot_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start bot creation conversation"""
        query = update.callback_query
        # Also mark a flag to catch token via generic text handler if conversation misses it
        context.user_data['awaiting_bot_token'] = True
        await query.edit_message_text(
            """
🤖 **ساخت ربات جدید**

برای ساخت ربات لازمه از @BotFather یه توکن بگیری.

**مراحل کار:**
1) برو سراغ @BotFather
2) دستور /newbot رو بزن
3) اسم و یوزرنیم بده
4) توکن رو کپی کن
5) همینجا برام بفرست

الان توکن رباتتو بفرست:
            """,
            parse_mode=ParseMode.MARKDOWN
        )
        return WAITING_FOR_BOT_TOKEN
    
    @handle_telegram_errors
    async def handle_bot_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot token input"""
        bot_token = update.message.text.strip()
        user_id = update.effective_user.id
        
        # Validate token format (basic validation)
        import re
        token_pattern = r'^\d{6,}:[A-Za-z0-9_-]{30,}$'
        if not bot_token or not re.match(token_pattern, bot_token):
            await update.message.reply_text(
                "❌ فرمت توکن درست نیست. دوباره چک کن و بفرست.\n"
                "برای لغو /cancel رو بزن."
            )
            return WAITING_FOR_BOT_TOKEN
        
        try:
            # Test the token by getting bot info
            from telegram import Bot as PTBBot
            test_bot = PTBBot(token=bot_token)
            bot_info = await test_bot.get_me()
            
            # Add bot to database
            bot_id = await db.add_bot(
                owner_id=user_id,
                bot_token=bot_token,
                bot_username=bot_info.username,
                bot_name=bot_info.first_name
            )
            
            await update.message.reply_text(
                f"✅ ربات با موفقیت ساخته شد!\n"
                f"شناسه ربات: {bot_id}\n"
                f"یوزرنیم: @{bot_info.username}\n\n"
                f"برای فعال‌سازی، یکی از پلن‌ها رو انتخاب کن.\n"
                f"/subscribe"
            )
            
        except Exception as e:
            logger.error(f"Error creating bot: {e}")
            await update.message.reply_text(
                "❌ ساخت ربات ناموفق بود. توکن رو چک کن و دوباره بفرست.\n"
                "برای لغو /cancel رو بزن."
            )
            return WAITING_FOR_BOT_TOKEN
        
        return ConversationHandler.END
    
    async def show_subscription_plans(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show subscription plans (Persian casual)"""
        plans_text = """
💳 **پلن‌های اشتراک**

یکی از پلن‌ها رو انتخاب کن تا رباتت فعال بشه:

**پلن ۱ ماهه**
💰 قیمت: ${:.2f}
⏰ مدت: {} روز
🆔 شناسه پلن: plan_1_month

**پلن ۲ ماهه** (به‌صرفه‌تر!)
💰 قیمت: ${:.2f} (صرفه‌جویی ${:.2f})
⏰ مدت: {} روز
🆔 شناسه پلن: plan_2_months

**پلن ۳ ماهه** (بهترین صرفه اقتصادی!)
💰 قیمت: ${:.2f} (صرفه‌جویی ${:.2f})
⏰ مدت: {} روز
🆔 شناسه پلن: plan_3_months

**روش‌های پرداخت:**
• کارت‌به‌کارت
• ارز دیجیتال

روی پلن دلخواهت بزن تا ادامه بدیم.
        """.format(
            Config.PRICE_1_MONTH, Config.PLAN_1_MONTH,
            Config.PRICE_2_MONTHS, Config.PRICE_1_MONTH * 2 - Config.PRICE_2_MONTHS, Config.PLAN_2_MONTHS,
            Config.PRICE_3_MONTHS, Config.PRICE_1_MONTH * 3 - Config.PRICE_3_MONTHS, Config.PLAN_3_MONTHS
        )
        
        keyboard = [
            [
                InlineKeyboardButton("۱ ماهه - ${:.2f}".format(Config.PRICE_1_MONTH), callback_data="plan_1_month"),
                InlineKeyboardButton("۲ ماهه - ${:.2f}".format(Config.PRICE_2_MONTHS), callback_data="plan_2_months")
            ],
            [InlineKeyboardButton("۳ ماهه - ${:.2f}".format(Config.PRICE_3_MONTHS), callback_data="plan_3_months")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
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
            text = "🤖 **ربات‌های شما**\\n\\nهنوز هیچ رباتی ندارید.\\n\\nبرای شروع روی 'ایجاد ربات جدید' کلیک کنید!"
            keyboard = [[InlineKeyboardButton("➕ ایجاد ربات جدید", callback_data="create_bot")]]
        else:
            text = "🤖 **ربات‌های شما**\\n\\n"
            keyboard = []
            
            for bot in bots:
                subscription = await db.get_bot_subscription(bot['id'])
                is_active = await db.is_subscription_active(bot['id'])
                is_running = await bot_manager.is_bot_running(bot['id'])
                
                status_emoji = "🟢" if is_running and is_active else "🔴"
                status_text = "فعال" if is_running and is_active else "غیرفعال"
                
                if subscription:
                    end_date = datetime.fromisoformat(subscription['end_date'])
                    days_left = (end_date - datetime.now()).days
                    text += f"{status_emoji} **@{bot['bot_username']}**\\n"
                    text += f"وضعیت: {status_text}\\n"
                    text += f"پلن: {subscription['plan_type']}\\n"
                    text += f"روزهای باقی‌مانده: {days_left}\\n\\n"
                else:
                    text += f"🔴 **@{bot['bot_username']}**\\n"
                    text += f"وضعیت: بدون اشتراک\\n\\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"مدیریت @{bot['bot_username']}", 
                    callback_data=f"bot_{bot['id']}"
                )])
            
            keyboard.append([InlineKeyboardButton("➕ ایجاد ربات جدید", callback_data="create_bot")])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
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
        
        active_bots = 0
        for bot in all_bots:
            if await db.is_subscription_active(bot['id']):
                active_bots += 1
        
        text = f"""
⚙️ **پنل ادمین**

📊 **آمار:**
• کل ربات‌ها: {len(all_bots)}
• ربات‌های فعال: {active_bots}
• پرداخت‌های در انتظار: {len(pending_payments)}

**عملیات ادمین:**
        """
        
        keyboard = [
            [InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")],
            [InlineKeyboardButton("💳 پرداخت‌های در انتظار", callback_data="admin_payments")],
            [InlineKeyboardButton("🤖 همه ربات‌ها", callback_data="admin_bots")],
            [InlineKeyboardButton("⚙️ تنظیمات", callback_data="admin_settings")],
            [InlineKeyboardButton("📢 ارسال پیام", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
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
        plan_type = data
        await payment_handler.handle_plan_selection(update, context, plan_type)
    
    async def handle_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle payment selection callback: payment_<plan_type>_<bot_id>"""
        parts = data.split("_")
        if len(parts) >= 3:
            bot_id = int(parts[-1])
            plan_type = "_".join(parts[1:-1])
            await payment_handler.handle_payment_selection(update, context, plan_type, bot_id)
    
    async def handle_payment_method_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Handle payment method selection callback: method_<method>_<plan_type>_<bot_id>"""
        parts = data.split("_")
        if len(parts) >= 5:
            payment_method = parts[1]
            bot_id = int(parts[-1])
            plan_type = "_".join(parts[2:-1])
            await payment_handler.show_payment_instructions(update, context, payment_method, plan_type, bot_id)
    
    async def start_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start payment conversation from callback: payment_<plan_type>_<bot_id>"""
        query = update.callback_query
        data = query.data
        
        # Extract payment info from callback data
        parts = data.split("_")
        if len(parts) >= 3:
            bot_id = int(parts[-1])
            plan_type = "_".join(parts[1:-1])
            await payment_handler.handle_payment_selection(update, context, plan_type, bot_id)
        else:
            await query.edit_message_text("❌ Invalid payment data.")
    
    async def handle_payment_proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment proof submission"""
        result = await payment_handler.handle_payment_proof(update, context)
        if result == "WAITING_FOR_PAYMENT_PROOF":
            return WAITING_FOR_PAYMENT_PROOF
        return result
    
    async def handle_submit_proof_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment proof submission callback: submit_proof_<method>_<plan_type>_<bot_id>"""
        data = update.callback_query.data
        parts = data.split("_")
        if len(parts) >= 6:
            payment_method = parts[2]
            bot_id = int(parts[-1])
            plan_type = "_".join(parts[3:-1])
            await payment_handler.start_payment_proof_submission(update, context, payment_method, plan_type, bot_id)
            return WAITING_FOR_PAYMENT_PROOF
    
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
🤖 **مدیریت ربات: @{bot['bot_username']}**

**وضعیت:** {status['status'].title()}
**در حال اجرا:** {'✅ بله' if status['is_running'] else '❌ خیر'}
**اشتراک:** {'✅ فعال' if status['subscription_active'] else '❌ غیرفعال'}

**جزئیات ربات:**
• ایجاد شده: {status['created_at']}
• آخرین فعالیت: {status['last_activity'] or 'هرگز'}
        """
        
        if subscription:
            end_date = datetime.fromisoformat(subscription['end_date'])
            days_left = (end_date - datetime.now()).days
            text += f"• پلن: {subscription['plan_type']}\\n"
            text += f"• انقضا: {end_date.strftime('%Y-%m-%d')}\\n"
            text += f"• روزهای باقی‌مانده: {days_left}\\n"
        
        keyboard = []
        
        if status['subscription_active']:
            if status['is_running']:
                keyboard.append([InlineKeyboardButton("⏹️ توقف ربات", callback_data=f"stop_bot_{bot_id}")])
            else:
                keyboard.append([InlineKeyboardButton("▶️ شروع ربات", callback_data=f"start_bot_{bot_id}")])
            keyboard.append([InlineKeyboardButton("🔄 راه‌اندازی مجدد ربات", callback_data=f"restart_bot_{bot_id}")])
        else:
            keyboard.append([InlineKeyboardButton("💳 اشتراک", callback_data="subscribe")])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به ربات‌های من", callback_data="my_bots")])
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
        elif data == "update_prices":
            await self.prompt_update_prices(update, context)
        elif data == "update_payment_info":
            await self.prompt_update_payment_info(update, context)
    
    async def show_pending_payments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show pending payments for admin"""
        payments = await db.get_pending_payments()
        
        if not payments:
            text = "💳 **پرداخت‌های در انتظار**\\n\\nهیچ پرداخت در انتظاری یافت نشد."
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]]
        else:
            text = "💳 **پرداخت‌های در انتظار**\\n\\n"
            keyboard = []
            
            for payment in payments:
                text += f"**پرداخت #{payment['id']}**\\n"
                text += f"کاربر: @{payment['username'] or payment['first_name']}\\n"
                text += f"مبلغ: ${payment['amount']:.2f}\\n"
                text += f"پلن: {payment['plan_type']}\\n"
                text += f"روش: {payment['payment_method']}\\n"
                text += f"تاریخ: {payment['created_at']}\\n\\n"
                
                keyboard.append([
                    InlineKeyboardButton(f"✅ تایید #{payment['id']}", callback_data=f"approve_payment_{payment['id']}"),
                    InlineKeyboardButton(f"❌ رد #{payment['id']}", callback_data=f"reject_payment_{payment['id']}")
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")])
        
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
            text = "🤖 **همه ربات‌ها**\\n\\nهیچ رباتی یافت نشد."
        else:
            text = "🤖 **همه ربات‌ها**\\n\\n"
            
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
        """Show admin settings (Persian) with live values from DB settings, fallback to Config."""
        # Read runtime values from settings table if available
        price_1 = await db.get_setting('PRICE_1_MONTH')
        price_2 = await db.get_setting('PRICE_2_MONTHS')
        price_3 = await db.get_setting('PRICE_3_MONTHS')
        bank_val = await db.get_setting('BANK_CARD_NUMBER')
        crypto_val = await db.get_setting('CRYPTO_WALLET_ADDRESS')

        p1 = float(price_1) if price_1 else float(Config.PRICE_1_MONTH or 0)
        p2 = float(price_2) if price_2 else float(Config.PRICE_2_MONTHS or 0)
        p3 = float(price_3) if price_3 else float(Config.PRICE_3_MONTHS or 0)
        bank = escape(str(bank_val or Config.BANK_CARD_NUMBER or "-"))
        crypto = escape(str(crypto_val or Config.CRYPTO_WALLET_ADDRESS or "-"))
        repo = escape(str(Config.BOT_REPO_URL or "-"))
        deploy = escape(str(Config.BOT_DEPLOYMENT_DIR or "-"))

        text = (
            f"<b>⚙️ تنظیمات ادمین</b>\n\n"
            f"<b>پیکربندی فعلی:</b>\n"
            f"• پلن ۱ ماهه: ${p1:.2f} ({Config.PLAN_1_MONTH} روز)\n"
            f"• پلن ۲ ماهه: ${p2:.2f} ({Config.PLAN_2_MONTHS} روز)\n"
            f"• پلن ۳ ماهه: ${p3:.2f} ({Config.PLAN_3_MONTHS} روز)\n\n"
            f"<b>روش‌های پرداخت:</b>\n"
            f"• کارت: <code>{bank}</code>\n"
            f"• ولت ارز دیجیتال: <code>{crypto}</code>\n\n"
            f"<b>اطلاعات سیستم:</b>\n"
            f"• سورس ربات: <code>{repo}</code>\n"
            f"• مسیر استقرار: <code>{deploy}</code>"
        )
        
        keyboard = [
            [InlineKeyboardButton("💰 بروزرسانی قیمت‌ها", callback_data="update_prices")],
            [InlineKeyboardButton("💳 بروزرسانی اطلاعات پرداخت", callback_data="update_payment_info")],
            [InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
    
    async def show_broadcast_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show broadcast panel for admin"""
        text = "📢 **ارسال همگانی**\\n\\nاین بخش به‌زودی تکمیل می‌شه."
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_setup_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show setup panel for admin"""
        text = f"""
⚙️ **تنظیمات اولیه**

**پیکربندی فعلی:**
• توکن ربات اصلی: {'✅ ثبت شده' if Config.MAIN_BOT_TOKEN else '❌ ثبت نشده'}
• آیدی عددی ادمین: {'✅ ثبت شده' if Config.ADMIN_USER_ID else '❌ ثبت نشده'}
• آیدی ربات اصلی: {'✅ ثبت شده' if Config.MAIN_BOT_ID else '❌ ثبت نشده'}
• کانال قفل‌شده: {'✅ ثبت شده' if Config.LOCKED_CHANNEL_ID else '❌ ثبت نشده'}

**دیتابیس:**
• وضعیت: ✅ آماده

**سورس ربات‌ها:**
• آدرس: {Config.BOT_REPO_URL}
• مسیر استقرار: {Config.BOT_DEPLOYMENT_DIR}
        """
        
        keyboard = [
            [InlineKeyboardButton("🔄 راه‌اندازی مجدد همه ربات‌ها", callback_data="restart_all_bots")],
            [InlineKeyboardButton("🧹 پاکسازی ربات‌های منقضی", callback_data="cleanup_expired")],
            [InlineKeyboardButton("📊 آمار سیستم", callback_data="system_stats")],
            [InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    async def prompt_update_prices(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Prompt admin to send new prices in one line"""
        context.user_data['awaiting_prices'] = True
        context.user_data['awaiting_payment'] = False
        await update.callback_query.edit_message_text(
            "💰 قیمت‌های جدید رو به این شکل بفرست:\n\n"
            "مثال: 1=10.00, 2=18.00, 3=25.00\n\n"
            "یعنی: ۱ ماهه=۱۰ دلار، ۲ ماهه=۱۸ دلار، ۳ ماهه=۲۵ دلار"
        )

    async def prompt_update_payment_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Prompt admin to send new payment info"""
        context.user_data['awaiting_payment'] = True
        context.user_data['awaiting_prices'] = False
        await update.callback_query.edit_message_text(
            "💳 اطلاعات پرداخت رو به این شکل بفرست:\n\n"
            "CARD=xxxx-xxxx-xxxx-xxxx, CRYPTO=your_wallet"
        )

    async def handle_text_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin inline inputs for settings updates"""
        user_id = update.effective_user.id
        text = (update.message.text or "").strip()

        # If user is in bot-token flow, accept Telegram token here as a fallback
        if context.user_data.get('awaiting_bot_token'):
            import re
            if re.match(r'^\d{6,}:[A-Za-z0-9_-]{30,}$', text):
                # Clear flag and delegate to token handler
                context.user_data['awaiting_bot_token'] = False
                await self.handle_bot_token(update, context)
                return

        if not await db.is_admin(user_id):
            return
        # Update prices
        if context.user_data.get('awaiting_prices'):
            try:
                parts = [p.strip() for p in text.split(',') if p.strip()]
                mapping = {}
                for p in parts:
                    if '=' not in p:
                        raise ValueError('bad part')
                    k, v = [x.strip() for x in p.split('=', 1)]
                    mapping[k] = float(v)
                if '1' in mapping:
                    Config.PRICE_1_MONTH = mapping['1']
                    await db.set_setting('PRICE_1_MONTH', str(mapping['1']))
                if '2' in mapping:
                    Config.PRICE_2_MONTHS = mapping['2']
                    await db.set_setting('PRICE_2_MONTHS', str(mapping['2']))
                if '3' in mapping:
                    Config.PRICE_3_MONTHS = mapping['3']
                    await db.set_setting('PRICE_3_MONTHS', str(mapping['3']))
                context.user_data['awaiting_prices'] = False
                await update.message.reply_text("✅ قیمت‌ها بروزرسانی شد.")
                # Refresh admin settings view
                await self.show_admin_settings(update, context)
            except Exception:
                await update.message.reply_text("❌ فرمت اشتباهه. مثال: 1=10.00, 2=18.00, 3=25.00")
            return
        # Update payment info
        if context.user_data.get('awaiting_payment'):
            try:
                parts = [p.strip() for p in text.split(',') if p.strip()]
                kv = {}
                for p in parts:
                    if '=' not in p:
                        raise ValueError('bad part')
                    k, v = [x.strip() for x in p.split('=', 1)]
                    # Normalize key to be more tolerant of typos/variants
                    import re
                    key_norm = re.sub(r'[^A-Z0-9]', '', k.upper())
                    if key_norm in { 'CARD', 'CAERD', 'BANKCARD', 'CARDNUMBER', 'CARDNO', 'CARDNUM' }:
                        kv_key = 'CARD'
                    elif key_norm in { 'CRYPTO', 'WALLET', 'WALLETADDRESS', 'WALLETADDR', 'CRYPTOWALLET' }:
                        kv_key = 'CRYPTO'
                    else:
                        kv_key = k.upper()
                    kv[kv_key] = v
                if 'CARD' in kv:
                    Config.BANK_CARD_NUMBER = kv['CARD']
                    await db.set_setting('BANK_CARD_NUMBER', kv['CARD'])
                if 'CRYPTO' in kv:
                    Config.CRYPTO_WALLET_ADDRESS = kv['CRYPTO']
                    await db.set_setting('CRYPTO_WALLET_ADDRESS', kv['CRYPTO'])
                context.user_data['awaiting_payment'] = False
                await update.message.reply_text("✅ اطلاعات پرداخت بروزرسانی شد.")
                # Refresh admin settings view
                await self.show_admin_settings(update, context)
            except Exception:
                await update.message.reply_text("❌ فرمت اشتباهه. مثال: CARD=xxxx, CRYPTO=wallet")
    
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
        if self.application is None:
            self.setup_handlers()
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