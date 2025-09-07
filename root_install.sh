#!/bin/bash

# Telegram Bot Manager System - Root Installation Script
# This script is specifically designed to run as root

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_color() {
    echo -e "${1}${2}${NC}"
}

print_header() {
    echo ""
    print_color $CYAN "=========================================="
    print_color $CYAN "$1"
    print_color $CYAN "=========================================="
    echo ""
}

print_success() {
    print_color $GREEN "✅ $1"
}

print_error() {
    print_color $RED "❌ $1"
}

print_warning() {
    print_color $YELLOW "⚠️ $1"
}

print_info() {
    print_color $BLUE "ℹ️ $1"
}

# Function to get user input
get_input() {
    local prompt="$1"
    local var_name="$2"
    local default="${3:-}"
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " input
        input=${input:-$default}
    else
        read -p "$prompt: " input
    fi
    
    eval "$var_name='$input'"
}

# Function to validate bot token
validate_bot_token() {
    local token="$1"
    if [[ ! "$token" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
        return 1
    fi
    return 0
}

# Function to validate user ID
validate_user_id() {
    local user_id="$1"
    if [[ ! "$user_id" =~ ^[0-9]+$ ]]; then
        return 1
    fi
    return 0
}

# Function to validate channel ID
validate_channel_id() {
    local channel_id="$1"
    if [[ ! "$channel_id" =~ ^@[A-Za-z0-9_]+$ ]] && [[ ! "$channel_id" =~ ^-[0-9]+$ ]]; then
        return 1
    fi
    return 0
}

# Main function
main() {
    print_header "🚀 Telegram Bot Manager System - Root Installation"
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root."
        print_info "Please run: sudo $0"
        exit 1
    fi
    
    print_info "Running as root user - this is safe for this installation."
    echo ""
    
    # Get the directory where the script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    print_info "Script directory: $SCRIPT_DIR"
    INSTALL_DIR="/opt/bot-manager"
    print_info "Install directory: $INSTALL_DIR"
    
    # Prepare install directory and copy files
    mkdir -p "$INSTALL_DIR"
    if command -v rsync >/dev/null 2>&1; then
        rsync -a --delete --exclude '.git' --exclude 'venv' --exclude '__pycache__' "$SCRIPT_DIR/" "$INSTALL_DIR/"
    else
        cp -a "$SCRIPT_DIR/." "$INSTALL_DIR/"
    fi
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    print_info "This script will install the Telegram Bot Manager System."
    print_info "Make sure you have the following ready:"
    echo "  • Bot token from @BotFather"
    echo "  • Your Telegram user ID"
    echo "  • Channel username (for user verification)"
    echo "  • Payment information (bank card, crypto wallet)"
    echo ""
    
    read -p "Press Enter to continue or Ctrl+C to exit..."
    
    # Check system requirements
    print_info "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Installing now..."
        apt-get update
        apt-get install -y python3 python3-pip python3-venv
    fi
    
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    required_version="3.8"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        print_error "Python 3.8+ is required. Current version: $python_version"
        exit 1
    fi
    
    print_success "Python version check passed: $python_version"
    
    # Install system dependencies
    print_info "Installing system dependencies..."
    apt-get update
    apt-get install -y python3-pip python3-venv git curl
    
    print_success "System dependencies installed!"
    
    # Get configuration from user
    print_info "Configuration Setup"
    print_info "Let's configure your bot manager system..."
    echo ""
    
    # Bot Token
    while true; do
        get_input "Enter your main bot token from @BotFather" MAIN_BOT_TOKEN
        if validate_bot_token "$MAIN_BOT_TOKEN"; then
            break
        else
            print_error "Invalid bot token format. Should be like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        fi
    done
    
    # Admin User ID
    while true; do
        get_input "Enter your Telegram user ID (get it from @userinfobot)" ADMIN_USER_ID
        if validate_user_id "$ADMIN_USER_ID"; then
            break
        else
            print_error "Invalid user ID. Should be a number like: 123456789"
        fi
    done
    
    # Main Bot ID
    get_input "Enter your main bot ID (same as user ID for simplicity)" MAIN_BOT_ID "$ADMIN_USER_ID"
    
    # Locked Channel
    while true; do
        get_input "Enter channel username for user verification (e.g., @your_channel)" LOCKED_CHANNEL_ID
        if validate_channel_id "$LOCKED_CHANNEL_ID"; then
            break
        else
            print_error "Invalid channel format. Should be like: @your_channel or -100123456789"
        fi
    done
    
    # Bot Repository
    get_input "Enter GitHub repository URL for bot template" BOT_REPO_URL "https://github.com/your-username/telegram-bot-template.git"
    
    # Payment Information
    print_info "Now let's set up payment information..."
    echo ""
    
    get_input "Enter bank card number for payments" BANK_CARD_NUMBER
    get_input "Enter cryptocurrency wallet address" CRYPTO_WALLET_ADDRESS
    
    # Subscription Plans
    print_info "Setting up subscription plans..."
    echo ""
    
    get_input "Enter 1-month plan price (USD)" PRICE_1_MONTH "10.00"
    get_input "Enter 2-months plan price (USD)" PRICE_2_MONTHS "18.00"
    get_input "Enter 3-months plan price (USD)" PRICE_3_MONTHS "25.00"
    
    # Create .env file
    print_info "Creating configuration file..."
    
    cat > "$INSTALL_DIR/.env" << EOF
# Main Bot Configuration
MAIN_BOT_TOKEN=$MAIN_BOT_TOKEN
ADMIN_USER_ID=$ADMIN_USER_ID
MAIN_BOT_ID=$MAIN_BOT_ID
LOCKED_CHANNEL_ID=$LOCKED_CHANNEL_ID

# Database Configuration
DATABASE_URL=sqlite:///bot_manager.db

# Bot Deployment Configuration
BOT_REPO_URL=$BOT_REPO_URL
BOT_DEPLOYMENT_DIR=$INSTALL_DIR/deployed_bots
BOT_PYTHON_PATH=/usr/bin/python3

# Payment Configuration
BANK_CARD_NUMBER=$BANK_CARD_NUMBER
CRYPTO_WALLET_ADDRESS=$CRYPTO_WALLET_ADDRESS

# Subscription Plans (in days)
PLAN_1_MONTH=30
PLAN_2_MONTHS=60
PLAN_3_MONTHS=90

# Subscription Prices (in USD)
PRICE_1_MONTH=$PRICE_1_MONTH
PRICE_2_MONTHS=$PRICE_2_MONTHS
PRICE_3_MONTHS=$PRICE_3_MONTHS

# Bot Status
BOT_STATUS_ACTIVE=active
BOT_STATUS_INACTIVE=inactive
BOT_STATUS_EXPIRED=expired
BOT_STATUS_PENDING=pending

# Payment Status
PAYMENT_STATUS_PENDING=pending
PAYMENT_STATUS_APPROVED=approved
PAYMENT_STATUS_REJECTED=rejected

# User Roles
USER_ROLE_ADMIN=admin
USER_ROLE_USER=user
EOF
    
    print_success "Configuration file created!"
    
    # Install Python dependencies
    print_info "Installing Python dependencies..."
    
    # Create virtual environment
    print_info "Creating Python virtual environment..."
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install requirements
    print_info "Installing Python packages..."
    pip install -r "$INSTALL_DIR/requirements.txt"
    
    print_success "Python dependencies installed!"
    
    # Create necessary directories
    print_info "Creating directories..."
    
    mkdir -p "$INSTALL_DIR/data" "$INSTALL_DIR/logs" "$INSTALL_DIR/deployed_bots"
    
    print_success "Directories created!"
    
    # Set permissions
    print_info "Setting permissions..."
    
    chmod +x "$INSTALL_DIR/run.py"
    chmod 755 "$INSTALL_DIR/data" "$INSTALL_DIR/logs" "$INSTALL_DIR/deployed_bots"
    
    print_success "Permissions set!"
    
    # Test database connection
    print_info "Testing database connection..."
    
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '$INSTALL_DIR')
from database import db

async def test_db():
    try:
        await db.init_db()
        print('✅ Database connection successful')
        return True
    except Exception as e:
        print(f'❌ Database error: {e}')
        return False

result = asyncio.run(test_db())
sys.exit(0 if result else 1)
"
    
    if [ $? -eq 0 ]; then
        print_success "Database test passed!"
    else
        print_error "Database test failed!"
        exit 1
    fi
    
    # Test bot connection
    print_info "Testing bot connection..."
    
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '$INSTALL_DIR')
from telegram import Bot
from config import Config

async def test_bot():
    try:
        bot = Bot(token=Config.MAIN_BOT_TOKEN)
        me = await bot.get_me()
        print(f'✅ Bot connection successful: @{me.username}')
        return True
    except Exception as e:
        print(f'❌ Bot connection error: {e}')
        return False

result = asyncio.run(test_bot())
sys.exit(0 if result else 1)
"
    
    if [ $? -eq 0 ]; then
        print_success "Bot connection test passed!"
    else
        print_error "Bot connection test failed!"
        exit 1
    fi
    
    # Create systemd service
    print_info "Creating systemd service..."
    
    tee /etc/systemd/system/bot-manager.service > /dev/null << EOF
[Unit]
Description=Telegram Bot Manager System
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/run.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=$INSTALL_DIR
Environment=PYTHONUNBUFFERED=1

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=bot-manager

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR $INSTALL_DIR/data $INSTALL_DIR/logs $INSTALL_DIR/deployed_bots

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    
    print_success "Systemd service created!"
    
    # Final setup
    print_info "Final setup..."
    
    # Add admin user to database
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '$INSTALL_DIR')
from database import db

