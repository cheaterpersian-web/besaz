#!/bin/bash

# Telegram Bot Manager System - Root Installation Script
# This script can be run from anywhere and will install the system

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
    
    print_info "This script will install the Telegram Bot Manager System from anywhere."
    print_info "It will download the latest version and set up everything automatically."
    echo ""
    
    # Get installation directory
    get_input "Enter installation directory" INSTALL_DIR "/opt/bot-manager"
    
    # Check if directory exists
    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Directory $INSTALL_DIR already exists!"
        read -p "Do you want to overwrite it? (y/n): " overwrite
        if [[ ! $overwrite =~ ^[Yy]$ ]]; then
            print_info "Installation cancelled."
            exit 0
        fi
        rm -rf "$INSTALL_DIR"
    fi
    
    # Create installation directory
    print_info "Creating installation directory: $INSTALL_DIR"
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown $USER:$USER "$INSTALL_DIR"
    
    # Download the system
    print_info "Downloading Telegram Bot Manager System..."
    
    # Check if git is available
    if command -v git &> /dev/null; then
        print_info "Cloning from GitHub..."
        git clone https://github.com/your-repo/telegram-bot-manager.git "$INSTALL_DIR"
    else
        print_info "Git not available, downloading zip file..."
        # Download zip file (you would need to provide a zip download URL)
        print_error "Git is required for installation. Please install git first."
        exit 1
    fi
    
    # Change to installation directory
    cd "$INSTALL_DIR"
    
    print_success "System downloaded successfully!"
    
    # Get configuration
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
    
    cat > "$INSTALL_DIR/.env" << EOF
# Main Bot Configuration
MAIN_BOT_TOKEN=$MAIN_BOT_TOKEN
ADMIN_USER_ID=$ADMIN_USER_ID
MAIN_BOT_ID=$ADMIN_USER_ID
LOCKED_CHANNEL_ID=$LOCKED_CHANNEL_ID

# Database Configuration
DATABASE_URL=sqlite:///bot_manager.db

# Bot Deployment Configuration
BOT_REPO_URL=https://github.com/your-username/telegram-bot-template.git
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
    
    # Install system dependencies
    print_info "Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv git
    
    # Install Python dependencies
    print_info "Installing Python dependencies..."
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    pip install --upgrade pip
    pip install -r "$INSTALL_DIR/requirements.txt"
    
    # Create directories
    mkdir -p "$INSTALL_DIR/data" "$INSTALL_DIR/logs" "$INSTALL_DIR/deployed_bots"
    chmod 755 "$INSTALL_DIR/data" "$INSTALL_DIR/logs" "$INSTALL_DIR/deployed_bots"
    chmod +x "$INSTALL_DIR/run.py"
    
    # Test configuration
    print_info "Testing configuration..."
    
    # Test bot token
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '$INSTALL_DIR')
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
sys.path.insert(0, '$INSTALL_DIR')
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
    
    # Create systemd service
    print_info "Creating systemd service..."
    
    sudo tee /etc/systemd/system/bot-manager.service > /dev/null << EOF
[Unit]
Description=Telegram Bot Manager System
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
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
ReadWritePaths=$INSTALL_DIR/data $INSTALL_DIR/logs $INSTALL_DIR/deployed_bots

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    
    print_success "Systemd service created!"
    
    # Final message
    print_header "🎉 Installation Complete!"
    
    print_success "Telegram Bot Manager System has been installed successfully!"
    echo ""
    
    print_info "Installation Summary:"
    echo "  • Installation Directory: $INSTALL_DIR"
    echo "  • Bot Token: $MAIN_BOT_TOKEN"
    echo "  • Admin User ID: $ADMIN_USER_ID"
    echo "  • Channel: $LOCKED_CHANNEL_ID"
    echo "  • Configuration File: $INSTALL_DIR/.env"
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
    echo "  cd $INSTALL_DIR"
    echo "  source venv/bin/activate"
    echo "  python run.py"
    echo ""
    
    print_info "Configuration:"
    echo "  • Edit $INSTALL_DIR/.env to change settings"
    echo "  • Restart service after changes: sudo systemctl restart bot-manager"
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