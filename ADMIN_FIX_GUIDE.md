# 🔧 راهنمای حل مشکل ادمین - Telegram Bot Manager System

## 🚨 مشکل: "Access denied. Admin privileges required."

اگر این پیام را می‌بینید:
```
❌ دسترسی رد شد. دسترسی ادمین مورد نیاز است.
```

## 🎯 علل احتمالی:

1. **کاربر ادمین در دیتابیس وجود ندارد**
2. **آیدی کاربر در فایل .env اشتباه است**
3. **کاربر با نقش ادمین ثبت نشده است**
4. **دیتابیس به درستی راه‌اندازی نشده است**

## 🛠️ راه‌حل‌ها

### راه‌حل 1: استفاده از اسکریپت تعمیر (پیشنهادی)
```bash
# دانلود و اجرای اسکریپت تعمیر
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/fix_admin.py
chmod +x fix_admin.py
python3 fix_admin.py
```

### راه‌حل 2: تعمیر کامل با فارسی‌سازی
```bash
# دانلود و اجرای اسکریپت تعمیر کامل
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/fix_and_farsi.sh
chmod +x fix_and_farsi.sh
./fix_and_farsi.sh
```

### راه‌حل 3: تعمیر دستی

#### مرحله 1: بررسی فایل .env
```bash
# بررسی محتویات فایل .env
cat .env | grep ADMIN_USER_ID
```

#### مرحله 2: دریافت آیدی کاربری خود
```bash
# به ربات @userinfobot پیام بفرستید تا آیدی خود را دریافت کنید
# یا از ربات خود /start بزنید و آیدی را از لاگ‌ها ببینید
```

#### مرحله 3: به‌روزرسانی فایل .env
```bash
# ویرایش فایل .env
nano .env

# مطمئن شوید که این خط درست است:
ADMIN_USER_ID=your_actual_user_id_here
```

#### مرحله 4: تعمیر دیتابیس
```bash
# فعال‌سازی محیط مجازی
source venv/bin/activate

# اجرای اسکریپت تعمیر
python3 fix_admin.py
```

## 🔍 تشخیص مشکل

### 1. بررسی آیدی کاربری
```bash
# بررسی فایل .env
grep ADMIN_USER_ID .env

# باید چیزی شبیه این باشد:
# ADMIN_USER_ID=123456789
```

### 2. بررسی دیتابیس
```bash
# فعال‌سازی محیط مجازی
source venv/bin/activate

# اجرای اسکریپت تشخیص
python3 fix_admin.py
```

### 3. بررسی لاگ‌ها
```bash
# بررسی لاگ‌های ربات
tail -f logs/bot_manager.log

# یا اگر با systemd اجرا می‌کنید
sudo journalctl -u bot-manager -f
```

## 📋 مراحل کامل تعمیر

### مرحله 1: توقف ربات
```bash
# اگر با systemd اجرا می‌کنید
sudo systemctl stop bot-manager

# یا اگر دستی اجرا می‌کنید
pkill -f "python run.py"
```

### مرحله 2: بررسی تنظیمات
```bash
# بررسی فایل .env
cat .env

# مطمئن شوید که این خطوط درست هستند:
# MAIN_BOT_TOKEN=your_bot_token
# ADMIN_USER_ID=your_user_id
# LOCKED_CHANNEL_ID=@your_channel
```

### مرحله 3: تعمیر ادمین
```bash
# فعال‌سازی محیط مجازی
source venv/bin/activate

# اجرای اسکریپت تعمیر
python3 fix_admin.py
```

### مرحله 4: تست سیستم
```bash
# تست سریع
python3 test_quick.py

# اگر همه چیز درست بود، ربات را استارت کنید
./start_bot.sh
```

### مرحله 5: تست ادمین
```bash
# به ربات خود /admin بفرستید
# باید پنل ادمین نمایش داده شود
```

## 🚨 مشکلات رایج

### مشکل 1: آیدی کاربری اشتباه
```bash
# دریافت آیدی صحیح از @userinfobot
# به‌روزرسانی فایل .env
nano .env
# تغییر ADMIN_USER_ID به آیدی صحیح
```

### مشکل 2: دیتابیس خراب
```bash
# حذف دیتابیس قدیمی
rm bot_manager.db

# ایجاد مجدد
source venv/bin/activate
python3 -c "from database import db; import asyncio; asyncio.run(db.init_db())"

# تعمیر ادمین
python3 fix_admin.py
```

### مشکل 3: محیط مجازی خراب
```bash
# حذف محیط مجازی قدیمی
rm -rf venv

# ایجاد مجدد
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# تعمیر ادمین
python3 fix_admin.py
```

## 🧪 تست نهایی

### تست 1: بررسی ادمین
```bash
# اجرای تست
python3 fix_admin.py

# باید پیام موفقیت ببینید:
# ✅ Admin user fixed successfully!
```

### تست 2: تست ربات
```bash
# استارت ربات
./start_bot.sh

# در ربات /admin بزنید
# باید پنل ادمین نمایش داده شود
```

### تست 3: تست فارسی
```bash
# در ربات /start بزنید
# باید پیام فارسی نمایش داده شود
```

## 📊 دستورات مفید

### بررسی وضعیت:
```bash
# بررسی فایل .env
cat .env | grep ADMIN_USER_ID

# بررسی دیتابیس
python3 fix_admin.py

# بررسی لاگ‌ها
tail -f logs/bot_manager.log
```

### تعمیر سریع:
```bash
# تعمیر کامل
./fix_and_farsi.sh

# یا تعمیر فقط ادمین
python3 fix_admin.py
```

### استارت ربات:
```bash
# استارت سریع
./start_bot.sh

# یا استارت دستی
source venv/bin/activate
python -W ignore::UserWarning run.py
```

## 🎉 پس از حل مشکل

### تست‌های نهایی:
1. **تست ادمین**: `/admin` بزنید
2. **تست فارسی**: `/start` بزنید
3. **تست عملکرد**: تمام قابلیت‌ها را تست کنید

### دستورات مفید:
```bash
# مشاهده لاگ‌های زنده
tail -f logs/bot_manager.log

# راه‌اندازی مجدد در صورت نیاز
./start_bot.sh

# بررسی وضعیت
ps aux | grep "run.py"
```

---

**🎯 با این راهنما باید بتوانید مشکل ادمین را حل کنید! 🚀**