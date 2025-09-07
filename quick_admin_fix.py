#!/usr/bin/env python3
"""
Quick admin fix - just add admin user to database
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
    sys.exit(1)

async def quick_fix():
    print("🔧 Quick Admin Fix")
    print("=" * 20)
    
    try:
        await db.init_db()
        print("✅ Database initialized")
        
        # Use the admin ID from config
        admin_id = Config.ADMIN_USER_ID
        print(f"📋 Using Admin ID: {admin_id}")
        
        # Add or update admin user
        user = await db.get_user(admin_id)
        if user:
            if user['role'] != 'admin':
                await db.update_user_role(admin_id, 'admin')
                print(f"✅ User {admin_id} role updated to admin")
            else:
                print(f"✅ User {admin_id} is already an admin")
        else:
            await db.add_user(
                user_id=admin_id,
                username='admin_user',
                first_name='Admin',
                role='admin'
            )
            print(f"✅ Admin user {admin_id} added to database")
        
        # Verify
        user = await db.get_user(admin_id)
        if user and user['role'] == 'admin':
            print(f"🎉 SUCCESS: User {admin_id} is now an admin!")
        else:
            print(f"❌ FAILED: User {admin_id} is still not an admin")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(quick_fix())