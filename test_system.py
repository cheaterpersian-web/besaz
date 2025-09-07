#!/usr/bin/env python3
"""
Test script for Telegram Bot Manager System
This script tests all major components of the system
"""

import asyncio
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
        from bot_manager import bot_manager
        print("✅ Bot manager module imported successfully")
    except Exception as e:
        print(f"❌ Bot manager import failed: {e}")
        return False
    
    try:
        from payment_handler import payment_handler
        print("✅ Payment handler module imported successfully")
    except Exception as e:
        print(f"❌ Payment handler import failed: {e}")
        return False
    
    try:
        from monitor import monitor
        print("✅ Monitor module imported successfully")
    except Exception as e:
        print(f"❌ Monitor import failed: {e}")
        return False
    
    try:
        from error_handler import error_handler
        print("✅ Error handler module imported successfully")
    except Exception as e:
        print(f"❌ Error handler import failed: {e}")
        return False
    
    try:
        from logger import logger
        print("✅ Logger module imported successfully")
    except Exception as e:
        print(f"❌ Logger import failed: {e}")
        return False
    
    return True

async def test_database():
    """Test database functionality"""
    print("\n🗄️ Testing database...")
    
    try:
        from database import db
        
        # Test database initialization
        await db.init_db()
        print("✅ Database initialization successful")
        
        # Test adding a user
        result = await db.add_user(
            user_id=123456789,
            username="test_user",
            first_name="Test",
            last_name="User"
        )
        if result:
            print("✅ User addition successful")
        else:
            print("❌ User addition failed")
            return False
        
        # Test getting a user
        user = await db.get_user(123456789)
        if user:
            print("✅ User retrieval successful")
        else:
            print("❌ User retrieval failed")
            return False
        
        # Test adding a bot
        bot_id = await db.add_bot(
            owner_id=123456789,
            bot_token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
            bot_username="test_bot",
            bot_name="Test Bot"
        )
        if bot_id:
            print("✅ Bot addition successful")
        else:
            print("❌ Bot addition failed")
            return False
        
        # Test getting a bot
        bot = await db.get_bot(bot_id)
        if bot:
            print("✅ Bot retrieval successful")
        else:
            print("❌ Bot retrieval failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_bot_manager():
    """Test bot manager functionality"""
    print("\n🤖 Testing bot manager...")
    
    try:
        from bot_manager import bot_manager
        
        # Test setup deployment directory
        await bot_manager.setup_deployment_directory()
        print("✅ Deployment directory setup successful")
        
        # Test getting bot status
        status = await bot_manager.get_bot_status(1)
        if status:
            print("✅ Bot status retrieval successful")
        else:
            print("❌ Bot status retrieval failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Bot manager test failed: {e}")
        return False

async def test_payment_handler():
    """Test payment handler functionality"""
    print("\n💳 Testing payment handler...")
    
    try:
        from payment_handler import payment_handler
        
        # Test getting plan details
        plan = payment_handler.get_plan_details("plan_1_month")
        if plan:
            print("✅ Plan details retrieval successful")
        else:
            print("❌ Plan details retrieval failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Payment handler test failed: {e}")
        return False

async def test_monitor():
    """Test monitor functionality"""
    print("\n📊 Testing monitor...")
    
    try:
        from monitor import monitor
        
        # Test getting system stats
        stats = await monitor.get_system_stats()
        if stats:
            print("✅ System stats retrieval successful")
        else:
            print("❌ System stats retrieval failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Monitor test failed: {e}")
        return False

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

def test_logger():
    """Test logger functionality"""
    print("\n📝 Testing logger...")
    
    try:
        from logger import logger
        
        # Test logging
        logger.info("Test info message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        logger.audit("TEST_ACTION", 123456789, "Test audit event")
        
        print("✅ Logger test successful")
        return True
        
    except Exception as e:
        print(f"❌ Logger test failed: {e}")
        return False

def test_error_handler():
    """Test error handler functionality"""
    print("\n🛡️ Testing error handler...")
    
    try:
        from error_handler import error_handler
        
        # Test error handling
        @error_handler.handle_sync_errors
        def test_function():
            return "Test successful"
        
        result = test_function()
        if result == "Test successful":
            print("✅ Error handler test successful")
            return True
        else:
            print("❌ Error handler test failed")
            return False
        
    except Exception as e:
        print(f"❌ Error handler test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 Telegram Bot Manager System - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Logger", test_logger),
        ("Error Handler", test_error_handler),
        ("Database", test_database),
        ("Bot Manager", test_bot_manager),
        ("Payment Handler", test_payment_handler),
        ("Monitor", test_monitor),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
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
        return 0
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)