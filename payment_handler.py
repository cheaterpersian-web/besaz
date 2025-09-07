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
        
        # Get plan details
        plan_details = self.get_plan_details(plan_type)
        if not plan_details:
            await query.edit_message_text("❌ Invalid plan selected.")
            return
        
        # Get user's bots
        user_bots = await db.get_user_bots(user_id)
        if not user_bots:
            await query.edit_message_text(
                "❌ You don't have any bots yet.\\n"
                "Please create a bot first using the 'Create New Bot' option."
            )
            return
        
        # Show bot selection
        text = f"""
💳 **Payment for {plan_details['name']}**

💰 **Price:** ${plan_details['price']:.2f}
⏰ **Duration:** {plan_details['duration']} days
🆔 **Plan ID:** {plan_type}

**Select a bot to subscribe:**
        """
        
        keyboard = []
        for bot in user_bots:
            subscription = await db.get_bot_subscription(bot['id'])
            is_active = await db.is_subscription_active(bot['id'])
            
            if is_active:
                status = "🟢 Active"
            elif subscription:
                status = "🔴 Expired"
            else:
                status = "⚪ No subscription"
            
            keyboard.append([InlineKeyboardButton(
                f"@{bot['bot_username']} - {status}",
                callback_data=f"payment_{plan_type}_{bot['id']}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 Back to Plans", callback_data="subscribe")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def handle_payment_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     plan_type: str, bot_id: int):
        """Handle payment method selection"""
        query = update.callback_query
        user_id = query.from_user.id
        
        # Get plan details
        plan_details = self.get_plan_details(plan_type)
        if not plan_details:
            await query.edit_message_text("❌ Invalid plan selected.")
            return
        
        # Get bot info
        bot = await db.get_bot(bot_id)
        if not bot or bot['owner_id'] != user_id:
            await query.edit_message_text("❌ Bot not found or access denied.")
            return
        
        # Show payment methods
        text = f"""
💳 **Payment Details**

🤖 **Bot:** @{bot['bot_username']}
💰 **Plan:** {plan_details['name']}
💵 **Amount:** ${plan_details['price']:.2f}
⏰ **Duration:** {plan_details['duration']} days

**Choose Payment Method:**
        """
        
        keyboard = [
            [InlineKeyboardButton("🏦 Bank Transfer", callback_data=f"method_bank_{plan_type}_{bot_id}")],
            [InlineKeyboardButton("₿ Cryptocurrency", callback_data=f"method_crypto_{plan_type}_{bot_id}")],
            [InlineKeyboardButton("🔙 Back to Bot Selection", callback_data=f"plan_{plan_type}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def show_payment_instructions(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                      payment_method: str, plan_type: str, bot_id: int):
        """Show payment instructions"""
        query = update.callback_query
        user_id = query.from_user.id
        
        # Get plan details
        plan_details = self.get_plan_details(plan_type)
        if not plan_details:
            await query.edit_message_text("❌ Invalid plan selected.")
            return
        
        # Get bot info
        bot = await db.get_bot(bot_id)
        if not bot or bot['owner_id'] != user_id:
            await query.edit_message_text("❌ Bot not found or access denied.")
            return
        
        if payment_method == "bank":
            text = f"""
🏦 **Bank Transfer Payment**

🤖 **Bot:** @{bot['bot_username']}
💰 **Amount:** ${plan_details['price']:.2f}
⏰ **Duration:** {plan_details['duration']} days

**Payment Instructions:**
1. Transfer ${plan_details['price']:.2f} to the following card:
   `{Config.BANK_CARD_NUMBER}`

2. Take a screenshot of the payment confirmation

3. Send the screenshot here as proof of payment

4. Wait for admin approval (usually within 24 hours)

**Important:** Include your username (@{query.from_user.username}) in the payment description if possible.

Click "I've Made Payment" when you're ready to submit proof.
            """
        else:  # crypto
            text = f"""
₿ **Cryptocurrency Payment**

🤖 **Bot:** @{bot['bot_username']}
💰 **Amount:** ${plan_details['price']:.2f}
⏰ **Duration:** {plan_details['duration']} days

**Payment Instructions:**
1. Send ${plan_details['price']:.2f} worth of cryptocurrency to:
   `{Config.CRYPTO_WALLET_ADDRESS}`

2. Copy the transaction ID/hash

3. Send the transaction ID here as proof of payment

4. Wait for admin approval (usually within 24 hours)

**Important:** Make sure to send the exact amount in USD equivalent.

Click "I've Made Payment" when you're ready to submit proof.
            """
        
        keyboard = [
            [InlineKeyboardButton("✅ I've Made Payment", callback_data=f"submit_proof_{payment_method}_{plan_type}_{bot_id}")],
            [InlineKeyboardButton("🔙 Back to Payment Methods", callback_data=f"payment_{plan_type}_{bot_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
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
            "📸 **Submit Payment Proof**\\n\\n"
            "Please send your payment proof:\\n"
            "• Screenshot of bank transfer (for bank payments)\\n"
            "• Transaction ID/hash (for crypto payments)\\n\\n"
            "Send /cancel to cancel this operation."
        )
        
        return WAITING_FOR_PAYMENT_PROOF
    
    async def handle_payment_proof(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle payment proof submission"""
        user_id = update.effective_user.id
        
        # Get payment info from context
        payment_method = context.user_data.get('payment_method')
        plan_type = context.user_data.get('plan_type')
        bot_id = context.user_data.get('bot_id')
        
        if not all([payment_method, plan_type, bot_id]):
            await update.message.reply_text("❌ Payment session expired. Please start over.")
            return ConversationHandler.END
        
        # Get plan details
        plan_details = self.get_plan_details(plan_type)
        if not plan_details:
            await update.message.reply_text("❌ Invalid plan selected.")
            return ConversationHandler.END
        
        # Get bot info
        bot = await db.get_bot(bot_id)
        if not bot or bot['owner_id'] != user_id:
            await update.message.reply_text("❌ Bot not found or access denied.")
            return ConversationHandler.END
        
        # Handle different proof types
        proof_text = ""
        if update.message.photo:
            proof_text = f"Photo proof from user {user_id}"
        elif update.message.text:
            proof_text = update.message.text
        else:
            await update.message.reply_text("❌ Please send a photo or text as payment proof.")
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
        
        # Notify admin about new payment
        await self.notify_admin_new_payment(payment_id, user_id, bot, plan_details, payment_method)
        
        await update.message.reply_text(
            f"✅ **Payment proof submitted successfully!**\\n\\n"
            f"Payment ID: {payment_id}\\n"
            f"Amount: ${plan_details['price']:.2f}\\n"
            f"Method: {payment_method.title()}\\n\\n"
            f"Your payment is now pending admin approval.\\n"
            f"You will be notified once it's processed."
        )
        
        return ConversationHandler.END
    
    async def notify_admin_new_payment(self, payment_id: int, user_id: int, bot: Dict[str, Any], 
                                     plan_details: Dict[str, Any], payment_method: str):
        """Notify admin about new payment"""
        try:
            # In a real implementation, you would send a message to the admin here
            logger.info(f"New payment {payment_id} from user {user_id} for bot {bot['id']}")
            
            # You could use the main bot to send a message to the admin
            # await main_bot.send_admin_notification(f"New payment {payment_id} pending approval")
            
        except Exception as e:
            logger.error(f"Error notifying admin about payment {payment_id}: {e}")
    
    async def approve_payment(self, payment_id: int, admin_id: int) -> bool:
        """Approve a payment and activate subscription"""
        try:
            # Get payment info
            # This would require a new method in the database class
            # For now, we'll implement the logic
            
            # Update payment status
            await db.update_payment_status(payment_id, Config.PAYMENT_STATUS_APPROVED, admin_id)
            
            # Get payment details (this would need to be implemented in database.py)
            # payment = await db.get_payment(payment_id)
            # if not payment:
            #     return False
            
            # Add subscription
            # await db.add_subscription(payment['bot_id'], payment['plan_type'], plan_details['duration'])
            
            # Deploy bot if not running
            # await bot_manager.deploy_bot(payment['bot_id'], bot['bot_token'])
            
            logger.info(f"Payment {payment_id} approved by admin {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error approving payment {payment_id}: {e}")
            return False
    
    async def reject_payment(self, payment_id: int, admin_id: int, reason: str = None) -> bool:
        """Reject a payment"""
        try:
            await db.update_payment_status(payment_id, Config.PAYMENT_STATUS_REJECTED, admin_id)
            
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
    
    async def show_payment_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Show user's payment history"""
        # This would require implementing get_user_payments in database.py
        # For now, we'll show a placeholder
        
        text = """
💳 **Payment History**

Your payment history will be displayed here.

**Recent Payments:**
• No payments found

**Payment Status:**
• Pending: 0
• Approved: 0
• Rejected: 0
        """
        
        keyboard = [
            [InlineKeyboardButton("💳 New Payment", callback_data="subscribe")],
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

# Global payment handler instance
payment_handler = PaymentHandler()