#!/bin/bash

# Diagnostic script for Telegram Bot Manager System

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
    print_info "🔍 Diagnosing Telegram Bot Manager System"
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
    
    echo ""
    print_info "=== SYSTEM CHECKS ==="
    
    # Check Python
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version 2>&1)
        print_success "Python found: $python_version"
    else
        print_error "Python3 not found"
    fi
    
    # Check pip
    if command -v pip3 &> /dev/null; then
        print_success "pip3 found"
    else
        print_warning "pip3 not found"
    fi
    
    echo ""
    print_info "=== FILE CHECKS ==="
    
    # Check main files
    if [ -f "$SCRIPT_DIR/run.py" ]; then
        print_success "run.py found"
        if [ -x "$SCRIPT_DIR/run.py" ]; then
            print_success "run.py is executable"
        else
            print_warning "run.py is not executable"
        fi
    else
        print_error "run.py not found"
    fi
    
    if [ -f "$SCRIPT_DIR/config.py" ]; then
        print_success "config.py found"
    else
        print_error "config.py not found"
    fi
    
    if [ -f "$SCRIPT_DIR/.env" ]; then
        print_success ".env file found"
    else
        print_error ".env file not found"
    fi
    
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        print_success "requirements.txt found"
    else
        print_error "requirements.txt not found"
    fi
    
    echo ""
    print_info "=== VIRTUAL ENVIRONMENT CHECKS ==="
    
    if [ -d "$SCRIPT_DIR/venv" ]; then
        print_success "Virtual environment directory found"
        
        if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
            print_success "Virtual environment Python found"
            if [ -x "$SCRIPT_DIR/venv/bin/python" ]; then
                print_success "Virtual environment Python is executable"
            else
                print_warning "Virtual environment Python is not executable"
            fi
        else
            print_error "Virtual environment Python not found"
        fi
        
        if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
            print_success "Virtual environment activate script found"
        else
            print_error "Virtual environment activate script not found"
        fi
    else
        print_error "Virtual environment directory not found"
    fi
    
    echo ""
    print_info "=== PYTHON DEPENDENCIES CHECK ==="
    
    if [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
        print_info "Testing Python imports..."
        
        # Test basic imports
        if "$SCRIPT_DIR/venv/bin/python" -c "import sys; print('Python test: OK')" 2>/dev/null; then
            print_success "Basic Python test passed"
        else
            print_error "Basic Python test failed"
        fi
        
        # Test config import
        if "$SCRIPT_DIR/venv/bin/python" -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); from config import Config; print('Config import: OK')" 2>/dev/null; then
            print_success "Config import test passed"
        else
            print_error "Config import test failed"
        fi
        
        # Test telegram import
        if "$SCRIPT_DIR/venv/bin/python" -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); from telegram import Bot; print('Telegram import: OK')" 2>/dev/null; then
            print_success "Telegram import test passed"
        else
            print_error "Telegram import test failed"
        fi
        
        # Test database import
        if "$SCRIPT_DIR/venv/bin/python" -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); from database import db; print('Database import: OK')" 2>/dev/null; then
            print_success "Database import test passed"
        else
            print_error "Database import test failed"
        fi
    else
        print_error "Cannot test Python dependencies - virtual environment Python not found"
    fi
    
    echo ""
    print_info "=== SYSTEMD SERVICE CHECK ==="
    
    if [ -f "/etc/systemd/system/bot-manager.service" ]; then
        print_success "Systemd service file found"
        
        # Check service status
        if $SUDO_CMD systemctl is-active --quiet bot-manager; then
            print_success "Service is active"
        else
            print_warning "Service is not active"
        fi
        
        if $SUDO_CMD systemctl is-enabled --quiet bot-manager; then
            print_success "Service is enabled"
        else
            print_warning "Service is not enabled"
        fi
        
        # Show service status
        echo ""
        print_info "Service status:"
        $SUDO_CMD systemctl status bot-manager --no-pager || true
        
    else
        print_error "Systemd service file not found"
    fi
    
    echo ""
    print_info "=== RECENT LOGS ==="
    
    print_info "Recent systemd logs:"
    $SUDO_CMD journalctl -u bot-manager --no-pager -n 10 || true
    
    echo ""
    print_info "=== DIRECTORY PERMISSIONS ==="
    
    print_info "Directory permissions:"
    ls -la "$SCRIPT_DIR" | head -10
    
    echo ""
    print_info "=== ENVIRONMENT VARIABLES ==="
    
    if [ -f "$SCRIPT_DIR/.env" ]; then
        print_info "Environment file contents:"
        grep -E "^(MAIN_BOT_TOKEN|ADMIN_USER_ID|LOCKED_CHANNEL_ID)" "$SCRIPT_DIR/.env" || true
    fi
    
    echo ""
    print_info "=== RECOMMENDATIONS ==="
    
    # Check for common issues and provide recommendations
    if [ ! -f "$SCRIPT_DIR/venv/bin/python" ]; then
        print_warning "Virtual environment Python not found. Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    fi
    
    if [ ! -x "$SCRIPT_DIR/run.py" ]; then
        print_warning "run.py is not executable. Run: chmod +x run.py"
    fi
    
    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        print_warning ".env file not found. Create it with your configuration."
    fi
    
    if ! $SUDO_CMD systemctl is-active --quiet bot-manager; then
        print_warning "Service is not running. Try: $SUDO_CMD systemctl start bot-manager"
    fi
    
    echo ""
    print_info "=== DIAGNOSIS COMPLETE ==="
    
    print_info "If you found issues, you can:"
    echo "  1. Run the fix script: ./fix_systemd.sh"
    echo "  2. Reinstall dependencies: source venv/bin/activate && pip install -r requirements.txt"
    echo "  3. Check logs: $SUDO_CMD journalctl -u bot-manager -f"
    echo "  4. Restart service: $SUDO_CMD systemctl restart bot-manager"
}

# Run main function
main "$@"