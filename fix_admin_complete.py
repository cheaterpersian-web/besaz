#!/usr/bin/env python3
"""
Complete admin fix script with user ID input
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.abspath('.'))

try:
    from database import db
    from config import Config
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the correct directory with all required files.")
    sys.exit(1)

async def fix_admin_user():
    print("🔧 Complete Admin Fix Script")
    print("=" * 40)
    
    try:
        # Initialize database
        await db.init_db()
        print("✅ Database initialized")
        
        # Get admin ID from user input
        print("\n📋 Please provide your Telegram User ID:")
        print("You can get it from @userinfobot")
        
        while True:
            try:
                admin_id = input("Enter your User ID: ").strip()
                if admin_id.isdigit():
                    admin_id = int(admin_id)
                    break
                else:
                    print("❌ Please enter a valid numeric User ID")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled")
                sys.exit(1)
        
        print(f"📋 Admin ID: {admin_id}")
        
        # Check if user exists
        user = await db.get_user(admin_id)
        if user:
            print(f"👤 User {admin_id} found in database")
            if user['role'] != 'admin':
                await db.update_user_role(admin_id, 'admin')
                print(f"✅ User {admin_id} role updated to admin")
            else:
                print(f"✅ User {admin_id} is already an admin")
        else:
            print(f"👤 User {admin_id} not found in database, adding...")
            await db.add_user(
                user_id=admin_id,
                username='admin_user',
                first_name='Admin',
                role='admin'
            )
            print(f"✅ Admin user {admin_id} added to database")
        
        # Update .env file
        env_file = '.env'
        if os.path.exists(env_file):
            print(f"\n📝 Updating {env_file} file...")
            with open(env_file, 'r') as f:
                content = f.read()
            
            # Update ADMIN_USER_ID
            lines = content.split('\n')
            updated_lines = []
            for line in lines:
                if line.startswith('ADMIN_USER_ID='):
                    updated_lines.append(f'ADMIN_USER_ID={admin_id}')
                else:
                    updated_lines.append(line)
            
            with open(env_file, 'w') as f:
                f.write('\n'.join(updated_lines))
            
            print(f"✅ {env_file} updated with ADMIN_USER_ID={admin_id}")
        else:
            print(f"⚠️ {env_file} file not found, creating...")
            with open(env_file, 'w') as f:
                f.write(f"""# Main Bot Configuration
MAIN_BOT_TOKEN=your_main_bot_token_here
ADMIN_USER_ID={admin_id}
MAIN_BOT_ID=your_main_bot_id_here
LOCKED_CHANNEL_ID=@your_channel_username

# Database Configuration
DATABASE_URL=sqlite:///bot_manager.db

# Bot Deployment Configuration
BOT_REPO_URL=https://github.com/your-username/telegram-bot-template.git
BOT_DEPLOYMENT_DIR=/workspace/deployed_bots
BOT_PYTHON_PATH=/usr/bin/python3

# Payment Configuration
BANK_CARD_NUMBER=1234567890123456
CRYPTO_WALLET_ADDRESS=your_crypto_wallet_address

# Subscription Plans (in days)
PLAN_1_MONTH=30
PLAN_2_MONTHS=60
PLAN_3_MONTHS=90

# Subscription Prices (in USD)
PRICE_1_MONTH=10.00
PRICE_2_MONTHS=18.00
PRICE_3_MONTHS=25.00
""")
            print(f"✅ {env_file} created with ADMIN_USER_ID={admin_id}")
        
        # Verify the fix
        user = await db.get_user(admin_id)
        if user and user['role'] == 'admin':
            print(f"\n🎉 SUCCESS: User {admin_id} is now an admin!")
            print("You can now use /admin command")
            print("\n📋 Next steps:")
            print("1. Update MAIN_BOT_TOKEN in .env file")
            print("2. Update other configuration values in .env file")
            print("3. Start the bot with: ./start_bot_complete.sh")
        else:
            print(f"❌ FAILED: User {admin_id} is still not an admin")
            
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    print("🚀 Starting complete admin fix process...")
    asyncio.run(fix_admin_user())
    print("✅ Admin fix process completed")