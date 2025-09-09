import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode
from config import Config
from database import db
from bot_manager import bot_manager

logger = logging.getLogger(__name__)

class PaymentHandler:
    def __init__(self):
        pass
    
    async def handle_plan_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, plan_type: str):
        """Handle plan selection and show payment options"""
        query = update.callback_query
        user_id = query.from_user.id
        
        # Get plan details (runtime from settings)
        plan_details = await self.get_runtime_plan_details(plan_type)
        if not plan_details:
            await query.edit_message_text("❌ Invalid plan selected.")
            return
        
        # Get user's bots
        user_bots = await db.get_user_bots(user_id)
        if not user_bots:
            await query.edit_message_text(
                "❌ هنوز رباتی نساختی.\\n"
                "اول با گزینه ‘ایجاد ربات جدید’ یکی بساز بعد بیا اینجا."
            )
            return
        
        # Show bot selection (use HTML to avoid Markdown entity issues)
        from html import escape
        text = (
            f"<b>💳 پرداخت برای {escape(str(plan_details['name']))}</b>\n\n"
            f"💰 <b>مبلغ:</b> ${plan_details['price']:.2f}\n"
            f"⏰ <b>مدت:</b> {plan_details['duration']} روز\n"
            f"🆔 <b>شناسه پلن:</b> <code>{escape(str(plan_type))}</code>\n\n"
            f"<b>یکی از ربات‌هات رو انتخاب کن:</b>"
        )
        
        keyboard = []
        for bot in user_bots:
            subscription = await db.get_bot_subscription(bot['id'])
            is_active = await db.is_subscription_active(bot['id'])
            
            if is_active:
                status = "🟢 فعال"
            elif subscription:
                status = "🔴 منقضی"
            else:
                status = "⚪ بدون اشتراک"
            
            keyboard.append([InlineKeyboardButton(
                f"@{bot['bot_username']} - {status}",
                callback_data=f"payment_{plan_type}_{bot['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به پلن‌ها", callback_data="subscribe")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def handle_payment_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     plan_type: str, bot_id: int):
        """Handle payment method selection (Persian)"""
        query = update.callback_query
        user_id = query.from_user.id
        
        # Get plan details
        plan_details = await self.get_runtime_plan_details(plan_type)
        if not plan_details:
            await query.edit_message_text("❌ Invalid plan selected.")
            return
        
        # Get bot info
        bot = await db.get_bot(bot_id)
        if not bot or bot['owner_id'] != user_id:
            await query.edit_message_text("❌ Bot not found or access denied.")
            return
        
        # Show payment methods (use HTML and escape username)
        from html import escape
        safe_bot_username = escape(str(bot['bot_username']))
        text = (
            f"<b>💳 جزئیات پرداخت</b>\n\n"
            f"🤖 <b>ربات:</b> @{safe_bot_username}\n"
            f"💰 <b>پلن:</b> {escape(str(plan_details['name']))}\n"
            f"💵 <b>مبلغ:</b> ${plan_details['price']:.2f}\n"
            f"⏰ <b>مدت:</b> {plan_details['duration']} روز\n\n"
            f"<b>روش پرداخت رو انتخاب کن:</b>"
        )
        
        keyboard = [
            [InlineKeyboardButton("🏦 کارت‌به‌کارت", callback_data=f"method_bank_{plan_type}_{bot_id}")],
            [InlineKeyboardButton("₿ ارز دیجیتال", callback_data=f"method_crypto_{plan_type}_{bot_id}")],
            [InlineKeyboardButton("🔙 بازگشت به انتخاب ربات", callback_data=f"{plan_type}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def show_payment_instructions(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                      payment_method: str, plan_type: str, bot_id: int):
        """Show payment instructions (HTML)"""
        query = update.callback_query
        user_id = query.from_user.id
        
        # Get plan details
        plan_details = await self.get_runtime_plan_details(plan_type)
        if not plan_details:
            await query.edit_message_text("❌ Invalid plan selected.")
            return
        
        # Get bot info
        bot = await db.get_bot(bot_id)
        if not bot or bot['owner_id'] != user_id:
            await query.edit_message_text("❌ Bot not found or access denied.")
            return
        
        from html import escape
        safe_bot = escape(str(bot['bot_username']))
        safe_user = escape(str(query.from_user.username or ""))
        # Read bank/wallet from settings with fallback to Config
        bank_val = await db.get_setting('BANK_CARD_NUMBER')
        wallet_val = await db.get_setting('CRYPTO_WALLET_ADDRESS')
        bank = escape(str(bank_val or Config.BANK_CARD_NUMBER or "-"))
        wallet = escape(str(wallet_val or Config.CRYPTO_WALLET_ADDRESS or "-"))

        if payment_method == "bank":
            text = (
                f"<b>🏦 پرداخت کارت‌به‌کارت</b>\n\n"
                f"🤖 <b>ربات:</b> @{safe_bot}\n"
                f"💰 <b>مبلغ:</b> ${plan_details['price']:.2f}\n"
                f"⏰ <b>مدت:</b> {plan_details['duration']} روز\n\n"
                f"<b>راهنمای پرداخت:</b>\n"
                f"1) مبلغ {plan_details['price']:.2f}$ رو به کارت زیر واریز کن:\n   <code>{bank}</code>\n\n"
                f"2) از رسید پرداخت اسکرین‌شات بگیر\n\n"
                f"3) همینجا عکس رسید رو بفرست\n\n"
                f"4) منتظر تایید ادمین بمون (معمولاً تا ۲۴ ساعت)\n\n"
                f"نکته: اگه شد، یوزرنیمت (@{safe_user}) رو تو توضیحات پرداخت بنویس."
            )
        else:  # crypto
            text = (
                f"<b>₿ پرداخت ارز دیجیتال</b>\n\n"
                f"🤖 <b>ربات:</b> @{safe_bot}\n"
                f"💰 <b>مبلغ:</b> ${plan_details['price']:.2f}\n"
                f"⏰ <b>مدت:</b> {plan_details['duration']} روز\n\n"
                f"<b>راهنمای پرداخت:</b>\n"
                f"1) معادل {plan_details['price']:.2f}$ ارز دیجیتال به این آدرس بفرست:\n   <code>{wallet}</code>\n\n"
                f"2) شناسه/هش تراکنش رو کپی کن\n\n"
                f"3) همینجا شناسه تراکنش رو بفرست\n\n"
                f"4) منتظر تایید ادمین بمون (معمولاً تا ۲۴ ساعت)\n\n"
                f"نکته: مبلغ دقیق رو بفرست که مشکلی پیش نیاد."
            )
        
        keyboard = [
            [InlineKeyboardButton("✅ پرداخت کردم", callback_data=f"submit_proof_{payment_method}_{plan_type}_{bot_id}")],
            [InlineKeyboardButton("🔙 برگشت به روش‌های پرداخت", callback_data=f"payment_{plan_type}_{bot_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )
    
    async def start_payment_proof_submission(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                           payment_method: str, plan_type: str, bot_id: int):
        """Start payment proof submission"""
        query = update.callback_query
        
        # Store payment info in context
        context.user_data['payment_method'] = payment_method
        context.user_data['plan_type'] = plan_type
        context.user_data['bot_id'] = bot_id
        
        await query.edit_message_text(
            (
                "<b>📸 ارسال رسید پرداخت</b>\n\n"
                "لطفاً مدرک پرداختتو بفرست:\n"
                "• اسکرین‌شات کارت‌به‌کارت (برای کارت‌به‌کارت)\n"
                "• شناسه/هش تراکنش (برای ارز دیجیتال)\n\n"
                "برای لغو، /cancel رو بزن."
            ),
            parse_mode=ParseMode.HTML
        )
    
    async def handle_payment_proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment proof submission"""
        user_id = update.effective_user.id
        username = update.effective_user.username or ""
        
        # Get payment info from context
        payment_method = context.user_data.get('payment_method')
        plan_type = context.user_data.get('plan_type')
        bot_id = context.user_data.get('bot_id')
        
        if not all([payment_method, plan_type, bot_id]):
            await update.message.reply_text("❌ جلسه پرداخت تموم شده. از اول شروع کن.")
            return ConversationHandler.END
        
        # Get plan details
        plan_details = await self.get_runtime_plan_details(plan_type)
        if not plan_details:
            await update.message.reply_text("❌ پلن نامعتبره.")
            return ConversationHandler.END
        
        # Get bot info
        bot = await db.get_bot(bot_id)
        if not bot or bot['owner_id'] != user_id:
            await update.message.reply_text("❌ ربات پیدا نشد یا دسترسی نداری.")
            return ConversationHandler.END
        
        # Handle different proof types
        proof_text = ""
        if update.message.photo:
            proof_text = f"photo:{update.message.photo[-1].file_id}"
        elif getattr(update.message, 'document', None):
            proof_text = f"document:{update.message.document.file_id}"
        elif update.message.text:
            proof_text = update.message.text
        else:
            await update.message.reply_text("❌ لطفاً عکس رسید، فایل، یا متن شناسه تراکنش رو بفرست.")
            return "WAITING_FOR_PAYMENT_PROOF"
        
        # Add payment to database
        payment_id = await db.add_payment(
            user_id=user_id,
            bot_id=bot_id,
            amount=plan_details['price'],
            plan_type=plan_type,
            payment_method=payment_method,
            payment_proof=proof_text
        )
        
        # Forward proof and details to admin (if configured)
        await self.send_admin_payment_proof(
            context=context,
            payment_id=payment_id,
            user_id=user_id,
            username=username,
            bot=bot,
            plan_details=plan_details,
            payment_method=payment_method,
            message=update.message,
        )

        # Acknowledge to user
        ack_text = (
            "✅ رسید پرداخت با موفقیت ثبت شد!\n\n"
            f"شناسه پرداخت: {payment_id}\n"
            f"مبلغ: ${plan_details['price']:.2f}\n"
            f"روش: {('کارت‌به‌کارت' if payment_method=='bank' else 'ارز دیجیتال')}\n\n"
            "پرداختت رفته برای تایید ادمین.\n"
            "بهت خبر می‌دیم نتیجه چی شد."
        )
        await update.message.reply_text(ack_text)
        
        return ConversationHandler.END
    
    async def notify_admin_new_payment(self, context: ContextTypes.DEFAULT_TYPE, payment_id: int, user_id: int, bot: Dict[str, Any], 
                                     plan_details: Dict[str, Any], payment_method: str):
        """Notify admin about new payment"""
        try:
            logger.info(f"New payment {payment_id} from user {user_id} for bot {bot['id']}")
            if Config.ADMIN_USER_ID:
                text = (
                    f"📥 پرداخت جدید\n"
                    f"شناسه پرداخت: {payment_id}\n"
                    f"کاربر: {user_id}\n"
                    f"ربات: @{bot.get('bot_username','-')}\n"
                    f"پلن: {plan_details.get('name','-')} ({plan_details.get('duration','-')} روز)\n"
                    f"مبلغ: ${plan_details.get('price',0):.2f}\n"
                    f"روش: {'کارت‌به‌کارت' if payment_method=='bank' else 'ارز دیجیتال'}"
                )
                await context.bot.send_message(chat_id=int(Config.ADMIN_USER_ID), text=text)
        except Exception as e:
            logger.error(f"Error notifying admin about payment {payment_id}: {e}")

    async def send_admin_payment_proof(self, context: ContextTypes.DEFAULT_TYPE, payment_id: int, user_id: int, username: str,
                                      bot: Dict[str, Any], plan_details: Dict[str, Any], payment_method: str, message):
        """Send payment details and proof to admin (media-aware)."""
        try:
            if not Config.ADMIN_USER_ID:
                return
            from html import escape
            admin_id = int(Config.ADMIN_USER_ID)
            user_display = f"@{username}" if username else f"User {user_id}"
            safe_bot = escape(str(bot.get('bot_username', '-')))
            safe_user = escape(str(user_display))
            caption = (
                f"<b>📥 پرداخت جدید</b>\n\n"
                f"<b>شناسه پرداخت:</b> <code>#{payment_id}</code>\n"
                f"<b>کاربر:</b> {safe_user} (<code>{user_id}</code>)\n"
                f"<b>ربات:</b> @{safe_bot}\n"
                f"<b>پلن:</b> {escape(str(plan_details.get('name','-')))} ({plan_details.get('duration','-')} روز)\n"
                f"<b>مبلغ:</b> ${plan_details.get('price',0):.2f}\n"
                f"<b>روش:</b> {'کارت‌به‌کارت' if payment_method=='bank' else 'ارز دیجیتال'}"
            )

            # Send media with caption if available, otherwise send text
            if message.photo:
                file_id = message.photo[-1].file_id
                await context.bot.send_photo(chat_id=admin_id, photo=file_id, caption=caption, parse_mode=ParseMode.HTML)
            elif getattr(message, 'document', None):
                file_id = message.document.file_id
                await context.bot.send_document(chat_id=admin_id, document=file_id, caption=caption, parse_mode=ParseMode.HTML)
            elif message.text:
                extra = f"\n\n<b>🧾 مدرک/شناسه:</b>\n<code>{escape(message.text)}</code>"
                await context.bot.send_message(chat_id=admin_id, text=caption + extra, parse_mode=ParseMode.HTML)
            else:
                # Fallback to text-only notification
                await context.bot.send_message(chat_id=admin_id, text=caption, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Error sending admin payment proof for {payment_id}: {e}")
    
    async def approve_payment(self, payment_id: int, admin_id: int) -> bool:
        """Approve a payment: mark approved, add subscription, deploy bot, notify user/admin."""
        try:
            payment = await db.get_payment(payment_id)
            if not payment:
                return False
            bot = await db.get_bot(payment['bot_id']) if payment.get('bot_id') else None
            plan_details = self.get_plan_details(payment['plan_type'])
            if not plan_details:
                return False
            # Update status
            await db.update_payment_status(payment_id, Config.PAYMENT_STATUS_APPROVED, admin_id)
            # Add/extend subscription
            await db.add_subscription(payment['bot_id'], payment['plan_type'], plan_details['duration'])
            # Deploy bot if token available
            deploy_ok = False
            if bot and bot.get('bot_token'):
                deploy_ok = await bot_manager.deploy_bot(payment['bot_id'], bot['bot_token'])
            # Notify user
            try:
                from telegram import Bot as PTBBot
                # Using main bot to notify
                # context.bot is not here, so use a new Bot
                notify_bot = PTBBot(token=Config.MAIN_BOT_TOKEN)
                await notify_bot.send_message(chat_id=int(payment['user_id']), text=(
                    "✅ پرداخت شما تایید شد!\n\n"
                    f"پلن: {plan_details['name']} ({plan_details['duration']} روز)\n"
                    + ("🤖 ربات شما با موفقیت اجرا شد." if deploy_ok else "ℹ️ اشتراک فعال شد. اجرای ربات به‌زودی انجام می‌شود.")
                ))
            except Exception:
                pass
            # Notify admin
            try:
                if Config.ADMIN_USER_ID:
                    from telegram import Bot as PTBBot
                    notify_bot = PTBBot(token=Config.MAIN_BOT_TOKEN)
                    await notify_bot.send_message(chat_id=int(Config.ADMIN_USER_ID), text=(
                        f"✅ پرداخت #{payment_id} تایید شد. " + ("(Deploy OK)" if deploy_ok else "(Deploy pending)")
                    ))
            except Exception:
                pass
            logger.info(f"Payment {payment_id} approved by admin {admin_id}")
            return True
        except Exception as e:
            logger.error(f"Error approving payment {payment_id}: {e}")
            return False
    
    async def reject_payment(self, payment_id: int, admin_id: int, reason: str = None) -> bool:
        """Reject a payment: mark rejected and notify user/admin."""
        try:
            payment = await db.get_payment(payment_id)
            if not payment:
                return False
            await db.update_payment_status(payment_id, Config.PAYMENT_STATUS_REJECTED, admin_id)
            # Notify user
            try:
                from telegram import Bot as PTBBot
                notify_bot = PTBBot(token=Config.MAIN_BOT_TOKEN)
                rejection_text = "❌ پرداخت شما رد شد." + (f"\nدلیل: {reason}" if reason else "")
                await notify_bot.send_message(chat_id=int(payment['user_id']), text=rejection_text)
            except Exception:
                pass
            # Notify admin
            try:
                if Config.ADMIN_USER_ID:
                    from telegram import Bot as PTBBot
                    notify_bot = PTBBot(token=Config.MAIN_BOT_TOKEN)
                    await notify_bot.send_message(chat_id=int(Config.ADMIN_USER_ID), text=f"❌ پرداخت #{payment_id} رد شد.")
            except Exception:
                pass
            logger.info(f"Payment {payment_id} rejected by admin {admin_id}")
            return True
        except Exception as e:
            logger.error(f"Error rejecting payment {payment_id}: {e}")
            return False
    
    def get_plan_details(self, plan_type: str) -> Optional[Dict[str, Any]]:
        """Get plan details by type"""
        plans = {
            "plan_1_month": {
                "name": "1 Month Plan",
                "price": Config.PRICE_1_MONTH,
                "duration": Config.PLAN_1_MONTH
            },
            "plan_2_months": {
                "name": "2 Months Plan",
                "price": Config.PRICE_2_MONTHS,
                "duration": Config.PLAN_2_MONTHS
            },
            "plan_3_months": {
                "name": "3 Months Plan",
                "price": Config.PRICE_3_MONTHS,
                "duration": Config.PLAN_3_MONTHS
            }
        }
        
        return plans.get(plan_type)

    async def get_runtime_plan_details(self, plan_type: str) -> Optional[Dict[str, Any]]:
        """Get plan details pulling latest prices from DB settings (fallback to Config)."""
        # Read settings
        p1 = await db.get_setting('PRICE_1_MONTH')
        p2 = await db.get_setting('PRICE_2_MONTHS')
        p3 = await db.get_setting('PRICE_3_MONTHS')
        try:
            price_1 = float(p1) if p1 is not None else float(Config.PRICE_1_MONTH or 0)
            price_2 = float(p2) if p2 is not None else float(Config.PRICE_2_MONTHS or 0)
            price_3 = float(p3) if p3 is not None else float(Config.PRICE_3_MONTHS or 0)
        except Exception:
            price_1 = float(Config.PRICE_1_MONTH or 0)
            price_2 = float(Config.PRICE_2_MONTHS or 0)
            price_3 = float(Config.PRICE_3_MONTHS or 0)

        plans = {
            "plan_1_month": {
                "name": "پلن ۱ ماهه",
                "price": price_1,
                "duration": Config.PLAN_1_MONTH
            },
            "plan_2_months": {
                "name": "پلن ۲ ماهه",
                "price": price_2,
                "duration": Config.PLAN_2_MONTHS
            },
            "plan_3_months": {
                "name": "پلن ۳ ماهه",
                "price": price_3,
                "duration": Config.PLAN_3_MONTHS
            }
        }
        return plans.get(plan_type)
    
    async def show_payment_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Show user's payment history"""
        # This would require implementing get_user_payments in database.py
        # For now, we'll show a placeholder
        
        text = """
💳 **تاریخچه پرداخت‌ها**

اینجا تاریخچه پرداخت‌هات میاد.

**پرداخت‌های اخیر:**
• فعلاً چیزی ثبت نشده

**وضعیت‌ها:**
• در انتظار: ۰
• تایید شده: ۰
• رد شده: ۰
        """
        
        keyboard = [
            [InlineKeyboardButton("💳 پرداخت جدید", callback_data="subscribe")],
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

# Global payment handler instance
payment_handler = PaymentHandler()