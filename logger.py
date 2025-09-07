import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

class BotManagerLogger:
    def __init__(self, name: str = "bot_manager", log_dir: str = "logs"):
        self.name = name
        self.log_dir = log_dir
        self.setup_logging()
    
    def setup_logging(self):
        """Setup comprehensive logging configuration"""
        # Create logs directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for general logs
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'bot_manager.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'errors.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # Security/audit log handler
        audit_handler = logging.handlers.RotatingFileHandler(
            os.path.join(self.log_dir, 'audit.log'),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=10
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(detailed_formatter)
        
        # Create audit logger
        self.audit_logger = logging.getLogger(f"{self.name}.audit")
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.addHandler(audit_handler)
        self.audit_logger.propagate = False
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def audit(self, action: str, user_id: Optional[int] = None, details: str = "", **kwargs):
        """Log audit event"""
        timestamp = datetime.now().isoformat()
        audit_message = f"AUDIT: {action}"
        
        if user_id:
            audit_message += f" | User: {user_id}"
        
        if details:
            audit_message += f" | Details: {details}"
        
        self.audit_logger.info(audit_message, **kwargs)
    
    def log_bot_event(self, bot_id: int, event: str, details: str = "", **kwargs):
        """Log bot-specific event"""
        message = f"Bot {bot_id}: {event}"
        if details:
            message += f" - {details}"
        self.info(message, **kwargs)
    
    def log_payment_event(self, payment_id: int, event: str, user_id: int = None, **kwargs):
        """Log payment-specific event"""
        message = f"Payment {payment_id}: {event}"
        if user_id:
            message += f" | User: {user_id}"
        self.info(message, **kwargs)
    
    def log_system_event(self, event: str, details: str = "", **kwargs):
        """Log system-wide event"""
        message = f"SYSTEM: {event}"
        if details:
            message += f" - {details}"
        self.info(message, **kwargs)

# Global logger instance
logger = BotManagerLogger()