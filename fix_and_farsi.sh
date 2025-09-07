#!/bin/bash

# Fix admin and make bot Persian script

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

# Main function
main() {
    print_info "🔧 Fixing admin and making bot Persian"
    echo ""
    
    # Get the directory where the script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    print_info "Script directory: $SCRIPT_DIR"
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_info "Please create .env file with your configuration first."
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found!"
        print_info "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
    fi
    
    # Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Fix admin user
    print_info "Fixing admin user..."
    python3 fix_admin.py
    
    if [ $? -eq 0 ]; then
        print_success "Admin user fixed successfully!"
    else
        print_error "Failed to fix admin user"
        exit 1
    fi
    
    # Test the bot
    print_info "Testing bot..."
    python3 test_quick.py
    
    if [ $? -eq 0 ]; then
        print_success "Bot test passed!"
    else
        print_warning "Bot test failed, but continuing..."
    fi
    
    print_success "All fixes applied successfully!"
    echo ""
    
    print_info "Next steps:"
    echo "  1. Restart your bot:"
    echo "     ./start_bot.sh"
    echo ""
    echo "  2. Test admin access:"
    echo "     Send /admin to your bot"
    echo ""
    echo "  3. Test Persian interface:"
    echo "     Send /start to your bot"
    echo ""
    
    print_warning "Important:"
    echo "  • Make sure your ADMIN_USER_ID in .env is correct"
    echo "  • Make sure your bot is added to the channel"
    echo "  • Test all functionality after restart"
    echo ""
    
    print_success "Ready to start! 🚀"
}

# Run main function
main "$@"