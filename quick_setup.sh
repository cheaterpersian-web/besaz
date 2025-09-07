#!/bin/bash

# Quick Setup Script for Telegram Bot Manager System
# This script allows you to quickly configure the system with minimal input

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_color() {
    echo -e "${1}${2}${NC}"
}

print_header() {
    echo ""
    print_color $BLUE "=========================================="
    print_color $BLUE "$1"
    print_color $BLUE "=========================================="
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
    print_header "🚀 Quick Setup - Telegram Bot Manager System"
    
    # Get the directory where the script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    print_info "Script directory: $SCRIPT_DIR"
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    print_info "This script will quickly configure your bot manager system."
    print_info "You only need to provide the essential information."
    echo ""
    
    # Check if .env already exists
    if [ -f .env ]; then
        print_warning ".env file already exists!"
        read -p "Do you want to overwrite it? (y/n): " overwrite
        if [[ ! $overwrite =~ ^[Yy]$ ]]; then
            print_info "Setup cancelled."
            exit 0
        fi
    fi
    
    # Get essential configuration
    echo ""
    print_info "Please provide the following information:"
    echo ""
    
    # Bot Token
    while true; do
        get_input "Bot Token from @BotFather" MAIN_BOT_TOKEN
        if validate_bot_token "$MAIN_BOT_TOKEN"; then
            break
        else
            print_error "Invalid bot token format. Should be like: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        fi
    done
    
    # Admin User ID
    while true; do
        get_input "Your Telegram User ID (get from @userinfobot)" ADMIN_USER_ID
        if validate_user_id "$ADMIN_USER_ID"; then
            break
        else
            print_error "Invalid user ID. Should be a number like: 123456789"
        fi
    done
    
    # Channel
    while true; do
        get_input "Channel username (e.g., @your_channel)" LOCKED_CHANNEL_ID
        if validate_channel_id "$LOCKED_CHANNEL_ID"; then
            break
        else
            print_error "Invalid channel format. Should be like: @your_channel"
        fi
    done
    
    # Payment info
    get_input "Bank card number" BANK_CARD_NUMBER "1234567890123456"
    get_input "Crypto wallet address" CRYPTO_WALLET_ADDRESS "your_crypto_wallet_address"
    
    # Prices
    get_input "1-month plan price (USD)" PRICE_1_MONTH "10.00"
    get_input "2-months plan price (USD)" PRICE_2_MONTHS "18.00"
    get_input "3-months plan price (USD)" PRICE_3_MONTHS "25.00"
    
    # Create .env file
    print_info "Creating configuration file..."
    
    cat > "$SCRIPT_DIR/.env" << EOF
# Main Bot Configuration
MAIN_BOT_TOKEN=$MAIN_BOT_TOKEN
ADMIN_USER_ID=$ADMIN_USER_ID
MAIN_BOT_ID=$ADMIN_USER_ID
LOCKED_CHANNEL_ID=$LOCKED_CHANNEL_ID

# Database Configuration
DATABASE_URL=sqlite:///bot_manager.db

# Bot Deployment Configuration
BOT_REPO_URL=https://github.com/your-username/telegram-bot-template.git
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
    
    # Test configuration
    print_info "Testing configuration..."
    
    # Test bot token
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from telegram import Bot

async def test_bot():
    try:
        bot = Bot(token='$MAIN_BOT_TOKEN')
        me = await bot.get_me()
        print(f'✅ Bot: @{me.username}')
        return True
    except Exception as e:
        print(f'❌ Bot error: {e}')
        return False

result = asyncio.run(test_bot())
sys.exit(0 if result else 1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Bot token is valid!"
    else
        print_error "Bot token test failed!"
        exit 1
    fi
    
    # Test database
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from database import db

async def test_db():
    try:
        await db.init_db()
        print('✅ Database: OK')
        return True
    except Exception as e:
        print(f'❌ Database error: {e}')
        return False

result = asyncio.run(test_db())
sys.exit(0 if result else 1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Database is ready!"
    else
        print_error "Database test failed!"
        exit 1
    fi
    
    # Add admin user
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '$SCRIPT_DIR')
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
        print('✅ Admin user added')
        return True
    except Exception as e:
        print(f'❌ Admin user error: {e}')
        return False

result = asyncio.run(add_admin())
sys.exit(0 if result else 1)
" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "Admin user added!"
    else
        print_warning "Admin user may already exist"
    fi
    
    # Create directories
    mkdir -p "$SCRIPT_DIR/data" "$SCRIPT_DIR/logs" "$SCRIPT_DIR/deployed_bots"
    chmod 755 "$SCRIPT_DIR/data" "$SCRIPT_DIR/logs" "$SCRIPT_DIR/deployed_bots"
    
    print_success "Directories created!"
    
    # Final message
    print_header "🎉 Quick Setup Complete!"
    
    print_success "Your bot manager system is configured and ready!"
    echo ""
    
    print_info "Configuration Summary:"
    echo "  • Bot: $MAIN_BOT_TOKEN"
    echo "  • Admin: $ADMIN_USER_ID"
    echo "  • Channel: $LOCKED_CHANNEL_ID"
    echo "  • Prices: $PRICE_1_MONTH, $PRICE_2_MONTHS, $PRICE_3_MONTHS"
    echo ""
    
    print_info "To start the system:"
    echo "  cd $SCRIPT_DIR"
    echo "  python3 run.py"
    echo ""
    
    print_info "To install as service:"
    echo "  cd $SCRIPT_DIR"
    echo "  ./auto_install.sh"
    echo ""
    
    print_warning "Important:"
    echo "  • Make sure your bot is added to the channel: $LOCKED_CHANNEL_ID"
    echo "  • Test with /start command"
    echo "  • Check payment information"
    echo ""
    
    print_success "Setup completed! 🚀"
}

# Run main function
main "$@"