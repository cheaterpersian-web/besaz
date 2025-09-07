#!/bin/bash

# Fix systemd service script for Telegram Bot Manager System

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
    print_info "🔧 Fixing systemd service for Telegram Bot Manager System"
    echo ""
    
    # Get the directory where the script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    print_info "Script directory: $SCRIPT_DIR"
    
    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        SUDO_CMD=""
        print_info "Running as root user"
    else
        SUDO_CMD="sudo"
        print_info "Running as regular user (will use sudo)"
    fi
    
    # Stop the service first
    print_info "Stopping bot-manager service..."
    $SUDO_CMD systemctl stop bot-manager 2>/dev/null || true
    
    # Check if files exist
    print_info "Checking files..."
    
    if [ ! -f "$SCRIPT_DIR/run.py" ]; then
        print_error "run.py not found in $SCRIPT_DIR"
        exit 1
    fi
    
    if [ ! -f "$SCRIPT_DIR/venv/bin/python" ]; then
        print_error "Python virtual environment not found in $SCRIPT_DIR/venv/bin/python"
        print_info "Creating virtual environment..."
        cd "$SCRIPT_DIR"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    # Check permissions
    print_info "Checking permissions..."
    chmod +x "$SCRIPT_DIR/run.py"
    chmod +x "$SCRIPT_DIR/venv/bin/python"
    
    # Test if the script can run
    print_info "Testing if the script can run..."
    cd "$SCRIPT_DIR"
    if "$SCRIPT_DIR/venv/bin/python" -c "import sys; print('Python test successful')" 2>/dev/null; then
        print_success "Python test passed"
    else
        print_error "Python test failed"
        exit 1
    fi
    
    # Test if the main script can be imported
    print_info "Testing if main script can be imported..."
    if "$SCRIPT_DIR/venv/bin/python" -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); from config import Config; print('Import test successful')" 2>/dev/null; then
        print_success "Import test passed"
    else
        print_error "Import test failed"
        print_info "Installing dependencies..."
        source "$SCRIPT_DIR/venv/bin/activate"
        pip install -r requirements.txt
    fi
    
    # Create a new systemd service file
    print_info "Creating new systemd service file..."
    
    $SUDO_CMD tee /etc/systemd/system/bot-manager.service > /dev/null << EOF
[Unit]
Description=Telegram Bot Manager System
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/run.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=$SCRIPT_DIR
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
ReadWritePaths=$SCRIPT_DIR/data $SCRIPT_DIR/logs $SCRIPT_DIR/deployed_bots

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    print_info "Reloading systemd..."
    $SUDO_CMD systemctl daemon-reload
    
    # Start the service
    print_info "Starting bot-manager service..."
    $SUDO_CMD systemctl start bot-manager
    
    # Wait a moment
    sleep 3
    
    # Check status
    print_info "Checking service status..."
    if $SUDO_CMD systemctl is-active --quiet bot-manager; then
        print_success "Service is running successfully!"
        
        # Show status
        echo ""
        print_info "Service status:"
        $SUDO_CMD systemctl status bot-manager --no-pager
        
        echo ""
        print_info "Recent logs:"
        $SUDO_CMD journalctl -u bot-manager --no-pager -n 10
        
    else
        print_error "Service failed to start"
        
        echo ""
        print_info "Service status:"
        $SUDO_CMD systemctl status bot-manager --no-pager
        
        echo ""
        print_info "Recent logs:"
        $SUDO_CMD journalctl -u bot-manager --no-pager -n 20
        
        exit 1
    fi
    
    echo ""
    print_success "Systemd service fixed successfully!"
    
    print_info "Useful commands:"
    echo "  • Check status: $SUDO_CMD systemctl status bot-manager"
    echo "  • View logs: $SUDO_CMD journalctl -u bot-manager -f"
    echo "  • Restart: $SUDO_CMD systemctl restart bot-manager"
    echo "  • Stop: $SUDO_CMD systemctl stop bot-manager"
    echo ""
    
    print_info "Your bot manager system should now be running! 🎉"
}

# Run main function
main "$@"