async def add_admin():
    try:
        await db.init_db()
        await db.add_user(
            user_id=$ADMIN_USER_ID,
            username='admin',
            first_name='Admin',
            role='admin'
        )
        print('✅ Admin user added to database')
        return True
    except Exception as e:
        print(f'❌ Error adding admin user: {e}')
        return False

result = asyncio.run(add_admin())
sys.exit(0 if result else 1)
"
    
    if [ $? -eq 0 ]; then
        print_success "Admin user added to database!"
    else
        print_warning "Could not add admin user to database (may already exist)"
    fi
    
    # Installation complete
    print_header "🎉 Installation Complete!"
    
    print_success "Telegram Bot Manager System has been installed successfully!"
    echo ""
    
    print_info "Installation Summary:"
    echo "  • Bot Token: $MAIN_BOT_TOKEN"
    echo "  • Admin User ID: $ADMIN_USER_ID"
    echo "  • Channel: $LOCKED_CHANNEL_ID"
    echo "  • Installation Directory: $INSTALL_DIR"
    echo "  • Configuration File: $INSTALL_DIR/.env"
    echo ""
    
    print_info "Next Steps:"
    echo "  1. Start the system:"
    echo "     systemctl start bot-manager"
    echo ""
    echo "  2. Enable auto-start:"
    echo "     systemctl enable bot-manager"
    echo ""
    echo "  3. Check status:"
    echo "     systemctl status bot-manager"
    echo ""
    echo "  4. View logs:"
    echo "     journalctl -u bot-manager -f"
    echo ""
    echo "  5. Test your bot:"
    echo "     Send /start to your bot on Telegram"
    echo ""
    
    print_info "Manual Start (if needed):"
    echo "  cd $INSTALL_DIR"
    echo "  source venv/bin/activate"
    echo "  python run.py"
    echo ""
    
    print_info "Configuration:"
    echo "  • Edit $INSTALL_DIR/.env to change settings"
    echo "  • Restart service after changes: systemctl restart bot-manager"
    echo ""
    
    print_info "Support:"
    echo "  • Check logs: journalctl -u bot-manager"
    echo "  • Stop service: systemctl stop bot-manager"
    echo "  • Restart service: systemctl restart bot-manager"
    echo ""
    
    print_warning "Important Notes:"
    echo "  • Make sure your bot is added to the channel: $LOCKED_CHANNEL_ID"
    echo "  • Test the bot with /start command"
    echo "  • Check that users can join the channel"
    echo "  • Verify payment information is correct"
    echo ""
    
    # Ask if user wants to start the service
    echo ""
    read -p "Do you want to start the service now? (y/n): " start_service
    
    if [[ $start_service =~ ^[Yy]$ ]]; then
        print_info "Starting service..."
        systemctl start bot-manager
        systemctl enable bot-manager
        
        sleep 3
        
        if systemctl is-active --quiet bot-manager; then
            print_success "Service started successfully!"
            print_info "You can now test your bot by sending /start to it on Telegram"
        else
            print_error "Service failed to start. Check logs with: journalctl -u bot-manager"
        fi
    fi
    
    echo ""
    print_success "Installation completed! Enjoy your new bot manager system! 🎉"
}

# Run main function
main "$@"