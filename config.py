import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Main Bot Configuration
    MAIN_BOT_TOKEN = os.getenv('MAIN_BOT_TOKEN')
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
    MAIN_BOT_ID = os.getenv('MAIN_BOT_ID')
    LOCKED_CHANNEL_ID = os.getenv('LOCKED_CHANNEL_ID')
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot_manager.db')
    
    # Bot Deployment Configuration
    BOT_REPO_URL = os.getenv('BOT_REPO_URL', 'https://github.com/wings-iran/WINGSBOT_FREE')
    # Default to a folder named 'deployed bot' inside the project directory (supports space as user requested)
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BOT_DEPLOYMENT_DIR = os.getenv('BOT_DEPLOYMENT_DIR', os.path.join(_BASE_DIR, 'deployed bot'))
    BOT_PYTHON_PATH = os.getenv('BOT_PYTHON_PATH', '/usr/bin/python3')
    
    # Payment Configuration
    BANK_CARD_NUMBER = os.getenv('BANK_CARD_NUMBER')
    CRYPTO_WALLET_ADDRESS = os.getenv('CRYPTO_WALLET_ADDRESS')
    
    # Subscription Plans (in days)
    PLAN_1_MONTH = int(os.getenv('PLAN_1_MONTH', 30))
    PLAN_2_MONTHS = int(os.getenv('PLAN_2_MONTHS', 60))
    PLAN_3_MONTHS = int(os.getenv('PLAN_3_MONTHS', 90))
    
    # Subscription Prices (in USD)
    PRICE_1_MONTH = float(os.getenv('PRICE_1_MONTH', 10.00))
    PRICE_2_MONTHS = float(os.getenv('PRICE_2_MONTHS', 18.00))
    PRICE_3_MONTHS = float(os.getenv('PRICE_3_MONTHS', 25.00))
    
    # Bot Status
    BOT_STATUS_ACTIVE = "active"
    BOT_STATUS_INACTIVE = "inactive"
    BOT_STATUS_EXPIRED = "expired"
    BOT_STATUS_PENDING = "pending"
    
    # Payment Status
    PAYMENT_STATUS_PENDING = "pending"
    PAYMENT_STATUS_APPROVED = "approved"
    PAYMENT_STATUS_REJECTED = "rejected"
    
    # User Roles
    USER_ROLE_ADMIN = "admin"
    USER_ROLE_USER = "user"