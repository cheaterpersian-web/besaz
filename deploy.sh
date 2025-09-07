#!/bin/bash

# Telegram Bot Manager System Deployment Script

set -e

echo "🚀 Deploying Telegram Bot Manager System..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and configure it first."
    exit 1
fi

# Check if required environment variables are set
source .env

required_vars=("MAIN_BOT_TOKEN" "ADMIN_USER_ID" "MAIN_BOT_ID" "LOCKED_CHANNEL_ID")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set in .env file"
        exit 1
    fi
done

echo "✅ Environment configuration check passed"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs deployed_bots

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set permissions
echo "🔐 Setting permissions..."
chmod +x run.py
chmod 755 data logs deployed_bots

# Test database connection
echo "🗄️ Testing database connection..."
python3 -c "
import asyncio
from database import db

async def test_db():
    await db.init_db()
    print('✅ Database connection successful')

asyncio.run(test_db())
"

# Test bot token
echo "🤖 Testing bot token..."
python3 -c "
import asyncio
from telegram import Bot
from config import Config

async def test_bot():
    bot = Bot(token=Config.MAIN_BOT_TOKEN)
    me = await bot.get_me()
    print(f'✅ Bot connection successful: @{me.username}')

asyncio.run(test_bot())
"

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 To start the system:"
echo "   python3 run.py"
echo ""
echo "📋 To run in background:"
echo "   nohup python3 run.py > logs/bot_manager.log 2>&1 &"
echo ""
echo "📋 To stop the system:"
echo "   pkill -f 'python3 run.py'"
echo ""
echo "📊 Monitor logs:"
echo "   tail -f logs/bot_manager.log"
echo ""
echo "🔧 Configuration: .env"
echo "📁 Data directory: data/"
echo "📁 Logs directory: logs/"
echo "📁 Deployed bots: deployed_bots/"
echo ""
echo "📚 For more information, see README.md"