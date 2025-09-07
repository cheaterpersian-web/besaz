#!/bin/bash

# One-liner installation script for Telegram Bot Manager System
# This script can be run with a single command from anywhere

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

print_info() {
    print_color $BLUE "ℹ️ $1"
}

# Main function
main() {
    print_info "🚀 Telegram Bot Manager System - One-Liner Installation"
    echo ""
    
    # Get installation directory
    INSTALL_DIR="/opt/bot-manager"
    
    print_info "Installing to: $INSTALL_DIR"
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_error "This script should not be run as root for security reasons."
        print_info "Please run as a regular user with sudo privileges."
        exit 1
    fi
    
    # Install system dependencies
    print_info "Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv git
    
    # Create installation directory
    if [ -d "$INSTALL_DIR" ]; then
        print_info "Removing existing installation..."
        sudo rm -rf "$INSTALL_DIR"
    fi
    
    sudo mkdir -p "$INSTALL_DIR"
    sudo chown $USER:$USER "$INSTALL_DIR"
    
    # Download the system
    print_info "Downloading Telegram Bot Manager System..."
    git clone https://github.com/your-repo/telegram-bot-manager.git "$INSTALL_DIR"
    
    # Change to installation directory
    cd "$INSTALL_DIR"
    
    # Make scripts executable
    chmod +x *.sh
    
    # Run the automated installer
    print_info "Running automated installer..."
    ./auto_install.sh
    
    print_success "Installation completed!"
    print_info "Your bot manager system is ready to use!"
}

# Run main function
main "$@"