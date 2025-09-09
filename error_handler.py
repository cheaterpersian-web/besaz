import asyncio
import traceback
from typing import Any, Callable, Optional
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from logger import logger

class ErrorHandler:
    def __init__(self):
        self.logger = logger
    
    def handle_telegram_error(self, func: Callable) -> Callable:
        """Decorator to handle Telegram bot errors (works with bound methods)."""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Support both bound methods (self, update, context) and plain functions (update, context)
            try:
                if len(args) >= 3 and not isinstance(args[0], Update):
                    self_obj, update, context = args[0], args[1], args[2]
                    remaining = args[3:]
                    return await func(self_obj, update, context, *remaining, **kwargs)
                else:
                    update, context = args[0], args[1]
                    remaining = args[2:]
                    return await func(update, context, *remaining, **kwargs)
            except Exception as e:
                # Extract update/context for logging safely
                try:
                    upd = update if 'update' in locals() else (args[1] if len(args) > 1 and isinstance(args[1], Update) else None)
                    ctx = context if 'context' in locals() else (args[2] if len(args) > 2 else None)
                    await self.log_telegram_error(upd, ctx, e)
                    await self.send_error_response(upd, ctx, e)
                except Exception:
                    # As last resort, log raw exception
                    self.logger.error(f"Unhandled telegram error: {e}")
        return wrapper
    
    def handle_async_error(self, func: Callable) -> Callable:
        """Decorator to handle async function errors"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                self.log_async_error(func.__name__, e, args, kwargs)
                raise
        return wrapper
    
    def handle_sync_error(self, func: Callable) -> Callable:
        """Decorator to handle sync function errors"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.log_sync_error(func.__name__, e, args, kwargs)
                raise
        return wrapper
    
    async def log_telegram_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception):
        """Log Telegram bot error with context"""
        user_id = None
        chat_id = None
        try:
            if update and getattr(update, 'effective_user', None):
                user_id = update.effective_user.id
            if update and getattr(update, 'effective_chat', None):
                chat_id = update.effective_chat.id
        except Exception:
            pass
        user_id = user_id or "Unknown"
        chat_id = chat_id or "Unknown"
        
        error_details = {
            "user_id": user_id,
            "chat_id": chat_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc()
        }
        
        self.logger.error(f"Telegram bot error: {error}", extra=error_details)
        self.logger.audit("TELEGRAM_ERROR", user_id, f"Error in chat {chat_id}: {error}")
    
    def log_async_error(self, function_name: str, error: Exception, args: tuple, kwargs: dict):
        """Log async function error"""
        error_details = {
            "function": function_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "args": str(args),
            "kwargs": str(kwargs),
            "traceback": traceback.format_exc()
        }
        
        self.logger.error(f"Async function error in {function_name}: {error}", extra=error_details)
    
    def log_sync_error(self, function_name: str, error: Exception, args: tuple, kwargs: dict):
        """Log sync function error"""
        error_details = {
            "function": function_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "args": str(args),
            "kwargs": str(kwargs),
            "traceback": traceback.format_exc()
        }
        
        self.logger.error(f"Sync function error in {function_name}: {error}", extra=error_details)
    
    async def send_error_response(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception):
        """Send user-friendly error response"""
        try:
            # Determine error type and send appropriate response
            if isinstance(error, ValueError):
                message = "❌ Invalid input. Please check your data and try again."
            elif isinstance(error, PermissionError):
                message = "❌ Access denied. You don't have permission to perform this action."
            elif isinstance(error, ConnectionError):
                message = "❌ Connection error. Please try again later."
            elif isinstance(error, TimeoutError):
                message = "❌ Request timed out. Please try again."
            else:
                message = "❌ An unexpected error occurred. Please try again or contact support."
            
            # Send error message
            if update.callback_query:
                await update.callback_query.edit_message_text(message)
            elif update.message:
                await update.message.reply_text(message)
            
        except Exception as e:
            # If we can't send error response, log it
            self.logger.error(f"Failed to send error response: {e}")
    
    def handle_database_error(self, operation: str, error: Exception, **context):
        """Handle database-specific errors"""
        error_details = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        self.logger.error(f"Database error in {operation}: {error}", extra=error_details)
        
        # Log audit event for database errors
        self.logger.audit("DATABASE_ERROR", details=f"{operation}: {error}")
    
    def handle_bot_deployment_error(self, bot_id: int, error: Exception, **context):
        """Handle bot deployment errors"""
        error_details = {
            "bot_id": bot_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        self.logger.error(f"Bot deployment error for bot {bot_id}: {error}", extra=error_details)
        self.logger.log_bot_event(bot_id, "DEPLOYMENT_ERROR", str(error))
    
    def handle_payment_error(self, payment_id: int, error: Exception, user_id: int = None, **context):
        """Handle payment processing errors"""
        error_details = {
            "payment_id": payment_id,
            "user_id": user_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        self.logger.error(f"Payment error for payment {payment_id}: {error}", extra=error_details)
        self.logger.log_payment_event(payment_id, "PAYMENT_ERROR", user_id)
    
    def handle_monitoring_error(self, error: Exception, **context):
        """Handle monitoring system errors"""
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "traceback": traceback.format_exc()
        }
        
        self.logger.error(f"Monitoring system error: {error}", extra=error_details)
        self.logger.log_system_event("MONITORING_ERROR", str(error))
    
    async def safe_execute(self, coro, error_message: str = "Operation failed", **context):
        """Safely execute a coroutine with error handling"""
        try:
            return await coro
        except Exception as e:
            self.logger.error(f"{error_message}: {e}", extra=context)
            return None
    
    def safe_execute_sync(self, func: Callable, error_message: str = "Operation failed", **context):
        """Safely execute a sync function with error handling"""
        try:
            return func()
        except Exception as e:
            self.logger.error(f"{error_message}: {e}", extra=context)
            return None

# Global error handler instance
error_handler = ErrorHandler()

# Convenience decorators
def handle_telegram_errors(func):
    """Decorator for Telegram bot handlers"""
    return error_handler.handle_telegram_error(func)

def handle_async_errors(func):
    """Decorator for async functions"""
    return error_handler.handle_async_error(func)

def handle_sync_errors(func):
    """Decorator for sync functions"""
    return error_handler.handle_sync_error(func)