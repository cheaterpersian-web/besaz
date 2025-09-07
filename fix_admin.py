#!/usr/bin/env python3
"""
Fix admin user script for Telegram Bot Manager System
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def fix_admin():
    """Fix admin user in database"""
    print("🔧 Fixing admin user...")
    
    try:
        from database import db
        from config import Config
        
        # Initialize database
        await db.init_db()
        print("✅ Database initialized")
        
        # Get admin user ID from config
        admin_user_id = Config.ADMIN_USER_ID
        
        if not admin_user_id:
            print("❌ ADMIN_USER_ID not set in .env file")
            return False
        
        print(f"ℹ️ Admin User ID: {admin_user_id}")
        
        # Check if user exists
        user = await db.get_user(admin_user_id)
        
        if user:
            print(f"ℹ️ User exists with role: {user['role']}")
            
            # Update user to admin if not already
            if user['role'] != 'admin':
                print("🔄 Updating user role to admin...")
                await db.add_user(
                    user_id=admin_user_id,
                    username=user.get('username', 'admin'),
                    first_name=user.get('first_name', 'Admin'),
                    last_name=user.get('last_name', 'User'),
                    role='admin'
                )
                print("✅ User role updated to admin")
            else:
                print("✅ User is already admin")
        else:
            print("➕ Adding new admin user...")
            await db.add_user(
                user_id=admin_user_id,
                username='admin',
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            print("✅ Admin user added")
        
        # Verify admin status
        is_admin = await db.is_admin(admin_user_id)
        if is_admin:
            print("✅ Admin privileges confirmed")
            return True
        else:
            print("❌ Admin privileges not confirmed")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing admin: {e}")
        return False

async def show_users():
    """Show all users in database"""
    print("\n👥 All users in database:")
    
    try:
        from database import db
        
        # Get all users (we need to implement this in database.py)
        # For now, let's just check the admin user
        from config import Config
        admin_user_id = Config.ADMIN_USER_ID
        
        if admin_user_id:
            user = await db.get_user(admin_user_id)
            if user:
                print(f"  • User ID: {user['user_id']}")
                print(f"    Username: {user['username']}")
                print(f"    Name: {user['first_name']} {user['last_name']}")
                print(f"    Role: {user['role']}")
                print(f"    Created: {user['created_at']}")
            else:
                print(f"  • User ID {admin_user_id}: Not found")
        
    except Exception as e:
        print(f"❌ Error showing users: {e}")

async def main():
    """Main function"""
    print("🔧 Telegram Bot Manager System - Admin Fix")
    print("=" * 50)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create .env file with your configuration first.")
        return 1
    
    # Fix admin user
    success = await fix_admin()
    
    if success:
        print("\n🎉 Admin user fixed successfully!")
        
        # Show users
        await show_users()
        
        print("\n📋 Next steps:")
        print("  1. Restart your bot")
        print("  2. Send /admin to your bot")
        print("  3. You should now have admin access")
        
        return 0
    else:
        print("\n❌ Failed to fix admin user")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)