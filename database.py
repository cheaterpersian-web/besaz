import aiosqlite
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from config import Config

class Database:
    def __init__(self, db_path: str = "data/bot_manager.db"):
        # Resolve to absolute path under project directory to avoid CWD issues
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # If a URL-style was provided via code in future, strip sqlite scheme
        if isinstance(db_path, str) and db_path.startswith("sqlite:///"):
            db_path = db_path.replace("sqlite:///", "", 1)
        if not os.path.isabs(db_path):
            db_path = os.path.join(base_dir, db_path)
        self.db_path = db_path
    
    async def init_db(self):
        """Initialize the database with all required tables"""
        # Ensure parent directory exists (e.g., 'data/')
        try:
            parent_dir = os.path.dirname(self.db_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
        except Exception:
            pass
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Bots table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS bots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER NOT NULL,
                    bot_token TEXT UNIQUE NOT NULL,
                    bot_username TEXT,
                    bot_name TEXT,
                    admin_user_id INTEGER,
                    locked_channel_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP,
                    process_id INTEGER,
                    FOREIGN KEY (owner_id) REFERENCES users (user_id)
                )
            ''')
            # Backward-compat: add columns if table existed without new cols
            try:
                await db.execute("ALTER TABLE bots ADD COLUMN admin_user_id INTEGER")
            except Exception:
                pass
            try:
                await db.execute("ALTER TABLE bots ADD COLUMN locked_channel_id TEXT")
            except Exception:
                pass
            
            # Subscriptions table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id INTEGER NOT NULL,
                    plan_type TEXT NOT NULL,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (bot_id) REFERENCES bots (id)
                )
            ''')
            
            # Payments table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    bot_id INTEGER,
                    amount REAL NOT NULL,
                    plan_type TEXT NOT NULL,
                    payment_method TEXT NOT NULL,
                    payment_proof TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    processed_by INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (bot_id) REFERENCES bots (id),
                    FOREIGN KEY (processed_by) REFERENCES users (user_id)
                )
            ''')
            
            # Settings table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
    
    # User operations
    async def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, role: str = None) -> bool:
        """Add or update a user without overwriting existing role.
        If role is provided on first insert it will be set; on updates, role is preserved.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO users (user_id, username, first_name, last_name, role)
                    VALUES (?, ?, ?, ?, COALESCE(?, 'user'))
                    ON CONFLICT(user_id) DO UPDATE SET
                        username=excluded.username,
                        first_name=excluded.first_name,
                        last_name=excluded.last_name
                ''', (user_id, username, first_name, last_name, role))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information by user_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin. Falls back to configured ADMIN_USER_ID."""
        try:
            if Config.ADMIN_USER_ID and int(user_id) == int(Config.ADMIN_USER_ID):
                return True
        except Exception:
            pass
        user = await self.get_user(user_id)
        return bool(user and user.get('role') == Config.USER_ROLE_ADMIN)

    async def get_users_paginated(self, offset: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """Get users with pagination (ordered by created_at DESC)."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT * FROM users
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def count_users(self) -> int:
        """Count total users."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT COUNT(*) FROM users') as cursor:
                row = await cursor.fetchone()
                return int(row[0]) if row and row[0] is not None else 0

    async def count_active_users(self) -> int:
        """Count active users."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT COUNT(*) FROM users WHERE is_active = 1') as cursor:
                row = await cursor.fetchone()
                return int(row[0]) if row and row[0] is not None else 0

    async def count_admin_users(self) -> int:
        """Count admin users."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT COUNT(*) FROM users WHERE role = ?', (Config.USER_ROLE_ADMIN,)) as cursor:
                row = await cursor.fetchone()
                return int(row[0]) if row and row[0] is not None else 0

    async def set_user_role(self, user_id: int, role: str) -> bool:
        """Update user's role."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('UPDATE users SET role = ? WHERE user_id = ?', (role, user_id))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error setting user role: {e}")
            return False

    async def set_user_active(self, user_id: int, is_active: bool) -> bool:
        """Update user's active flag."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('UPDATE users SET is_active = ? WHERE user_id = ?', (1 if is_active else 0, user_id))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error setting user active flag: {e}")
            return False
    
    # Bot operations
    async def add_bot(self, owner_id: int, bot_token: str, bot_username: str = None, bot_name: str = None,
                      admin_user_id: int = None, locked_channel_id: str = None) -> int:
        """Add a new bot to the database"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO bots (owner_id, bot_token, bot_username, bot_name, admin_user_id, locked_channel_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (owner_id, bot_token, bot_username, bot_name, admin_user_id, locked_channel_id))
            await db.commit()
            return cursor.lastrowid
    
    async def get_bot(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Get bot information by bot_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM bots WHERE id = ?', (bot_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def get_bot_by_token(self, bot_token: str) -> Optional[Dict[str, Any]]:
        """Get bot information by bot token"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM bots WHERE bot_token = ?', (bot_token,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def get_user_bots(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all bots owned by a user"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM bots WHERE owner_id = ? ORDER BY created_at DESC', (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def update_bot_status(self, bot_id: int, status: str, process_id: int = None) -> bool:
        """Update bot status and process ID"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if process_id is not None:
                    await db.execute('''
                        UPDATE bots SET status = ?, process_id = ?, last_activity = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (status, process_id, bot_id))
                else:
                    await db.execute('''
                        UPDATE bots SET status = ?, last_activity = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (status, bot_id))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error updating bot status: {e}")
            return False

    async def update_bot_admin_and_channel(self, bot_id: int, admin_user_id: int = None, locked_channel_id: str = None) -> bool:
        """Update bot admin and locked channel settings"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE bots SET admin_user_id = ?, locked_channel_id = ?
                    WHERE id = ?
                ''', (admin_user_id, locked_channel_id, bot_id))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error updating bot admin/channel: {e}")
            return False
    
    async def get_all_bots(self) -> List[Dict[str, Any]]:
        """Get all bots in the system"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM bots ORDER BY created_at DESC') as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def delete_bot(self, bot_id: int, owner_id: int) -> bool:
        """Delete a bot and related data (subscriptions, payments referencing it).
        Requires owner_id match to prevent deleting others' bots.
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                # Ensure ownership
                async with db.execute('SELECT owner_id FROM bots WHERE id = ?', (bot_id,)) as cur:
                    row = await cur.fetchone()
                    if not row or int(row['owner_id']) != int(owner_id):
                        return False
                # Delete related subscriptions
                await db.execute('DELETE FROM subscriptions WHERE bot_id = ?', (bot_id,))
                # Null payments' bot_id to retain payment history
                await db.execute('UPDATE payments SET bot_id = NULL WHERE bot_id = ?', (bot_id,))
                # Delete the bot itself
                await db.execute('DELETE FROM bots WHERE id = ?', (bot_id,))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error deleting bot {bot_id}: {e}")
            return False
    
    # Subscription operations
    async def add_subscription(self, bot_id: int, plan_type: str, duration_days: int) -> int:
        """Add a new subscription for a bot"""
        start_date = datetime.now()
        end_date = start_date + timedelta(days=duration_days)
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO subscriptions (bot_id, plan_type, end_date)
                VALUES (?, ?, ?)
            ''', (bot_id, plan_type, end_date))
            await db.commit()
            return cursor.lastrowid
    
    async def get_bot_subscription(self, bot_id: int) -> Optional[Dict[str, Any]]:
        """Get active subscription for a bot"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT * FROM subscriptions 
                WHERE bot_id = ? AND is_active = 1 
                ORDER BY end_date DESC LIMIT 1
            ''', (bot_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def is_subscription_active(self, bot_id: int) -> bool:
        """Check if bot has an active subscription"""
        subscription = await self.get_bot_subscription(bot_id)
        if not subscription:
            return False
        
        end_date = datetime.fromisoformat(subscription['end_date'])
        return datetime.now() < end_date
    
    async def deactivate_subscription(self, bot_id: int) -> bool:
        """Deactivate subscription for a bot"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE subscriptions SET is_active = 0 
                    WHERE bot_id = ? AND is_active = 1
                ''', (bot_id,))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error deactivating subscription: {e}")
            return False
    
    # Payment operations
    async def add_payment(self, user_id: int, bot_id: int, amount: float, plan_type: str, 
                         payment_method: str, payment_proof: str = None) -> int:
        """Add a new payment record"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO payments (user_id, bot_id, amount, plan_type, payment_method, payment_proof)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, bot_id, amount, plan_type, payment_method, payment_proof))
            await db.commit()
            return cursor.lastrowid
    
    async def get_pending_payments(self) -> List[Dict[str, Any]]:
        """Get all pending payments"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('''
                SELECT p.*, u.username, u.first_name, b.bot_username
                FROM payments p
                JOIN users u ON p.user_id = u.user_id
                LEFT JOIN bots b ON p.bot_id = b.id
                WHERE p.status = 'pending'
                ORDER BY p.created_at DESC
            ''') as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_payment(self, payment_id: int) -> Optional[Dict[str, Any]]:
        """Get a single payment by id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute('SELECT * FROM payments WHERE id = ?', (payment_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def update_payment_status(self, payment_id: int, status: str, processed_by: int) -> bool:
        """Update payment status"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    UPDATE payments 
                    SET status = ?, processed_at = CURRENT_TIMESTAMP, processed_by = ?
                    WHERE id = ?
                ''', (status, processed_by, payment_id))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error updating payment status: {e}")
            return False
    
    # Settings operations
    async def set_setting(self, key: str, value: str) -> bool:
        """Set a configuration setting"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT OR REPLACE INTO settings (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                ''', (key, value))
                await db.commit()
                return True
        except Exception as e:
            print(f"Error setting configuration: {e}")
            return False
    
    async def get_setting(self, key: str) -> Optional[str]:
        """Get a configuration setting"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT value FROM settings WHERE key = ?', (key,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

# Global database instance
db = Database()