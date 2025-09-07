#!/bin/bash

# Telegram Bot Manager System - Automated Installation Script
# This script will guide you through the complete setup process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    echo -e "${1}${2}${NC}"
}

# Function to print header
print_header() {
    echo ""
    print_color $CYAN "=========================================="
    print_color $CYAN "$1"
    print_color $CYAN "=========================================="
    echo ""
}

# Function to print step
print_step() {
    echo ""
    print_color $BLUE "🔧 $1"
    echo ""
}

# Function to print success
print_success() {
    print_color $GREEN "✅ $1"
}

# Function to print error
print_error() {
    print_color $RED "❌ $1"
}

# Function to print warning
print_warning() {
    print_color $YELLOW "⚠️ $1"
}

# Function to print info
print_info() {
    print_color $PURPLE "ℹ️ $1"
}

# Function to get user input with validation
get_input() {
    local prompt="$1"
    local var_name="$2"
    local required="${3:-true}"
    local default="${4:-}"
    
    while true; do
        if [ -n "$default" ]; then
            read -p "$prompt [$default]: " input
            input=${input:-$default}
        else
            read -p "$prompt: " input
        fi
        
        if [ "$required" = "true" ] && [ -z "$input" ]; then
            print_error "This field is required. Please enter a value."
            continue
        fi
        
        eval "$var_name='$input'"
        break
    done
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

# Function to test bot token
test_bot_token() {
    local token="$1"
    print_info "Testing bot token..."
    
    # Create a simple test script
    cat > /tmp/test_bot.py << EOF
import asyncio
import sys
from telegram import Bot

async def test_bot():
    try:
        bot = Bot(token="$token")
        me = await bot.get_me()
        print(f"Bot username: @{me.username}")
        print(f"Bot name: {me.first_name}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_bot())
    sys.exit(0 if result else 1)
EOF
    
    if python3 /tmp/test_bot.py; then
        print_success "Bot token is valid!"
        rm -f /tmp/test_bot.py
        return 0
    else
        print_error "Bot token is invalid or bot is not accessible!"
        rm -f /tmp/test_bot.py
        return 1
    fi
}

# Main installation function
main() {
    print_header "🤖 Telegram Bot Manager System - Automated Installation"
    
    print_info "This script will guide you through the complete setup process."
    print_info "Make sure you have the following ready:"
    echo "  • Bot token from @BotFather"
    echo "  • Your Telegram user ID"
    echo "  • Channel username (for user verification)"
    echo "  • Payment information (bank card, crypto wallet)"
    echo ""
    
    read -p "Press Enter to continue or Ctrl+C to exit..."
    
    # Check system requirements
    print_step "Checking system requirements..."
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root for security reasons."
        print_info "Please run as a regular user with sudo privileges."
        exit 1
    fi
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+ first."
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    required_version="3.8"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        print_error "Python 3.8+ is required. Current version: $python_version"
        exit 1
    fi
    
    print_success "Python version check passed: $python_version"
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed. Please install pip3 first."
        exit 1
    fi
    
    print_success "System requirements check passed!"
    
    # Install system dependencies
    print_step "Installing system dependencies..."
    
    print_info "Installing required system packages..."
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv git curl
    
    print_success "System dependencies installed!"
    
    # Get configuration from user
    print_step "Configuration Setup"
    
    print_info "Let's configure your bot manager system..."
    echo ""
    
    # Bot Token
    while true; do
        get_input "Enter your main bot token from @BotFather" MAIN_BOT_TOKEN
        if validate_bot_token "$MAIN_BOT_TOKEN"; then
            if test_bot_token "$MAIN_BOT_TOKEN"; then
                break
            else
                print_error "Bot token test failed. Please check your token."
            fi
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
    print_step "Creating configuration file..."
    
    cat > .env << EOF
# Main Bot Configuration
MAIN_BOT_TOKEN=$MAIN_BOT_TOKEN
ADMIN_USER_ID=$ADMIN_USER_ID
MAIN_BOT_ID=$MAIN_BOT_ID
LOCKED_CHANNEL_ID=$LOCKED_CHANNEL_ID

# Database Configuration
DATABASE_URL=sqlite:///bot_manager.db

# Bot Deployment Configuration
BOT_REPO_URL=$BOT_REPO_URL
BOT_DEPLOYMENT_DIR=/opt/bot-manager/deployed_bots
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
    print_step "Installing Python dependencies..."
    
    # Create virtual environment
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    print_info "Installing Python packages..."
    pip install -r requirements.txt
    
    print_success "Python dependencies installed!"
    
    # Create necessary directories
    print_step "Creating directories..."
    
    mkdir -p data logs deployed_bots
    
    print_success "Directories created!"
    
    # Set permissions
    print_step "Setting permissions..."
    
    chmod +x run.py
    chmod 755 data logs deployed_bots
    
    print_success "Permissions set!"
    
    # Test database connection
    print_step "Testing database connection..."
    
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
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
    print_step "Testing bot connection..."
    
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
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
    print_step "Creating systemd service..."
    
    sudo tee /etc/systemd/system/bot-manager.service > /dev/null << EOF
[Unit]
Description=Telegram Bot Manager System
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python $(pwd)/run.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=$(pwd)
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
ReadWritePaths=$(pwd)/data $(pwd)/logs $(pwd)/deployed_bots

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    
    print_success "Systemd service created!"
    
    # Final setup
    print_step "Final setup..."
    
    # Add admin user to database
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
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
    echo "  • Installation Directory: $(pwd)"
    echo "  • Configuration File: $(pwd)/.env"
    echo ""
    
    print_info "Next Steps:"
    echo "  1. Start the system:"
    echo "     sudo systemctl start bot-manager"
    echo ""
    echo "  2. Enable auto-start:"
    echo "     sudo systemctl enable bot-manager"
    echo ""
    echo "  3. Check status:"
    echo "     sudo systemctl status bot-manager"
    echo ""
    echo "  4. View logs:"
    echo "     sudo journalctl -u bot-manager -f"
    echo ""
    echo "  5. Test your bot:"
    echo "     Send /start to your bot on Telegram"
    echo ""
    
    print_info "Manual Start (if needed):"
    echo "  source venv/bin/activate"
    echo "  python run.py"
    echo ""
    
    print_info "Configuration:"
    echo "  • Edit $(pwd)/.env to change settings"
    echo "  • Restart service after changes: sudo systemctl restart bot-manager"
    echo ""
    
    print_info "Support:"
    echo "  • Check logs: sudo journalctl -u bot-manager"
    echo "  • Stop service: sudo systemctl stop bot-manager"
    echo "  • Restart service: sudo systemctl restart bot-manager"
    echo ""
    
    print_warning "Important Notes:"
    echo "  • Make sure your bot is added to the channel: $LOCKED_CHANNEL_ID"
    echo "  • Test the bot with /start command"
    echo "  • Check that users can join the channel"
    echo "  • Verify payment information is correct"
    echo ""
    
    print_success "Your Telegram Bot Manager System is ready to use! 🚀"
    
    # Ask if user wants to start the service
    echo ""
    read -p "Do you want to start the service now? (y/n): " start_service
    
    if [[ $start_service =~ ^[Yy]$ ]]; then
        print_step "Starting service..."
        sudo systemctl start bot-manager
        sudo systemctl enable bot-manager
        
        sleep 3
        
        if sudo systemctl is-active --quiet bot-manager; then
            print_success "Service started successfully!"
            print_info "You can now test your bot by sending /start to it on Telegram"
        else
            print_error "Service failed to start. Check logs with: sudo journalctl -u bot-manager"
        fi
    fi
    
    echo ""
    print_success "Installation completed! Enjoy your new bot manager system! 🎉"
}

# Run main function
main "$@"