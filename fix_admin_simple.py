#!/usr/bin/env python3
"""
Simple admin fix script
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
    print("🔧 Attempting to fix admin user...")
    try:
        # Initialize database
        await db.init_db()
        print("✅ Database initialized")
        
        # Get admin ID from config
        admin_id = Config.ADMIN_USER_ID
        if not admin_id:
            print("❌ ADMIN_USER_ID is not set in .env file")
            print("Please set ADMIN_USER_ID in your .env file")
            sys.exit(1)
        
        print(f"📋 Admin ID from config: {admin_id}")
        
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
        
        # Verify the fix
        user = await db.get_user(admin_id)
        if user and user['role'] == 'admin':
            print(f"🎉 SUCCESS: User {admin_id} is now an admin!")
            print("You can now use /admin command")
        else:
            print(f"❌ FAILED: User {admin_id} is still not an admin")
            
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    print("🚀 Starting admin fix process...")
    asyncio.run(fix_admin_user())
    print("✅ Admin fix process completed")