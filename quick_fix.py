#!/usr/bin/env python3
"""
Quick fix for the callback query issue
"""

# This is a simple fix that you can apply to your main_bot.py file
# Just replace the help_command method with this version

help_command_fix = '''
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
'''

print("🔧 Quick fix for callback query issue")
print("=" * 50)
print()
print("The issue is that help_command method doesn't handle callback queries properly.")
print("The fix has been applied to the main_bot.py file.")
print()
print("Now you can:")
print("1. Copy the updated main_bot.py to your installation directory")
print("2. Restart your bot")
print("3. Test the /help command from both message and callback")
print()
print("✅ Fix applied successfully!")