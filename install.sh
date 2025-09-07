#!/bin/bash

# Telegram Bot Manager System Installation Script

set -e

echo "🤖 Installing Telegram Bot Manager System..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root for security reasons."
   echo "Please run as a regular user with sudo privileges."
   exit 1
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git

# Create application directory
APP_DIR="/opt/bot-manager"
echo "📁 Creating application directory: $APP_DIR"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files
echo "📋 Copying application files..."
cp -r . $APP_DIR/
cd $APP_DIR

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data logs deployed_bots

# Set permissions
echo "🔐 Setting permissions..."
chmod +x run.py
chmod 755 data logs deployed_bots

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo cp systemd/bot-manager.service /etc/systemd/system/
sudo systemctl daemon-reload

# Create user for the service
echo "👤 Creating service user..."
sudo useradd -r -s /bin/false -d $APP_DIR botmanager 2>/dev/null || true
sudo chown -R botmanager:botmanager $APP_DIR

# Setup environment file
echo "🔧 Setting up environment configuration..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "📝 Please edit $APP_DIR/.env with your configuration:"
    echo "   - MAIN_BOT_TOKEN"
    echo "   - ADMIN_USER_ID"
    echo "   - MAIN_BOT_ID"
    echo "   - LOCKED_CHANNEL_ID"
    echo "   - Payment information"
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit $APP_DIR/.env with your configuration"
echo "2. Start the service: sudo systemctl start bot-manager"
echo "3. Enable auto-start: sudo systemctl enable bot-manager"
echo "4. Check status: sudo systemctl status bot-manager"
echo "5. View logs: sudo journalctl -u bot-manager -f"
echo ""
echo "🔧 Configuration file: $APP_DIR/.env"
echo "📊 Logs: sudo journalctl -u bot-manager"
echo "🛑 Stop service: sudo systemctl stop bot-manager"
echo "🔄 Restart service: sudo systemctl restart bot-manager"
echo ""
echo "📚 For more information, see README.md"