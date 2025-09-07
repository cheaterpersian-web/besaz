#!/usr/bin/env python3
"""
Quick test script for Telegram Bot Manager System
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from config import Config
        print("✅ Config module imported successfully")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from database import db
        print("✅ Database module imported successfully")
    except Exception as e:
        print(f"❌ Database import failed: {e}")
        return False
    
    try:
        from main_bot import MainBot
        print("✅ MainBot module imported successfully")
    except Exception as e:
        print(f"❌ MainBot import failed: {e}")
        return False
    
    try:
        from payment_handler import payment_handler
        print("✅ Payment handler module imported successfully")
    except Exception as e:
        print(f"❌ Payment handler import failed: {e}")
        return False
    
    try:
        from bot_manager import bot_manager
        print("✅ Bot manager module imported successfully")
    except Exception as e:
        print(f"❌ Bot manager import failed: {e}")
        return False
    
    try:
        from monitor import monitor
        print("✅ Monitor module imported successfully")
    except Exception as e:
        print(f"❌ Monitor import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration"""
    print("\n⚙️ Testing configuration...")
    
    try:
        from config import Config
        
        # Check if required configs are set
        required_configs = [
            'MAIN_BOT_TOKEN',
            'ADMIN_USER_ID',
            'MAIN_BOT_ID',
            'LOCKED_CHANNEL_ID'
        ]
        
        missing_configs = []
        for config in required_configs:
            if not getattr(Config, config, None):
                missing_configs.append(config)
        
        if missing_configs:
            print(f"⚠️ Missing configurations: {', '.join(missing_configs)}")
            print("   Please set these in your .env file")
            return False
        else:
            print("✅ All required configurations are set")
            return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_main_bot():
    """Test MainBot class"""
    print("\n🤖 Testing MainBot class...")
    
    try:
        from main_bot import MainBot
        
        # Check if MainBot can be instantiated
        bot = MainBot()
        print("✅ MainBot instantiated successfully")
        
        # Check if required methods exist
        required_methods = [
            'start_command',
            'start_payment',
            'handle_payment_proof',
            'handle_bot_token',
            'cancel_conversation'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(bot, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing methods: {', '.join(missing_methods)}")
            return False
        else:
            print("✅ All required methods exist")
            return True
        
    except Exception as e:
        print(f"❌ MainBot test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Telegram Bot Manager System - Quick Test")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("MainBot", test_main_bot),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            
            if result:
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        print("\n🚀 To start the bot:")
        print("   ./start_bot.sh")
        print("   or")
        print("   python -W ignore::UserWarning run.py")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)