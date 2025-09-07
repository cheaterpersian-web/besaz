# 🔧 Root Installation Guide - Telegram Bot Manager System

## 🚨 Root Execution Issue

If you're getting this error:
```
❌ This script should not be run as root for security reasons.
ℹ️ Please run as a regular user with sudo privileges.
```

## 🎯 Solutions

### Option 1: Use Root Installation Script (Recommended)
```bash
# Download and run the root-specific installer
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/root_install.sh
chmod +x root_install.sh
sudo ./root_install.sh
```

### Option 2: Continue with Regular Script
```bash
# The regular script now asks if you want to continue as root
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/auto_install.sh
chmod +x auto_install.sh
sudo ./auto_install.sh
# When prompted, type 'y' to continue as root
```

### Option 3: Run as Regular User
```bash
# Create a regular user and run as that user
adduser botmanager
su - botmanager
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/auto_install.sh
chmod +x auto_install.sh
./auto_install.sh
```

## 🔧 Root Installation Script Features

The `root_install.sh` script is specifically designed for root execution:

- ✅ **Safe for root execution**
- ✅ **No sudo commands needed**
- ✅ **Direct systemd service creation**
- ✅ **Proper permissions handling**
- ✅ **Complete automated setup**

## 📋 Installation Commands

### For Root Users:
```bash
# Method 1: Root-specific installer
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/root_install.sh
chmod +x root_install.sh
sudo ./root_install.sh

# Method 2: Regular installer with root option
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/auto_install.sh
chmod +x auto_install.sh
sudo ./auto_install.sh
# Answer 'y' when asked about continuing as root
```

### For Regular Users:
```bash
# Regular installation
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/auto_install.sh
chmod +x auto_install.sh
./auto_install.sh
```

## 🎯 Quick Start for Root Users

```bash
# One-liner for root installation
curl -sSL https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/root_install.sh | sudo bash
```

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

## 🚀 Post-Installation

### Start the Service:
```bash
# For root users
systemctl start bot-manager
systemctl enable bot-manager

# For regular users
sudo systemctl start bot-manager
sudo systemctl enable bot-manager
```

### Check Status:
```bash
# For root users
systemctl status bot-manager

# For regular users
sudo systemctl status bot-manager
```

### View Logs:
```bash
# For root users
journalctl -u bot-manager -f

# For regular users
sudo journalctl -u bot-manager -f
```

## 🧪 Testing Your Installation

### Run System Tests:
```bash
cd /opt/bot-manager  # or your installation directory
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
systemctl status bot-manager

# Check logs
journalctl -u bot-manager -f

# Restart service
systemctl restart bot-manager
```

## 📊 Available Installation Scripts

### For Root Users:
- `root_install.sh` - **Recommended for root execution**
- `auto_install.sh` - Regular installer with root option
- `install_from_root.sh` - Installation from anywhere

### For Regular Users:
- `auto_install.sh` - **Recommended for regular users**
- `quick_setup.sh` - Quick configuration
- `one_liner_install.sh` - One-command installation

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
- Check system status: `systemctl status bot-manager`

### Useful Commands
```bash
# View real-time logs
journalctl -u bot-manager -f

# Restart service
systemctl restart bot-manager

# Check system status
systemctl status bot-manager

# Test system components
python3 test_system.py

# Manual start (for debugging)
cd /opt/bot-manager
source venv/bin/activate
python3 run.py
```

---

**🎯 Choose the installation method that works best for your setup! 🚀**