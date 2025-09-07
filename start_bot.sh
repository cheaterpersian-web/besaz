#!/bin/bash

# Quick start script for Telegram Bot Manager System

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
    print_info "🚀 Starting Telegram Bot Manager System"
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
    
    # Check if requirements are installed
    print_info "Checking dependencies..."
    if ! python -c "import telegram" 2>/dev/null; then
        print_warning "Dependencies not installed. Installing..."
        pip install -r requirements.txt
    fi
    
    # Test imports
    print_info "Testing imports..."
    if python -c "from config import Config; from database import db; from main_bot import MainBot; print('All imports successful')" 2>/dev/null; then
        print_success "All imports successful"
    else
        print_error "Import test failed"
        exit 1
    fi
    
    # Create necessary directories
    mkdir -p data logs deployed_bots
    
    # Start the bot
    print_info "Starting bot..."
    print_warning "Press Ctrl+C to stop the bot"
    echo ""
    
    # Start with warning suppression
    python -W ignore::UserWarning run.py
}

# Run main function
main "$@"