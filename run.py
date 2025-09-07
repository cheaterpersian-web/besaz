#!/usr/bin/env python3
"""
Main entry point for the Telegram Bot Manager System
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from main_bot import MainBot
from config import Config

def setup_logging():
    """Setup logging configuration"""
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join('logs', 'bot_manager.log')),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_config():
    """Check if all required configuration is set"""
    required_configs = [
        'MAIN_BOT_TOKEN',
        'ADMIN_USER_ID',
        'MAIN_BOT_ID',
        'LOCKED_CHANNEL_ID'
    ]
    
    missing_configs = []
    for config in required_configs:
        if not getattr(Config, config, None):
            missing_configs.append(config)
    
    if missing_configs:
        print("❌ Missing required configuration:")
        for config in missing_configs:
            print(f"   - {config}")
        print("\nPlease set these in your .env file or environment variables.")
        return False
    
    return True

async def main():
    """Main function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Telegram Bot Manager System...")
    
    # Check configuration
    if not check_config():
        logger.error("Configuration check failed. Exiting.")
        sys.exit(1)
    
    try:
        # Create and run the main bot
        main_bot = MainBot()
        await main_bot.run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())