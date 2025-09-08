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
WAITING_FOR_BOT_TOKEN, WAITING_FOR_ADMIN_ID, WAITING_FOR_CHANNEL_ID, WAITING_FOR_PAYMENT_PROOF = range(4)

class MainBot:
    def __init__(self):
        self.application = None
    
    def setup_handlers(self):
        """Setup all command and callback handlers"""
        self.application = Application.builder().token(Config.MAIN_BOT_TOKEN).build()
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("admin", self.admin_command))
        self.application.add_handler(CommandHandler("mybots", self.my_bots_command))
        self.application.add_handler(CommandHandler("subscribe", self.subscribe_command))
        self.application.add_handler(CommandHandler("payments", self.payments_command))
        
        # Admin command handlers
        self.application.add_handler(CommandHandler("setup", self.setup_command))
        self.application.add_handler(CommandHandler("users", self.users_command))
        self.application.add_handler(CommandHandler("role", self.set_user_role_command))
        self.application.add_handler(CommandHandler("active", self.set_user_active_command))
        self.application.add_handler(CommandHandler("broadcast", self.broadcast_command))
        
        # Conversation handlers (must be added BEFORE catch-all callback handler)
        bot_creation_conv = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.start_bot_creation, pattern="^create_bot$")],
            states={
                WAITING_FOR_BOT_TOKEN: [
                    # First try to parse as token; if not a token and expecting admin/channel, route to text handler
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.route_bot_creation_inputs)
                ],
                WAITING_FOR_ADMIN_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_admin_id_input)
                ],
                WAITING_FOR_CHANNEL_ID: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_channel_id_input)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
        )
        self.application.add_handler(bot_creation_conv)
        
        payment_conv = ConversationHandler(
            entry_points=[
                CallbackQueryHandler(self.start_payment, pattern="^payment_"),
                CallbackQueryHandler(self.handle_submit_proof_callback, pattern="^submit_proof_")
            ],
            states={
                WAITING_FOR_PAYMENT_PROOF: [MessageHandler((filters.PHOTO | filters.Document.ALL | (filters.TEXT & ~filters.COMMAND)), self.handle_payment_proof)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
        )
        self.application.add_handler(payment_conv)

        # Callback query handlers (catch-all) – add AFTER conversations
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))

        # Broadcast capture: handle forward mode (non-blocking)
        self.application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.handle_broadcast_capture, block=False))

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
            if Config.LOCKED_CHANNEL_ID:
                member = await context.bot.get_chat_member(Config.LOCKED_CHANNEL_ID, user.id)
                if member.status in ['left', 'kicked']:
                    lock_text = (
                        "🔒 برای استفاده از این ربات ابتدا باید در کانال ما عضو شوید.\n"
                        f"لطفاً عضو شوید: {Config.LOCKED_CHANNEL_ID}"
                    )
                    if update.callback_query:
                        await update.callback_query.edit_message_text(lock_text)
                    else:
                        await update.message.reply_text(lock_text)
                    return
        except Exception as e:
            logger.error(f"Error checking channel membership: {e}")
        
        # Welcome message (concise, friendly)
        welcome_text = f"سلام {user.first_name} 👋\n\nاز دکمه‌های زیر استفاده کن.\n\nبرای اطلاعیه‌ها حتماً عضو کانال شو: @wingsbotcr"
        
        keyboard = [
            [InlineKeyboardButton("📋 ربات‌های من", callback_data="my_bots")],
            [InlineKeyboardButton("➕ ایجاد ربات جدید", callback_data="create_bot")],
            [InlineKeyboardButton("💳 اشتراک", callback_data="subscribe")],
            [InlineKeyboardButton("📣 کانال", url="https://t.me/wingsbotcr")]
        ]
        
        if is_admin:
            keyboard.append([InlineKeyboardButton("⚙️ پنل ادمین", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                welcome_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help disabled."""
        return
    
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
        elif data in ("broadcast_text", "broadcast_forward"):
            # Forward broadcast mode selections to admin handler
            await self.handle_admin_callback(update, context, data)
        elif data.startswith("bot_"):
            await self.handle_bot_callback(update, context, data)
        elif data.startswith("start_bot_"):
            bot_id = int(data.split("_")[-1])
            bot_info = await db.get_bot(bot_id)
            if bot_info:
                await bot_manager.deploy_bot(bot_id, bot_info['bot_token'])
            await self.handle_bot_callback(update, context, f"bot_{bot_id}")
        elif data.startswith("stop_bot_"):
            bot_id = int(data.split("_")[-1])
            await bot_manager.stop_bot(bot_id)
            await self.handle_bot_callback(update, context, f"bot_{bot_id}")
        elif data.startswith("restart_bot_"):
            bot_id = int(data.split("_")[-1])
            await bot_manager.restart_bot(bot_id)
            await self.handle_bot_callback(update, context, f"bot_{bot_id}")
        elif data.startswith("plan_"):
            await self.handle_plan_callback(update, context, data)
        elif data.startswith("payment_"):
            await self.handle_payment_callback(update, context, data)
        elif data.startswith("method_"):
            await self.handle_payment_method_callback(update, context, data)
        elif data.startswith("submit_proof_"):
            await self.handle_submit_proof_callback(update, context)
        elif data.startswith("approve_payment_") or data.startswith("reject_payment_"):
            # Forward payment moderation actions to admin handler
            await self.handle_admin_callback(update, context, data)
        elif data.startswith("admin_"):
            await self.handle_admin_callback(update, context, data)
        elif data.startswith("delete_bot_"):
            try:
                bot_id = int(data.split("_")[-1])
            except Exception:
                await update.callback_query.answer("خطای حذف ربات", show_alert=True)
                return
            await self.prompt_delete_bot(update, context, bot_id)
        elif data.startswith("confirm_delete_"):
            try:
                bot_id = int(data.split("_")[-1])
            except Exception:
                await update.callback_query.answer("خطای حذف ربات", show_alert=True)
                return
            await self.confirm_delete_bot(update, context, bot_id)
        elif data.startswith("cancel_delete_"):
            try:
                bot_id = int(data.split("_")[-1])
                await self.handle_bot_callback(update, context, f"bot_{bot_id}")
            except Exception:
                await self.show_user_bots(update, context, update.callback_query.from_user.id)
        elif data == "setup_panel":
            await self.show_setup_panel(update, context)
        elif data == "system_stats":
            await self.show_system_stats(update, context)
        elif data == "restart_all_bots":
            await self.handle_restart_all_bots(update, context)
        elif data == "cleanup_expired":
            await self.handle_cleanup_expired(update, context)
    
    async def start_bot_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start bot creation conversation"""
        query = update.callback_query
        # Also mark a flag to catch token via generic text handler if conversation misses it
        context.user_data['awaiting_bot_token'] = True
        context.user_data['awaiting_admin_id'] = False
        context.user_data['awaiting_channel_id'] = False
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
            
            # Temporarily create bot with no admin/channel, then ask user to provide
            bot_id = await db.add_bot(
                owner_id=user_id,
                bot_token=bot_token,
                bot_username=bot_info.username,
                bot_name=bot_info.first_name,
                admin_user_id=None,
                locked_channel_id=None
            )

            # Ask for admin id
            context.user_data['new_bot_id'] = bot_id
            context.user_data['awaiting_admin_id'] = True
            context.user_data['awaiting_bot_token'] = False
            await update.message.reply_text(
                "👤 آیدی عددی ادمین این ربات رو بفرست (از @userinfobot)")
            return WAITING_FOR_ADMIN_ID
            
        except Exception as e:
            logger.error(f"Error creating bot: {e}")
            await update.message.reply_text(
                "❌ ساخت ربات ناموفق بود. توکن رو چک کن و دوباره بفرست.\n"
                "برای لغو /cancel رو بزن."
            )
            return WAITING_FOR_BOT_TOKEN
        
        return WAITING_FOR_BOT_TOKEN

    async def route_bot_creation_inputs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route incoming text during bot creation: token vs admin/channel IDs."""
        text = (update.message.text or "").strip()
        # If waiting for admin/channel, let generic text handler process it
        if context.user_data.get('awaiting_admin_id'):
            return await self.handle_admin_id_input(update, context)
        if context.user_data.get('awaiting_channel_id'):
            return await self.handle_channel_id_input(update, context)
        # Otherwise treat as token
        return await self.handle_bot_token(update, context)

    async def handle_text_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin inline inputs for settings updates"""
        user_id = update.effective_user.id
        text = (update.message.text or "").strip()

        # Always catch Telegram bot token patterns to start creation flow promptly
        # This ensures that if a user sends a token outside the exact conversation flow, we still proceed.
        try:
            import re
            token_pattern = r'^\d{6,}:[A-Za-z0-9_-]{30,}$'
            if re.match(token_pattern, text):
                # Clear any pending flags related to other steps and delegate to token handler
                context.user_data['awaiting_bot_token'] = False
                context.user_data['awaiting_admin_id'] = False
                context.user_data['awaiting_channel_id'] = False
                await self.handle_bot_token(update, context)
                return
        except Exception:
            # Non-fatal; continue with other handlers
            pass

        # Broadcast text flow
        if await db.is_admin(user_id) and context.user_data.get('awaiting_broadcast_text'):
            context.user_data['awaiting_broadcast_text'] = False
            await update.message.reply_text("⏳ در حال ارسال پیام به همه کاربران...")
            sent, failed = await self._broadcast_text_to_all(context, text)
            await update.message.reply_text(f"✅ ارسال همگانی انجام شد.\nارسال‌شده: {sent}\nناموفق: {failed}")
            return

        # Bot creation: collect admin id and channel id
        if context.user_data.get('awaiting_admin_id'):
            return await self.handle_admin_id_input(update, context)
        if context.user_data.get('awaiting_channel_id'):
            return await self.handle_channel_id_input(update, context)

        # Existing logic continues...
        
        # If user is in bot-token flow, accept Telegram token here as a fallback (kept for safety)
        if context.user_data.get('awaiting_bot_token'):
            try:
                import re
                if re.match(r'^\d{6,}:[A-Za-z0-9_-]{30,}$', text):
                    # Clear flag and delegate to token handler
                    context.user_data['awaiting_bot_token'] = False
                    await self.handle_bot_token(update, context)
                    return
            except Exception:
                pass

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
    
    async def show_subscription_plans(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show subscription plans (Persian casual)"""
        # Pull latest prices from settings (fallback to Config)
        price_1 = await db.get_setting('PRICE_1_MONTH')
        price_2 = await db.get_setting('PRICE_2_MONTHS')
        price_3 = await db.get_setting('PRICE_3_MONTHS')
        try:
            p1 = float(price_1) if price_1 is not None else float(Config.PRICE_1_MONTH or 0)
            p2 = float(price_2) if price_2 is not None else float(Config.PRICE_2_MONTHS or 0)
            p3 = float(price_3) if price_3 is not None else float(Config.PRICE_3_MONTHS or 0)
        except Exception:
            p1 = float(Config.PRICE_1_MONTH or 0)
            p2 = float(Config.PRICE_2_MONTHS or 0)
            p3 = float(Config.PRICE_3_MONTHS or 0)

        plans_text = (
            "💳 **پلن‌های اشتراک**\n\n"
            "یکی از پلن‌ها رو انتخاب کن تا رباتت فعال بشه:\n\n"
            "**پلن ۱ ماهه**\n"
            f"💰 قیمت: ${p1:.2f}\n"
            f"⏰ مدت: {Config.PLAN_1_MONTH} روز\n"
            "🆔 شناسه پلن: plan_1_month\n\n"
            "**پلن ۲ ماهه**\n"
            f"💰 قیمت: ${p2:.2f}\n"
            f"⏰ مدت: {Config.PLAN_2_MONTHS} روز\n"
            "🆔 شناسه پلن: plan_2_months\n\n"
            "**پلن ۳ ماهه**\n"
            f"💰 قیمت: ${p3:.2f}\n"
            f"⏰ مدت: {Config.PLAN_3_MONTHS} روز\n"
            "🆔 شناسه پلن: plan_3_months\n\n"
            "**روش‌های پرداخت:**\n"
            "• کارت‌به‌کارت\n"
            "• ارز دیجیتال\n\n"
            "روی پلن دلخواهت بزن تا ادامه بدیم."
        )
        
        keyboard = [
            [
                InlineKeyboardButton("۱ ماهه - ${:.2f}".format(p1), callback_data="plan_1_month"),
                InlineKeyboardButton("۲ ماهه - ${:.2f}".format(p2), callback_data="plan_2_months")
            ],
            [InlineKeyboardButton("۳ ماهه - ${:.2f}".format(p3), callback_data="plan_3_months")],
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
        """Show user's bots (HTML, safe, with real newlines)"""
        bots = await db.get_user_bots(user_id)
        
        if not bots:
            text = "<b>🤖 ربات‌های شما</b>\n\nهنوز هیچ رباتی ندارید.\n\nبرای شروع روی ‘ایجاد ربات جدید’ کلیک کنید!"
            keyboard = [[InlineKeyboardButton("➕ ایجاد ربات جدید", callback_data="create_bot")]]
        else:
            text = "<b>🤖 ربات‌های شما</b>\n\n"
            keyboard = []
            
            for bot in bots:
                subscription = await db.get_bot_subscription(bot['id'])
                is_active = await db.is_subscription_active(bot['id'])
                is_running = await bot_manager.is_bot_running(bot['id'])
                
                status_emoji = "🟢" if is_running and is_active else "🔴"
                status_text = "فعال" if is_running and is_active else "غیرفعال"
                
                username_html = f"<b>@{escape(str(bot['bot_username']))}</b>"
                
                if subscription:
                    end_date = datetime.fromisoformat(subscription['end_date'])
                    days_left = (end_date - datetime.now()).days
                    # Human-friendly plan name
                    plan_key = str(subscription['plan_type'] or '')
                    plan_display = {
                        'plan_1_month': '۱ ماهه',
                        'plan_2_months': '۲ ماهه',
                        'plan_3_months': '۳ ماهه',
                    }.get(plan_key, escape(plan_key))
                    text += f"{status_emoji} {username_html}\n"
                    text += f"وضعیت: {status_text}\n"
                    text += f"پلن: {plan_display}\n"
                    text += f"روزهای باقی‌مانده: {days_left}\n\n"
                else:
                    text += f"🔴 {username_html}\n"
                    text += "وضعیت: بدون اشتراک\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"مدیریت @{bot['bot_username']}", 
                        callback_data=f"bot_{bot['id']}"
                    ),
                    InlineKeyboardButton(
                        "🗑️ حذف",
                        callback_data=f"delete_bot_{bot['id']}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("➕ ایجاد ربات جدید", callback_data="create_bot")])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])
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
            # Skip edit if content hasn't changed to avoid 'Message is not modified'
            try:
                current_msg = update.callback_query.message
                if current_msg and getattr(current_msg, 'text', None) == text:
                    try:
                        await update.callback_query.answer()
                    except Exception:
                        pass
                    return
            except Exception:
                pass
            try:
                await update.callback_query.edit_message_text(
                    text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            except Exception as e:
                try:
                    from telegram.error import BadRequest
                    if isinstance(e, BadRequest) and 'Message is not modified' in str(e):
                        pass
                    else:
                        raise
                except Exception:
                    if 'Message is not modified' not in str(e):
                        raise
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
        logger.info("[PAYMENT] handle_payment_proof triggered")
        result = await payment_handler.handle_payment_proof(update, context)
        if result == "WAITING_FOR_PAYMENT_PROOF":
            return WAITING_FOR_PAYMENT_PROOF
        return result

    async def handle_admin_id_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle numeric admin ID during bot creation flow."""
        text = (update.message.text or "").strip()
        try:
            admin_id = int(text)
        except Exception:
            await update.message.reply_text("❌ آیدی عددی نامعتبره. فقط عدد بفرست.")
            return WAITING_FOR_ADMIN_ID
        context.user_data['awaiting_admin_id'] = False
        context.user_data['awaiting_channel_id'] = True
        context.user_data['pending_admin_id'] = admin_id
        await update.message.reply_text("🔒 آیدی کانال قفل (یا @username) رو بفرست. اگه نداری، بنویس: -")
        return WAITING_FOR_CHANNEL_ID

    async def handle_channel_id_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle channel ID or '-' during bot creation flow."""
        text = (update.message.text or "").strip()
        channel_id = text if text != '-' else None
        bot_id = context.user_data.get('new_bot_id')
        admin_id = context.user_data.get('pending_admin_id')
        if bot_id:
            await db.update_bot_admin_and_channel(bot_id, admin_user_id=admin_id, locked_channel_id=channel_id)
            # Auto-activate demo subscription for the first bot of this user
            try:
                if int(getattr(Config, 'DEMO_DURATION_DAYS', 0)) > 0:
                    user_id = update.effective_user.id
                    bots = await db.get_user_bots(user_id)
                    if bots and len(bots) == 1 and int(bots[0]['id']) == int(bot_id):
                        # Grant demo subscription
                        await db.add_subscription(bot_id, 'demo', int(Config.DEMO_DURATION_DAYS))
                        # Try to deploy immediately
                        try:
                            bot_info = await db.get_bot(bot_id)
                            if bot_info and bot_info.get('bot_token'):
                                await bot_manager.deploy_bot(bot_id, bot_info['bot_token'])
                        except Exception as e:
                            logger.error(f"Error deploying demo bot {bot_id}: {e}")
                        try:
                            await update.message.reply_text(
                                f"🎁 دمو {int(Config.DEMO_DURATION_DAYS)} روزه فعال شد. از منو «📋 ربات‌های من» مدیریت کن.")
                        except Exception:
                            pass
            except Exception as e:
                logger.error(f"Error during demo activation for bot {bot_id}: {e}")
        context.user_data['awaiting_channel_id'] = False
        await update.message.reply_text("✅ تنظیمات ربات ثبت شد. برای فعال‌سازی، از منو روی /subscribe بزن.")
        return ConversationHandler.END
    
    async def handle_submit_proof_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment proof submission callback: submit_proof_<method>_<plan_type>_<bot_id>"""
        data = update.callback_query.data
        parts = data.split("_")
        if len(parts) >= 6:
            payment_method = parts[2]
            bot_id = int(parts[-1])
            plan_type = "_".join(parts[3:-1])
            logger.info(f"[PAYMENT] submit_proof clicked: method={payment_method} plan={plan_type} bot_id={bot_id}")
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
        
        # Use HTML to avoid Markdown entity parsing issues (e.g., underscores in usernames)
        safe_username = escape(str(bot['bot_username']))
        status_title = escape(str(status['status']).title())
        created_at = escape(str(status['created_at']))
        last_activity = escape(str(status['last_activity'] or 'هرگز'))
        text = (
            f"<b>🤖 مدیریت ربات: @{safe_username}</b>\n\n"
            f"<b>وضعیت:</b> {status_title}\n"
            f"<b>در حال اجرا:</b> {'✅ بله' if status['is_running'] else '❌ خیر'}\n"
            f"<b>اشتراک:</b> {'✅ فعال' if status['subscription_active'] else '❌ غیرفعال'}\n\n"
            f"<b>جزئیات ربات:</b>\n"
            f"• ایجاد شده: {created_at}\n"
            f"• آخرین فعالیت: {last_activity}"
        )
        
        if subscription:
            end_date = datetime.fromisoformat(subscription['end_date'])
            days_left = (end_date - datetime.now()).days
            text += (
                f"\n• پلن: <code>{escape(str(subscription['plan_type']))}</code>\n"
                f"• انقضا: {escape(end_date.strftime('%Y-%m-%d'))}\n"
                f"• روزهای باقی‌مانده: {days_left}"
            )
        
        keyboard = []
        
        if status['subscription_active']:
            if status['is_running']:
                keyboard.append([InlineKeyboardButton("⏹️ توقف ربات", callback_data=f"stop_bot_{bot_id}")])
            else:
                keyboard.append([InlineKeyboardButton("▶️ شروع ربات", callback_data=f"start_bot_{bot_id}")])
            keyboard.append([InlineKeyboardButton("🔄 راه‌اندازی مجدد ربات", callback_data=f"restart_bot_{bot_id}")])
        else:
            keyboard.append([InlineKeyboardButton("💳 اشتراک", callback_data="subscribe")])
        
        keyboard.append([
            InlineKeyboardButton("🗑️ حذف ربات", callback_data=f"delete_bot_{bot_id}"),
            InlineKeyboardButton("🔙 بازگشت به ربات‌های من", callback_data="my_bots")
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Avoid Telegram BadRequest: Message is not modified
        try:
            await update.callback_query.edit_message_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        except Exception as e:
            try:
                from telegram.error import BadRequest
                if isinstance(e, BadRequest) and 'Message is not modified' in str(e):
                    # Ignore harmless error
                    pass
                else:
                    raise
            except Exception:
                # If telegram.error is not available for isinstance, fallback to string check
                if 'Message is not modified' not in str(e):
                    raise

    async def prompt_delete_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: int):
        """Ask user to confirm deleting the bot."""
        user_id = update.callback_query.from_user.id
        bot = await db.get_bot(bot_id)
        if not bot or bot['owner_id'] != user_id:
            await update.callback_query.answer("دسترسی غیرمجاز", show_alert=True)
            return
        text = (
            f"⚠️ آیا از حذف ربات @{bot['bot_username']} مطمئنی؟\n\n"
            "این کار قابل بازگشت نیست و فایل‌های استقرار هم حذف می‌شن."
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ بله، حذف کن", callback_data=f"confirm_delete_{bot_id}"),
                InlineKeyboardButton("❌ خیر، انصراف", callback_data=f"cancel_delete_{bot_id}")
            ]
        ]
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def confirm_delete_bot(self, update: Update, context: ContextTypes.DEFAULT_TYPE, bot_id: int):
        """Delete the bot after confirmation."""
        user_id = update.callback_query.from_user.id
        bot = await db.get_bot(bot_id)
        if not bot or bot['owner_id'] != user_id:
            await update.callback_query.answer("دسترسی غیرمجاز", show_alert=True)
            return
        # Stop and remove files
        try:
            await bot_manager.delete_bot(bot_id)
        except Exception:
            pass
        # Remove from DB
        ok = await db.delete_bot(bot_id, owner_id=user_id)
        if ok:
            await update.callback_query.edit_message_text("🗑️ ربات حذف شد.")
            # Show updated list
            await self.show_user_bots(update, context, user_id)
        else:
            await update.callback_query.edit_message_text("❌ حذف ربات ناموفق بود.")
    
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
        elif data == "broadcast_text":
            context.user_data['awaiting_broadcast_text'] = True
            context.user_data['awaiting_broadcast_forward'] = False
            await update.callback_query.edit_message_text(
                "📢 متن پیام همگانی را بفرستید.\n\nبرای لغو، /cancel را بزنید.")
        elif data == "broadcast_forward":
            context.user_data['awaiting_broadcast_forward'] = True
            context.user_data['awaiting_broadcast_text'] = False
            await update.callback_query.edit_message_text(
                "📨 پیامی که می‌خواهید فوروارد شود را همینجا ارسال/فوروارد کنید.\n\nبرای لغو، /cancel را بزنید.")
        elif data == "update_prices":
            await self.prompt_update_prices(update, context)
        elif data == "update_payment_info":
            await self.prompt_update_payment_info(update, context)
        elif data.startswith("approve_payment_"):
            try:
                payment_id = int(data.split("_")[-1])
                ok = await payment_handler.approve_payment(payment_id, user_id)
                if ok:
                    await self.show_pending_payments(update, context)
                else:
                    await update.callback_query.answer("خطا در تایید پرداخت", show_alert=True)
            except Exception:
                await update.callback_query.answer("خطا در تایید پرداخت", show_alert=True)
        elif data.startswith("reject_payment_"):
            try:
                payment_id = int(data.split("_")[-1])
                ok = await payment_handler.reject_payment(payment_id, user_id)
                if ok:
                    await self.show_pending_payments(update, context)
                else:
                    await update.callback_query.answer("خطا در رد پرداخت", show_alert=True)
            except Exception:
                await update.callback_query.answer("خطا در رد پرداخت", show_alert=True)
    
    @handle_telegram_errors
    async def show_pending_payments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show pending payments for admin"""
        payments = await db.get_pending_payments()
        
        if not payments:
            text = "<b>💳 پرداخت‌های در انتظار</b>\n\nهیچ پرداخت در انتظاری یافت نشد."
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]]
        else:
            text = "<b>💳 پرداخت‌های در انتظار</b>\n\n"
            keyboard = []
            
            for payment in payments:
                user_display = payment.get('username')
                if user_display:
                    user_display = '@' + user_display
                else:
                    user_display = payment.get('first_name') or f"ID {payment.get('user_id')}"
                text += f"<b>پرداخت #{payment['id']}</b>\n"
                text += f"کاربر: {escape(str(user_display))}\n"
                text += f"مبلغ: ${payment['amount']:.2f}\n"
                text += f"پلن: <code>{escape(str(payment['plan_type']))}</code>\n"
                text += f"روش: {escape(str(payment['payment_method']))}\n"
                text += f"تاریخ: {escape(str(payment['created_at']))}\n\n"
                
                keyboard.append([
                    InlineKeyboardButton(f"✅ تایید #{payment['id']}", callback_data=f"approve_payment_{payment['id']}"),
                    InlineKeyboardButton(f"❌ رد #{payment['id']}", callback_data=f"reject_payment_{payment['id']}")
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def show_all_bots(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all bots for admin (HTML)"""
        bots = await db.get_all_bots()
        
        if not bots:
            text = "<b>🤖 همه ربات‌ها</b>\n\nهیچ رباتی یافت نشد."
        else:
            text = "<b>🤖 همه ربات‌ها</b>\n\n"
            
            for bot in bots:
                subscription = await db.get_bot_subscription(bot['id'])
                is_active = await db.is_subscription_active(bot['id'])
                is_running = await bot_manager.is_bot_running(bot['id'])
                
                status_emoji = "🟢" if is_running and is_active else "🔴"
                safe_username = escape(str(bot['bot_username']))
                text += f"{status_emoji} <b>@{safe_username}</b>\n"
                text += f"Owner: {bot['owner_id']}\n"
                text += f"Status: {escape(str(bot['status']))}\n"
                text += f"Running: {'Yes' if is_running else 'No'}\n"
                text += f"Subscription: {'Active' if is_active else 'Inactive'}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_panel")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def show_users_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """نمایش مدیریت کاربران (فارسی) با صفحه‌بندی و اکشن‌ها"""
        query = update.callback_query
        data = (query.data or "")
        # صفحه فعلی از callback_data استخراج شود: users_page_<n>
        page = 1
        if data.startswith("users_page_"):
            try:
                page = int(data.split("_")[-1])
            except Exception:
                page = 1
        # اندازه صفحه
        page_size = 10
        offset = (page - 1) * page_size
        # آمار و لیست
        total = await db.count_users()
        actives = await db.count_active_users()
        admins = await db.count_admin_users()
        users = await db.get_users_paginated(offset=offset, limit=page_size)

        from html import escape
        text = (
            f"<b>👥 مدیریت کاربران</b>\n\n"
            f"کل کاربران: {total}\n"
            f"فعال: {actives}\n"
            f"ادمین‌ها: {admins}\n\n"
            f"<b>لیست (صفحه {page}):</b>\n"
        )
        if not users:
            text += "— لیستی برای نمایش نیست —"
        else:
            for u in users:
                uid = u.get('user_id')
                uname = (('@' + u['username']) if u.get('username') else (u.get('first_name') or 'بدون‌نام'))
                role = u.get('role') or '-'
                is_active = bool(u.get('is_active'))
                text += (
                    f"• {escape(str(uname))} (<code>{uid}</code>)\n"
                    f"  نقش: <b>{escape(str(role))}</b> | وضعیت: {'✅ فعال' if is_active else '❌ غیرفعال'}\n"
                )

        # دکمه‌ها: صفحه‌بندی + برگشت + راهنمای اکشن‌ها
        keyboard = []
        nav_row = []
        max_page = max(1, (total + page_size - 1) // page_size)
        if page > 1:
            nav_row.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"users_page_{page-1}"))
        if page < max_page:
            nav_row.append(InlineKeyboardButton("بعدی ➡️", callback_data=f"users_page_{page+1}"))
        if nav_row:
            keyboard.append(nav_row)
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")])

        # توضیح اکشن‌ها (با دستور اینلاین)
        text += (
            "\n<b>اکشن‌ها:</b>\n"
            "- برای تغییر نقش: /role &lt;user_id&gt; &lt;admin|user&gt;\n"
            "- برای فعال/غیرفعال: /active &lt;user_id&gt; &lt;1|0&gt;\n"
        )

        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_broadcast_capture(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Capture any message when awaiting broadcast forward, and dispatch broadcast."""
        try:
            user_id = update.effective_user.id if update.effective_user else None
            if not user_id or not await db.is_admin(user_id):
                return
            # Text-broadcast mode: send plain text to all
            if context.user_data.get('awaiting_broadcast_text') and getattr(update.effective_message, 'text', None):
                # Ignore commands
                if not update.effective_message.text.startswith('/'):
                    context.user_data['awaiting_broadcast_text'] = False
                    await update.effective_message.reply_text("⏳ در حال ارسال پیام به همه کاربران...")
                    sent, failed = await self._broadcast_text_to_all(context, update.effective_message.text)
                    await update.effective_message.reply_text(
                        f"✅ ارسال همگانی انجام شد.\nارسال‌شده: {sent}\nناموفق: {failed}")
                    return
            # Forward-mode: accept any message
            if context.user_data.get('awaiting_broadcast_forward'):
                context.user_data['awaiting_broadcast_forward'] = False
                # Source chat/message for forward
                src_chat_id = update.effective_chat.id
                msg_id = update.effective_message.message_id
                await update.effective_message.reply_text("⏳ در حال فوروارد به همه کاربران...")
                sent, failed = await self._broadcast_forward_to_all(context, src_chat_id, msg_id)
                await update.effective_message.reply_text(
                    f"✅ فوروارد انجام شد.\nارسال‌شده: {sent}\nناموفق: {failed}")
        except Exception as e:
            try:
                await update.effective_message.reply_text("❌ خطا در فوروارد همگانی.")
            except Exception:
                pass

    async def _iterate_active_user_ids(self, batch_size: int = 500):
        """Async generator yielding active user_ids in batches."""
        offset = 0
        while True:
            users = await db.get_users_paginated(offset=offset, limit=batch_size)
            if not users:
                break
            active_ids = [u['user_id'] for u in users if u.get('is_active')]
            if active_ids:
                yield active_ids
            offset += batch_size

    async def _broadcast_text_to_all(self, context: ContextTypes.DEFAULT_TYPE, text: str) -> tuple[int, int]:
        """Send plain text to all active users. Returns (sent, failed)."""
        sent = 0
        failed = 0
        async for batch in self._iterate_active_user_ids():
            for uid in batch:
                try:
                    await context.bot.send_message(chat_id=int(uid), text=text)
                    sent += 1
                except Exception:
                    failed += 1
                await asyncio.sleep(0.03)
        return sent, failed

    async def _broadcast_forward_to_all(self, context: ContextTypes.DEFAULT_TYPE, from_chat_id: int, message_id: int) -> tuple[int, int]:
        """Forward a message to all active users. Returns (sent, failed)."""
        sent = 0
        failed = 0
        async for batch in self._iterate_active_user_ids():
            for uid in batch:
                try:
                    await context.bot.forward_message(chat_id=int(uid), from_chat_id=from_chat_id, message_id=message_id)
                    sent += 1
                except Exception:
                    failed += 1
                await asyncio.sleep(0.03)
        return sent, failed

    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """بازنویسی /users برای نمایش پنل مدیریت کاربران"""
        user_id = update.effective_user.id
        if not await db.is_admin(user_id):
            await update.message.reply_text("❌ دسترسی رد شد.")
            return
        # شبیه callback، اما با reply
        # آمار و صفحه اول
        total = await db.count_users()
        actives = await db.count_active_users()
        admins = await db.count_admin_users()
        users = await db.get_users_paginated(offset=0, limit=10)
        from html import escape
        text = (
            f"<b>👥 مدیریت کاربران</b>\n\n"
            f"کل کاربران: {total}\n"
            f"فعال: {actives}\n"
            f"ادمین‌ها: {admins}\n\n"
            f"<b>لیست (صفحه 1):</b>\n"
        )
        if not users:
            text += "— لیستی برای نمایش نیست —"
        else:
            for u in users:
                uid = u.get('user_id')
                uname = (('@' + u['username']) if u.get('username') else (u.get('first_name') or 'بدون‌نام'))
                role = u.get('role') or '-'
                is_active = bool(u.get('is_active'))
                text += (
                    f"• {escape(str(uname))} (<code>{uid}</code>)\n"
                    f"  نقش: <b>{escape(str(role))}</b> | وضعیت: {'✅ فعال' if is_active else '❌ غیرفعال'}\n"
                )
        keyboard = [
            [InlineKeyboardButton("بعدی ➡️", callback_data="users_page_2")],
            [InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]
        ]
        text += (
            "\n<b>اکشن‌ها:</b>\n"
            "- برای تغییر نقش: /role &lt;user_id&gt; &lt;admin|user&gt;\n"
            "- برای فعال/غیرفعال: /active &lt;user_id&gt; &lt;1|0&gt;\n"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    async def set_user_role_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/role <user_id> <admin|user>"""
        user_id = update.effective_user.id
        if not await db.is_admin(user_id):
            await update.message.reply_text("❌ دسترسی رد شد.")
            return
        try:
            args = context.args
            target_id = int(args[0])
            role = args[1].lower()
            if role not in (Config.USER_ROLE_ADMIN, Config.USER_ROLE_USER):
                raise ValueError("bad role")
            ok = await db.set_user_role(target_id, role)
            await update.message.reply_text("✅ نقش کاربر بروزرسانی شد." if ok else "❌ بروزرسانی نقش ناموفق.")
        except Exception:
            await update.message.reply_text("❌ فرمت: /role <user_id> <admin|user>")

    async def set_user_active_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """/active <user_id> <1|0>"""
        user_id = update.effective_user.id
        if not await db.is_admin(user_id):
            await update.message.reply_text("❌ دسترسی رد شد.")
            return
        try:
            args = context.args
            target_id = int(args[0])
            active_val = int(args[1])
            if active_val not in (0, 1):
                raise ValueError("bad active")
            ok = await db.set_user_active(target_id, bool(active_val))
            await update.message.reply_text("✅ وضعیت کاربر بروزرسانی شد." if ok else "❌ بروزرسانی وضعیت ناموفق.")
        except Exception:
            await update.message.reply_text("❌ فرمت: /active <user_id> <1|0>")
    
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
        """Show broadcast panel for admin (Persian)"""
        text = (
            "<b>📢 ارسال همگانی</b>\n\n"
            "دو روش دارید:\n"
            "• <b>ارسال متن:</b> یک متن جدید برای همه ارسال می‌شود.\n"
            "• <b>فوروارد پیام:</b> پیامی که می‌فرستید به همه فوروارد می‌شود.\n\n"
            "پس از انتخاب، راهنما نمایش داده می‌شود."
        )
        keyboard = [
            [InlineKeyboardButton("📝 ارسال متن", callback_data="broadcast_text")],
            [InlineKeyboardButton("↪️ فوروارد پیام", callback_data="broadcast_forward")],
            [InlineKeyboardButton("🔙 بازگشت به پنل ادمین", callback_data="admin_panel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    
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

    async def show_system_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system statistics in setup panel"""
        all_bots = await db.get_all_bots()
        active_bots = 0
        running_bots = 0
        for bot in all_bots:
            if await db.is_subscription_active(bot['id']):
                active_bots += 1
            if await bot_manager.is_bot_running(bot['id']):
                running_bots += 1
        text = (
            "📊 **آمار سیستم**\n\n"
            f"• کل کاربران: -\n"
            f"• کل ربات‌ها: {len(all_bots)}\n"
            f"• ربات‌های دارای اشتراک فعال: {active_bots}\n"
            f"• ربات‌های در حال اجرا: {running_bots}\n"
        )
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="setup_panel")]]
        await update.callback_query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_restart_all_bots(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Restart all bots from setup panel"""
        summary = await bot_manager.restart_all_bots()
        await update.callback_query.answer("در حال راه‌اندازی مجدد ربات‌ها", show_alert=False)
        # Notify admin with results
        try:
            if Config.ADMIN_USER_ID:
                from html import escape
                def fmt_list(items):
                    if not items:
                        return "—"
                    return "\n".join([f"• @{escape(str(x.get('username') or '-'))} (ID {x.get('id')})" for x in items])
                text = (
                    "<b>🔄 گزارش راه‌اندازی مجدد همه ربات‌ها</b>\n\n"
                    f"<b>تعداد راه‌اندازی‌شده‌ها:</b> {len(summary.get('restarted', []))}\n"
                    f"<b>تعداد فقط آپدیت‌شده‌ها:</b> {len(summary.get('updated_only', []))}\n"
                    f"<b>تعداد متوقف‌شده‌های منقضی:</b> {len(summary.get('stopped_expired', []))}\n"
                    f"<b>تعداد متوقف‌شده‌های بدون اشتراک:</b> {len(summary.get('stopped_inactive', []))}\n"
                    f"<b>خطاها:</b> {len(summary.get('errors', []))}\n\n"
                    f"<b>🟢 راه‌اندازی‌شده‌ها:</b>\n{fmt_list(summary.get('restarted'))}\n\n"
                    f"<b>🛠 فقط آپدیت‌شده‌ها:</b>\n{fmt_list(summary.get('updated_only'))}\n\n"
                    f"<b>⛔ متوقف‌شده‌های منقضی:</b>\n{fmt_list(summary.get('stopped_expired'))}\n\n"
                    f"<b>⚪ متوقف‌شده‌های بدون اشتراک:</b>\n{fmt_list(summary.get('stopped_inactive'))}"
                )
                if summary.get('errors'):
                    err_lines = "\n".join([f"• @{escape(str(x.get('username') or '-'))} (ID {x.get('id')}): {escape(str(x.get('error')))}" for x in summary.get('errors')])
                    text += f"\n\n<b>❗ خطاها:</b>\n{err_lines}"
                await context.bot.send_message(chat_id=int(Config.ADMIN_USER_ID), text=text, parse_mode=ParseMode.HTML)
        except Exception:
            pass
        await self.show_setup_panel(update, context)

    async def handle_cleanup_expired(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cleanup expired bots from setup panel"""
        summary = await bot_manager.cleanup_expired_bots()
        await update.callback_query.answer("پاکسازی انجام شد", show_alert=False)
        # Notify admin with results
        try:
            if Config.ADMIN_USER_ID:
                from html import escape
                def fmt_list(items):
                    if not items:
                        return "—"
                    return "\n".join([f"• @{escape(str(x.get('username') or '-'))} (ID {x.get('id')})" for x in items])
                text = (
                    "<b>🧹 گزارش پاکسازی ربات‌های منقضی</b>\n\n"
                    f"<b>تعداد متوقف‌شده‌ها:</b> {len(summary.get('stopped_expired', []))}\n"
                    f"<b>تعداد از قبل غیرفعال:</b> {len(summary.get('already_inactive_expired', []))}\n\n"
                    f"<b>⛔ متوقف‌شده‌ها:</b>\n{fmt_list(summary.get('stopped_expired'))}\n\n"
                    f"<b>⚪ از قبل غیرفعال:</b>\n{fmt_list(summary.get('already_inactive_expired'))}"
                )
                await context.bot.send_message(chat_id=int(Config.ADMIN_USER_ID), text=text, parse_mode=ParseMode.HTML)
        except Exception:
            pass
        await self.show_setup_panel(update, context)

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
        
        # Start the bot using async initialization to work with asyncio.run()
        if self.application is None:
            self.setup_handlers()
        logger.info("Main bot starting polling...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Main bot started successfully!")
        
        try:
            # Keep the bot running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            try:
                await monitor.stop_monitoring()
            except Exception:
                pass
            try:
                await self.application.stop()
            except Exception:
                pass

# Create and run the main bot
if __name__ == '__main__':
    main_bot = MainBot()
    asyncio.run(main_bot.run())