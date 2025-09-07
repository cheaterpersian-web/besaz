# 🔧 راهنمای عیب‌یابی - Telegram Bot Manager System

## 🚨 خطای systemd: status=203/EXEC

اگر این خطا را می‌بینید:
```
systemd[1]: bot-manager.service: Main process exited, code=exited, status=203/EXEC
```

### 🎯 علل احتمالی:
1. **مسیر فایل اجرایی اشتباه**
2. **فایل اجرایی وجود ندارد**
3. **مجوزهای فایل اشتباه**
4. **محیط مجازی Python وجود ندارد**
5. **وابستگی‌های Python نصب نشده**

## 🔍 تشخیص مشکل

### 1. اجرای اسکریپت تشخیص:
```bash
# دانلود و اجرای اسکریپت تشخیص
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/diagnose.sh
chmod +x diagnose.sh
./diagnose.sh
```

### 2. بررسی دستی:
```bash
# بررسی وضعیت سرویس
sudo systemctl status bot-manager

# بررسی لاگ‌ها
sudo journalctl -u bot-manager -f

# بررسی فایل‌ها
ls -la /opt/bot-manager/  # یا مسیر نصب شما
```

## 🛠️ راه‌حل‌ها

### راه‌حل 1: استفاده از اسکریپت تعمیر (پیشنهادی)
```bash
# دانلود و اجرای اسکریپت تعمیر
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/fix_systemd.sh
chmod +x fix_systemd.sh
sudo ./fix_systemd.sh
```

### راه‌حل 2: تعمیر دستی

#### مرحله 1: توقف سرویس
```bash
sudo systemctl stop bot-manager
```

#### مرحله 2: بررسی فایل‌ها
```bash
# بررسی وجود فایل‌ها
ls -la /opt/bot-manager/run.py
ls -la /opt/bot-manager/venv/bin/python

# اگر فایل‌ها وجود ندارند، ایجاد کنید
cd /opt/bot-manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### مرحله 3: تنظیم مجوزها
```bash
chmod +x /opt/bot-manager/run.py
chmod +x /opt/bot-manager/venv/bin/python
```

#### مرحله 4: تست اجرا
```bash
cd /opt/bot-manager
source venv/bin/activate
python run.py
```

#### مرحله 5: ایجاد مجدد سرویس systemd
```bash
sudo tee /etc/systemd/system/bot-manager.service > /dev/null << EOF
[Unit]
Description=Telegram Bot Manager System
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/bot-manager
ExecStart=/opt/bot-manager/venv/bin/python /opt/bot-manager/run.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/bot-manager
Environment=PYTHONUNBUFFERED=1

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=bot-manager

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/bot-manager/data /opt/bot-manager/logs /opt/bot-manager/deployed_bots

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start bot-manager
```

### راه‌حل 3: نصب مجدد
```bash
# حذف سرویس قدیمی
sudo systemctl stop bot-manager
sudo systemctl disable bot-manager
sudo rm /etc/systemd/system/bot-manager.service

