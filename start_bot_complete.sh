#!/bin/bash

echo "🚀 Starting Bot Manager System..."
echo "=================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Please create .env file with your configuration"
    echo "You can copy from .env.example and modify it"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
echo "📥 Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Fix admin user
echo "👤 Fixing admin user..."
python3 fix_admin_simple.py

# Start the bot
echo "🤖 Starting bot..."
echo "Press Ctrl+C to stop"
echo "=================================="

python3 -W ignore::UserWarning run.py