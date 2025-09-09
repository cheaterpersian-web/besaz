import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from config import Config
from database import db
from bot_manager import bot_manager

logger = logging.getLogger(__name__)

class BotMonitor:
    def __init__(self):
        self.running = False
        self.check_interval = 300  # 5 minutes
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        self.running = True
        logger.info("Bot monitoring started")
        
        while self.running:
            try:
                await self.check_all_bots()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def stop_monitoring(self):
        """Stop the monitoring loop"""
        self.running = False
        logger.info("Bot monitoring stopped")
    
    async def check_all_bots(self):
        """Check all bots and handle expired subscriptions"""
        logger.info("Checking all bots...")
        
        # Get all bots
        bots = await db.get_all_bots()
        
        for bot in bots:
            bot_id = bot['id']
            owner_id = bot['owner_id']
            
            try:
                # Check subscription status
                is_subscription_active = await db.is_subscription_active(bot_id)
                is_bot_running = await bot_manager.is_bot_running(bot_id)
                
                # Get subscription info
                subscription = await db.get_bot_subscription(bot_id)
                
                if subscription:
                    end_date = datetime.fromisoformat(subscription['end_date'])
                    days_left = (end_date - datetime.now()).days
                    
                    # If subscription is expired and bot is running, stop it
                    if not is_subscription_active and is_bot_running:
                        logger.info(f"Stopping expired bot {bot_id}")
                        await bot_manager.stop_bot(bot_id)
                        await db.update_bot_status(bot_id, Config.BOT_STATUS_EXPIRED)
                        
                        # Notify user about expiration
                        await self.notify_user_expiration(owner_id, bot)
                    
                    # If subscription is active and bot is not running, start it
                    elif is_subscription_active and not is_bot_running:
                        logger.info(f"Starting bot {bot_id} with active subscription")
                        await bot_manager.deploy_bot(bot_id, bot['bot_token'])
                    
                    # Check if subscription expires in 3 days
                    elif days_left <= 3 and days_left > 0:
                        await self.notify_user_renewal(owner_id, bot, days_left)
                
                else:
                    # No subscription, make sure bot is stopped
                    if is_bot_running:
                        logger.info(f"Stopping bot {bot_id} without subscription")
                        await bot_manager.stop_bot(bot_id)
                        await db.update_bot_status(bot_id, Config.BOT_STATUS_INACTIVE)
                
                # Clean up dead processes
                if is_bot_running and not await bot_manager.is_bot_running(bot_id):
                    logger.info(f"Cleaning up dead process for bot {bot_id}")
                    await db.update_bot_status(bot_id, Config.BOT_STATUS_INACTIVE)
                
            except Exception as e:
                logger.error(f"Error checking bot {bot_id}: {e}")
        
        # Clean up any dead processes
        await bot_manager.cleanup_dead_processes()
        
        logger.info("Bot check completed")
    
    async def notify_user_expiration(self, user_id: int, bot: Dict[str, Any]):
        """Notify user about bot expiration"""
        try:
            # Log for audit
            logger.info(f"Bot {bot['id']} (@{bot['bot_username']}) expired for user {user_id}")
            # Try to notify the user via main bot
            try:
                from telegram import Bot as PTBBot
                from config import Config as _Cfg
                main_bot = PTBBot(token=_Cfg.MAIN_BOT_TOKEN)
                safe_username = bot.get('bot_username') or '-'
                text = (
                    f"⏰ مدت زمان ربات دمو/اشتراک شما برای @{safe_username} به پایان رسید.\n\n"
                    f"برای خرید اشتراک ماهانه روی /subscribe بزنید."
                )
                await main_bot.send_message(chat_id=int(user_id), text=text)
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"Error notifying user {user_id} about expiration: {e}")
    
    async def notify_user_renewal(self, user_id: int, bot: Dict[str, Any], days_left: int):
        """Notify user about upcoming renewal"""
        try:
            logger.info(f"Bot {bot['id']} (@{bot['bot_username']}) expires in {days_left} days for user {user_id}")
            
            # In a real implementation, you would send a Telegram message here
            # await send_notification(user_id, f"Your bot @{bot['bot_username']} expires in {days_left} days. Please renew your subscription.")
            
        except Exception as e:
            logger.error(f"Error notifying user {user_id} about renewal: {e}")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            bots = await db.get_all_bots()
            pending_payments = await db.get_pending_payments()
            
            active_bots = 0
            expired_bots = 0
            inactive_bots = 0
            
            for bot in bots:
                is_active = await db.is_subscription_active(bot['id'])
                is_running = await bot_manager.is_bot_running(bot['id'])
                
                if is_active and is_running:
                    active_bots += 1
                elif not is_active:
                    expired_bots += 1
                else:
                    inactive_bots += 1
            
            return {
                'total_bots': len(bots),
                'active_bots': active_bots,
                'expired_bots': expired_bots,
                'inactive_bots': inactive_bots,
                'pending_payments': len(pending_payments),
                'running_processes': len(bot_manager.running_bots)
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
    
    async def restart_all_bots(self):
        """Restart all bots with active subscriptions"""
        try:
            logger.info("Restarting all bots...")
            await bot_manager.restart_all_bots()
            logger.info("All bots restarted successfully")
        except Exception as e:
            logger.error(f"Error restarting all bots: {e}")
    
    async def cleanup_expired_bots(self):
        """Clean up all expired bots"""
        try:
            logger.info("Cleaning up expired bots...")
            await bot_manager.cleanup_expired_bots()
            logger.info("Expired bots cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up expired bots: {e}")

# Global monitor instance
monitor = BotMonitor()