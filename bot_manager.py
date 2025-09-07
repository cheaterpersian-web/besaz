import asyncio
import os
import subprocess
import psutil
import shutil
from datetime import datetime
from typing import Optional, Dict, Any
import git
from config import Config
from database import db

class BotManager:
    def __init__(self):
        self.deployment_dir = Config.BOT_DEPLOYMENT_DIR
        self.repo_url = Config.BOT_REPO_URL
        # Prefer venv python if present inside deployment dir; fallback to configured path
        self.python_path = Config.BOT_PYTHON_PATH
        self.running_bots = {}  # bot_id -> process_info
        
    async def setup_deployment_directory(self):
        """Create deployment directory if it doesn't exist"""
        if not os.path.exists(self.deployment_dir):
            os.makedirs(self.deployment_dir)
    
    async def clone_bot_template(self, bot_id: int) -> bool:
        """Clone the bot template repository for a specific bot"""
        try:
            bot_dir = os.path.join(self.deployment_dir, f"bot_{bot_id}")
            
            # Remove existing directory if it exists
            if os.path.exists(bot_dir):
                shutil.rmtree(bot_dir)
            
            # Clone the repository; if fails, fall back to local template
            try:
                git.Repo.clone_from(self.repo_url, bot_dir)
            except Exception:
                # Fallback: create minimal template locally
                await self.create_bot_template(bot_dir)
            
            return True
        except Exception as e:
            print(f"Error cloning bot template: {e}")
            return False
    
    async def create_bot_template(self, bot_dir: str):
        """Create a basic bot template"""
        bot_code = '''import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BotInstance:
    def __init__(self, token: str):
        self.token = token
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup command handlers"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "🤖 ربات فعاله!\\nبرای دیدن دستورات /help رو بزن."
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🤖 دستورات ربات:
/start - شروع
/help - همین راهنما
/status - وضعیت ربات
        """
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        await update.message.reply_text("✅ ربات فعاله و سالم کار می‌کنه!")
    
    async def run(self):
        """Run the bot"""
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            # Keep the bot running
            await asyncio.Event().wait()
        except Exception as e:
            logger.error(f"Error running bot: {e}")
        finally:
            await self.application.stop()

async def main():
    """Main function"""
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("Error: BOT_TOKEN environment variable not set")
        return
    
    bot = BotInstance(token)
    await bot.run()

if __name__ == '__main__':
    asyncio.run(main())
'''
        
        # Write bot.py
        with open(os.path.join(bot_dir, "bot.py"), "w") as f:
            f.write(bot_code)
        
        # Create requirements.txt
        requirements = '''python-telegram-bot==20.7
python-dotenv==1.0.0
'''
        with open(os.path.join(bot_dir, "requirements.txt"), "w") as f:
            f.write(requirements)
        
        # Create .env template
        env_template = '''BOT_TOKEN=your_bot_token_here
'''
        with open(os.path.join(bot_dir, ".env.template"), "w") as f:
            f.write(env_template)
    
    async def deploy_bot(self, bot_id: int, bot_token: str) -> bool:
        """Deploy a bot with the given token"""
        try:
            bot_dir = os.path.join(self.deployment_dir, f"bot_{bot_id}")
            
            # Clone template if not exists
            if not os.path.exists(bot_dir):
                if not await self.clone_bot_template(bot_id):
                    return False
            
            # Create .env file with bot token
            env_file = os.path.join(bot_dir, ".env")
            with open(env_file, "w") as f:
                f.write(f"BOT_TOKEN={bot_token}\\n")
            
            # Determine python path: use bot-specific venv if exists
            venv_python = os.path.join(bot_dir, 'venv', 'bin', 'python')
            python_exec = venv_python if os.path.exists(venv_python) else self.python_path

            # Install dependencies
            requirements_file = os.path.join(bot_dir, "requirements.txt")
            if os.path.exists(requirements_file):
                subprocess.run([
                    python_exec, "-m", "pip", "install", "-r", requirements_file
                ], cwd=bot_dir, check=True)
            
            # Start the bot process
            process = subprocess.Popen([
                python_exec, "bot.py"
            ], cwd=bot_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Store process info
            self.running_bots[bot_id] = {
                'process': process,
                'started_at': datetime.now(),
                'bot_dir': bot_dir
            }
            
            # Update database
            await db.update_bot_status(bot_id, Config.BOT_STATUS_ACTIVE, process.pid)
            
            return True
        except Exception as e:
            print(f"Error deploying bot {bot_id}: {e}")
            return False
    
    async def stop_bot(self, bot_id: int) -> bool:
        """Stop a running bot"""
        try:
            if bot_id in self.running_bots:
                process_info = self.running_bots[bot_id]
                process = process_info['process']
                
                # Terminate the process
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop gracefully
                    process.kill()
                    process.wait()
                
                # Remove from running bots
                del self.running_bots[bot_id]
                
                # Update database
                await db.update_bot_status(bot_id, Config.BOT_STATUS_INACTIVE)
                
                return True
            return False
        except Exception as e:
            print(f"Error stopping bot {bot_id}: {e}")
            return False
    
    async def restart_bot(self, bot_id: int) -> bool:
        """Restart a bot"""
        bot_info = await db.get_bot(bot_id)
        if not bot_info:
            return False
        
        # Stop the bot first
        await self.stop_bot(bot_id)
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Start it again
        return await self.deploy_bot(bot_id, bot_info['bot_token'])
    
    async def is_bot_running(self, bot_id: int) -> bool:
        """Check if a bot is currently running"""
        if bot_id not in self.running_bots:
            return False
        
        process_info = self.running_bots[bot_id]
        process = process_info['process']
        
        # Check if process is still alive
        return process.poll() is None
    
    async def get_bot_status(self, bot_id: int) -> Dict[str, Any]:
        """Get detailed status of a bot"""
        bot_info = await db.get_bot(bot_id)
        if not bot_info:
            return {'error': 'Bot not found'}
        
        is_running = await self.is_bot_running(bot_id)
        subscription = await db.get_bot_subscription(bot_id)
        is_subscription_active = await db.is_subscription_active(bot_id)
        
        return {
            'bot_id': bot_id,
            'bot_username': bot_info['bot_username'],
            'status': bot_info['status'],
            'is_running': is_running,
            'created_at': bot_info['created_at'],
            'last_activity': bot_info['last_activity'],
            'has_subscription': subscription is not None,
            'subscription_active': is_subscription_active,
            'subscription_end_date': subscription['end_date'] if subscription else None
        }
    
    async def cleanup_expired_bots(self):
        """Stop all bots with expired subscriptions"""
        bots = await db.get_all_bots()
        
        for bot in bots:
            bot_id = bot['id']
            is_subscription_active = await db.is_subscription_active(bot_id)
            
            if not is_subscription_active and await self.is_bot_running(bot_id):
                print(f"Stopping expired bot {bot_id}")
                await self.stop_bot(bot_id)
                await db.update_bot_status(bot_id, Config.BOT_STATUS_EXPIRED)
    
    async def restart_all_bots(self):
        """Restart all bots (useful when main bot restarts)"""
        bots = await db.get_all_bots()
        
        for bot in bots:
            bot_id = bot['id']
            is_subscription_active = await db.is_subscription_active(bot_id)
            
            if is_subscription_active:
                print(f"Restarting bot {bot_id}")
                await self.deploy_bot(bot_id, bot['bot_token'])
    
    async def cleanup_dead_processes(self):
        """Clean up any dead bot processes"""
        dead_bots = []
        
        for bot_id, process_info in self.running_bots.items():
            process = process_info['process']
            if process.poll() is not None:  # Process has terminated
                dead_bots.append(bot_id)
        
        for bot_id in dead_bots:
            print(f"Cleaning up dead process for bot {bot_id}")
            del self.running_bots[bot_id]
            await db.update_bot_status(bot_id, Config.BOT_STATUS_INACTIVE)

# Global bot manager instance
bot_manager = BotManager()