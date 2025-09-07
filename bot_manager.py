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
        """Create a basic bot template (python-telegram-bot v21)"""
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
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🤖 ربات فعاله!\nبرای دیدن دستورات /help رو بزن.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = "🤖 دستورات ربات:\n/start - شروع\n/help - همین راهنما\n/status - وضعیت ربات"
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("✅ ربات فعاله و سالم کار می‌کنه!")
    
    async def run(self):
        try:
            await self.application.run_polling()
        except Exception as e:
            logger.error(f"Error running bot: {e}")

async def main():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("Error: BOT_TOKEN environment variable not set")
        return
    
    bot = BotInstance(token)
    await bot.run()

if __name__ == '__main__':
    asyncio.run(main())
'''
        
        # Write bot.py (overwrite if exists to ensure a working entrypoint)
        with open(os.path.join(bot_dir, "bot.py"), "w") as f:
            f.write(bot_code)
        
        # Create minimal requirements.txt aligned with PTB v21
        requirements = '''python-telegram-bot==21.7
python-dotenv==1.0.1
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
            
            # Ensure repo present: if BOT_REPO_URL is set but directory is missing or not a git repo, reclone
            need_clone = False
            if not os.path.exists(bot_dir):
                need_clone = True
            else:
                git_dir = os.path.join(bot_dir, '.git')
                if Config.BOT_REPO_URL and not os.path.exists(git_dir):
                    # Existing non-git directory (likely local template). Re-clone from repo.
                    shutil.rmtree(bot_dir, ignore_errors=True)
                    need_clone = True
            if need_clone:
                if not await self.clone_bot_template(bot_id):
                    return False
            
            # Detect entrypoint. If missing, generate a minimal template.
            candidate_files = ["main.py", "bot.py", "app.py", "run.py"]
            entrypoint = None
            for fname in candidate_files:
                if os.path.exists(os.path.join(bot_dir, fname)):
                    entrypoint = fname
                    break
            if entrypoint is None:
                await self.create_bot_template(bot_dir)
                entrypoint = "bot.py"
            
            # Create .env file with bot token and optional admin/channel
            env_file = os.path.join(bot_dir, ".env")
            with open(env_file, "w") as f:
                f.write(("BOT_TOKEN={bot_token}\nADMIN_ID={admin_id}\nCHANNEL_ID={channel_id}\n").format(
                    bot_token=bot_token,
                    admin_id=str(Config.ADMIN_USER_ID or ""),
                    channel_id=str(Config.LOCKED_CHANNEL_ID or "")
                ))
            
            # Always use a per-bot virtual environment (PEP 668 safe)
            venv_dir = os.path.join(bot_dir, 'venv')
            venv_python = os.path.join(venv_dir, 'bin', 'python')
            if not os.path.exists(venv_python):
                # Create venv
                subprocess.run([self.python_path, "-m", "venv", "venv"], cwd=bot_dir, check=True)
            python_exec = venv_python

            # Ensure pip is available and up-to-date inside venv
            try:
                subprocess.run([python_exec, "-m", "ensurepip", "--upgrade"], cwd=bot_dir, check=False)
            except Exception:
                pass
            subprocess.run([python_exec, "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], cwd=bot_dir, check=True)

            # Install dependencies inside venv
            requirements_file = os.path.join(bot_dir, "requirements.txt")
            if os.path.exists(requirements_file):
                subprocess.run([python_exec, "-m", "pip", "install", "-r", requirements_file, "--no-cache-dir"], cwd=bot_dir, check=True)
            
            # Start the bot process (log to files to avoid pipe blocking)
            logs_dir = os.path.join(bot_dir, 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            stdout_path = os.path.join(logs_dir, 'stdout.log')
            stderr_path = os.path.join(logs_dir, 'stderr.log')
            stdout_file = open(stdout_path, 'ab')
            stderr_file = open(stderr_path, 'ab')

            # Pass BOT_TOKEN via environment to support repos that read env directly
            env = os.environ.copy()
            env['BOT_TOKEN'] = bot_token
            # Prefer per-bot admin/channel from DB if present
            try:
                bot_row = await db.get_bot(bot_id)
                if bot_row and bot_row.get('admin_user_id'):
                    env['ADMIN_ID'] = str(bot_row['admin_user_id'])
                else:
                    env['ADMIN_ID'] = str(Config.ADMIN_USER_ID or '')
                if bot_row and bot_row.get('locked_channel_id'):
                    env['CHANNEL_ID'] = str(bot_row['locked_channel_id'])
                else:
                    env['CHANNEL_ID'] = str(Config.LOCKED_CHANNEL_ID or '')
            except Exception:
                env['ADMIN_ID'] = str(Config.ADMIN_USER_ID or '')
                env['CHANNEL_ID'] = str(Config.LOCKED_CHANNEL_ID or '')
            env['PYTHONUNBUFFERED'] = '1'

            process = subprocess.Popen(
                [python_exec, entrypoint],
                cwd=bot_dir,
                stdout=stdout_file,
                stderr=stderr_file,
                env=env
            )
            
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
            # Try in-memory process first
            if bot_id in self.running_bots:
                process_info = self.running_bots[bot_id]
                process = process_info['process']
                # Terminate the process
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                del self.running_bots[bot_id]
                await db.update_bot_status(bot_id, Config.BOT_STATUS_INACTIVE)
                return True

            # Fallback: stop by PID stored in DB, if any
            bot_info = await db.get_bot(bot_id)
            if bot_info and bot_info.get('process_id'):
                pid = int(bot_info['process_id'])
                try:
                    p = psutil.Process(pid)
                    p.terminate()
                    try:
                        p.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        p.kill()
                        p.wait()
                    await db.update_bot_status(bot_id, Config.BOT_STATUS_INACTIVE)
                    return True
                except Exception:
                    pass
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

    async def delete_bot(self, bot_id: int) -> bool:
        """Stop a bot if running and remove its deployment directory."""
        try:
            # Stop if running
            try:
                await self.stop_bot(bot_id)
            except Exception:
                pass
            # Remove files
            bot_dir = os.path.join(self.deployment_dir, f"bot_{bot_id}")
            if os.path.exists(bot_dir):
                shutil.rmtree(bot_dir, ignore_errors=True)
            return True
        except Exception as e:
            print(f"Error deleting bot files {bot_id}: {e}")
            return False

# Global bot manager instance
bot_manager = BotManager()