# نصب مجدد
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/root_install.sh
chmod +x root_install.sh
sudo ./root_install.sh
```

## 🔍 مشکلات رایج

### مشکل 1: فایل .env وجود ندارد
```bash
# ایجاد فایل .env
cat > /opt/bot-manager/.env << EOF
MAIN_BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_user_id_here
MAIN_BOT_ID=your_bot_id_here
LOCKED_CHANNEL_ID=@your_channel
DATABASE_URL=sqlite:///bot_manager.db
BOT_REPO_URL=https://github.com/your-username/telegram-bot-template.git
BOT_DEPLOYMENT_DIR=/opt/bot-manager/deployed_bots
BOT_PYTHON_PATH=/usr/bin/python3
BANK_CARD_NUMBER=1234567890123456
CRYPTO_WALLET_ADDRESS=your_crypto_wallet_address
PLAN_1_MONTH=30
PLAN_2_MONTHS=60
PLAN_3_MONTHS=90
PRICE_1_MONTH=10.00
PRICE_2_MONTHS=18.00
PRICE_3_MONTHS=25.00
BOT_STATUS_ACTIVE=active
BOT_STATUS_INACTIVE=inactive
BOT_STATUS_EXPIRED=expired
BOT_STATUS_PENDING=pending
PAYMENT_STATUS_PENDING=pending
PAYMENT_STATUS_APPROVED=approved
PAYMENT_STATUS_REJECTED=rejected
USER_ROLE_ADMIN=admin
USER_ROLE_USER=user
EOF
```

### مشکل 2: محیط مجازی Python وجود ندارد
```bash
cd /opt/bot-manager
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### مشکل 3: مجوزهای فایل اشتباه
```bash
chmod +x /opt/bot-manager/run.py
chmod +x /opt/bot-manager/venv/bin/python
chmod 755 /opt/bot-manager/data
chmod 755 /opt/bot-manager/logs
chmod 755 /opt/bot-manager/deployed_bots
```

### مشکل 4: وابستگی‌های Python نصب نشده
```bash
cd /opt/bot-manager
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 🧪 تست سیستم

### تست 1: تست Python
```bash
cd /opt/bot-manager
source venv/bin/activate
python -c "import sys; print('Python test: OK')"
```

### تست 2: تست Import ها
```bash
cd /opt/bot-manager
source venv/bin/activate
python -c "from config import Config; print('Config import: OK')"
python -c "from telegram import Bot; print('Telegram import: OK')"
python -c "from database import db; print('Database import: OK')"
```

### تست 3: تست اجرای اصلی
```bash
cd /opt/bot-manager
source venv/bin/activate
python run.py
# اگر خطا داد، Ctrl+C بزنید
```

## 📊 دستورات مفید

### بررسی وضعیت:
```bash
# وضعیت سرویس
sudo systemctl status bot-manager

# لاگ‌های زنده
sudo journalctl -u bot-manager -f

# لاگ‌های اخیر
sudo journalctl -u bot-manager --no-pager -n 50
```

### مدیریت سرویس:
```bash
# شروع سرویس
sudo systemctl start bot-manager

# توقف سرویس
sudo systemctl stop bot-manager

# راه‌اندازی مجدد
sudo systemctl restart bot-manager

# فعال‌سازی خودکار
sudo systemctl enable bot-manager

# غیرفعال‌سازی خودکار
sudo systemctl disable bot-manager
```

### بررسی فایل‌ها:
```bash
# بررسی وجود فایل‌ها
ls -la /opt/bot-manager/

# بررسی مجوزها
ls -la /opt/bot-manager/run.py
ls -la /opt/bot-manager/venv/bin/python

# بررسی محتویات فایل
cat /opt/bot-manager/.env
```

## 🚨 در صورت عدم حل مشکل

### 1. بررسی کامل سیستم:
```bash
./diagnose.sh
```

### 2. تعمیر خودکار:
```bash
./fix_systemd.sh
```

### 3. نصب مجدد:
```bash
sudo ./root_install.sh
```

### 4. تماس با پشتیبانی:
- لاگ‌های کامل را ارسال کنید
- خروجی `./diagnose.sh` را ارسال کنید
- نسخه سیستم عامل و Python را ذکر کنید

## 🎉 پس از حل مشکل

### تست نهایی:
```bash
# بررسی وضعیت
sudo systemctl status bot-manager

# تست ربات
# به ربات خود /start بفرستید

# بررسی لاگ‌ها
sudo journalctl -u bot-manager -f
```

### دستورات مفید:
```bash
# مشاهده لاگ‌های زنده
sudo journalctl -u bot-manager -f

# راه‌اندازی مجدد در صورت نیاز
sudo systemctl restart bot-manager

# بررسی وضعیت
sudo systemctl status bot-manager
```

---

**🎯 با این راهنما باید بتوانید مشکل systemd را حل کنید! 🚀**