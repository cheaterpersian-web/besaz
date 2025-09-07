# 🚀 Telegram Bot Manager System - Installation Options

## 📋 Available Installation Methods

### 1. 🎯 **One-Liner Installation** (Easiest)
```bash
# Run this single command from anywhere
curl -sSL https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/one_liner_install.sh | bash
```

**Features:**
- ✅ Single command installation
- ✅ Downloads latest version
- ✅ Runs automated installer
- ✅ Complete setup

### 2. 🔧 **Root Installation** (From Anywhere)
```bash
# Download and run from anywhere
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/install_from_root.sh
chmod +x install_from_root.sh
./install_from_root.sh
```

**Features:**
- ✅ Can be run from any directory
- ✅ Interactive configuration
- ✅ Custom installation directory
- ✅ Complete automated setup

### 3. 🚀 **Fully Automated Installation** (Recommended)
```bash
# Download and run the complete automated installer
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/auto_install.sh
chmod +x auto_install.sh
./auto_install.sh
```

**Features:**
- ✅ Interactive setup with validation
- ✅ Automatic system dependency installation
- ✅ Bot token testing
- ✅ Database initialization
- ✅ Systemd service creation
- ✅ Complete configuration setup
- ✅ Admin user creation
- ✅ Service startup and testing

### 4. ⚡ **Quick Setup** (For experienced users)
```bash
# Quick configuration with minimal input
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/quick_setup.sh
chmod +x quick_setup.sh
./quick_setup.sh
```

**Features:**
- ✅ Minimal configuration input
- ✅ Basic validation
- ✅ Quick deployment
- ✅ Essential testing

### 5. 🔧 **Manual Installation**
```bash
# Traditional manual installation
git clone https://github.com/your-repo/telegram-bot-manager.git
cd telegram-bot-manager
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python3 run.py
```

## 🎯 Which Method Should You Choose?

### For Beginners:
**Use: One-Liner Installation**
- Simplest method
- Just run one command
- Everything is automated

### For Experienced Users:
**Use: Fully Automated Installation**
- More control over the process
- Interactive configuration
- Better error handling

### For Quick Testing:
**Use: Quick Setup**
- Fastest setup
- Minimal input required
- Good for testing

### For Custom Installation:
**Use: Root Installation**
- Choose custom directory
- Run from anywhere
- Full control

## 📝 Required Information

Before running any installation script, prepare:

### 🤖 Bot Information
- **Bot Token**: Get from @BotFather
- **Your User ID**: Get from @userinfobot
- **Channel Username**: Channel users must join (e.g., @your_channel)

### 💳 Payment Information
- **Bank Card Number**: For receiving payments
- **Crypto Wallet Address**: For cryptocurrency payments

### 💰 Pricing (Optional - defaults provided)
- **1 Month Plan**: Default $10.00
- **2 Months Plan**: Default $18.00
- **3 Months Plan**: Default $25.00

## 🚀 Quick Start Commands

### Easiest Installation:
```bash
curl -sSL https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/one_liner_install.sh | bash
```

### From Any Directory:
```bash
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/install_from_root.sh
chmod +x install_from_root.sh
./install_from_root.sh
```

### Full Control:
```bash
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/auto_install.sh
chmod +x auto_install.sh
./auto_install.sh
```

## 🔧 Post-Installation

### Start the Service:
```bash
sudo systemctl start bot-manager
sudo systemctl enable bot-manager
```

### Check Status:
```bash
sudo systemctl status bot-manager
```

### View Logs:
```bash
sudo journalctl -u bot-manager -f
```

### Test System:
```bash
cd /opt/bot-manager
python3 test_system.py
```

## 🧪 Testing Your Installation

### Run System Tests:
```bash
# Test all system components
python3 test_system.py
```

### Manual Testing:
1. Send `/start` to your bot
2. Check if you can access admin panel with `/admin`
3. Test bot creation process
4. Verify payment system

## 🚨 Troubleshooting

### Common Issues

#### Bot Token Invalid
```bash
# Test bot token
python3 -c "
import asyncio
from telegram import Bot
from config import Config

async def test():
    bot = Bot(token=Config.MAIN_BOT_TOKEN)
    me = await bot.get_me()
    print(f'Bot: @{me.username}')

asyncio.run(test())
"
```

#### Database Errors
```bash
# Recreate database
rm bot_manager.db
python3 -c "
import asyncio
from database import db
asyncio.run(db.init_db())
"
```

#### Service Not Starting
```bash
# Check service status
sudo systemctl status bot-manager

# Check logs
sudo journalctl -u bot-manager -f

# Restart service
sudo systemctl restart bot-manager
```

## 📊 System Components

### Core Files
- `main_bot.py` - Main bot application
- `database.py` - Database operations
- `bot_manager.py` - Bot deployment and management
- `payment_handler.py` - Payment processing
- `monitor.py` - System monitoring
- `error_handler.py` - Error handling
- `logger.py` - Logging system
- `config.py` - Configuration management

### Installation Scripts
- `one_liner_install.sh` - One-command installation
- `install_from_root.sh` - Installation from anywhere
- `auto_install.sh` - Complete automated installation
- `quick_setup.sh` - Quick configuration setup
- `install.sh` - Manual installation script
- `deploy.sh` - Deployment script
- `test_system.py` - System testing script

### Configuration Files
- `.env` - Environment configuration
- `.env.example` - Configuration template
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Docker setup
- `Dockerfile` - Docker configuration

## 🎉 Success!

Once installation is complete, you can:

1. **Start accepting users** - Users can send `/start` to your bot
2. **Manage subscriptions** - Approve payments and manage bots
3. **Monitor system** - Use admin panel to monitor all activities
4. **Scale your business** - Add more bots and users as needed

## 📞 Support

### Getting Help
- Check logs for error messages
- Run system tests: `python3 test_system.py`
- Review documentation in `README.md`
- Check system status: `sudo systemctl status bot-manager`

### Useful Commands
```bash
# View real-time logs
sudo journalctl -u bot-manager -f

# Restart service
sudo systemctl restart bot-manager

# Check system status
sudo systemctl status bot-manager

# Test system components
python3 test_system.py

# Manual start (for debugging)
cd /opt/bot-manager
source venv/bin/activate
python3 run.py
```

---

**🎯 Choose the installation method that works best for you and start your bot hosting business! 🚀**