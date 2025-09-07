# راهنمای نصب سیستم مدیریت ربات تلگرام

## 🚀 نصب خودکار (پیشنهادی)

### روش 1: نصب کامل خودکار
```bash
# دانلود و اجرای اسکریپت نصب
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/auto_install.sh
chmod +x auto_install.sh
./auto_install.sh
```

### روش 2: تنظیم سریع
```bash
# تنظیم سریع فقط با اطلاعات ضروری
wget https://raw.githubusercontent.com/your-repo/telegram-bot-manager/main/quick_setup.sh
chmod +x quick_setup.sh
./quick_setup.sh
```

## 📋 اطلاعات مورد نیاز

قبل از نصب، این اطلاعات را آماده کنید:

### 1. اطلاعات ربات
- **توکن ربات**: از @BotFather دریافت کنید
- **آیدی کاربری شما**: از @userinfobot دریافت کنید
- **آیدی کانال**: کانالی که کاربران باید عضو شوند

### 2. اطلاعات پرداخت
- **شماره کارت بانکی**: برای دریافت پرداخت
- **آدرس کیف پول کریپتو**: برای پرداخت ارز دیجیتال

### 3. قیمت‌گذاری
- **قیمت 1 ماهه**: مثلاً 10 دلار
- **قیمت 2 ماهه**: مثلاً 18 دلار
- **قیمت 3 ماهه**: مثلاً 25 دلار

## 🔧 مراحل نصب

### مرحله 1: آماده‌سازی سرور
```bash
# به‌روزرسانی سیستم
sudo apt update && sudo apt upgrade -y

# نصب Python و Git
sudo apt install python3 python3-pip python3-venv git -y
```

### مرحله 2: دانلود سیستم
```bash
# کلون کردن ریپازیتوری
git clone https://github.com/your-repo/telegram-bot-manager.git
cd telegram-bot-manager
```

### مرحله 3: نصب خودکار
```bash
# اجرای اسکریپت نصب
./auto_install.sh
```

### مرحله 4: راه‌اندازی سرویس
```bash
# شروع سرویس
sudo systemctl start bot-manager

# فعال‌سازی خودکار
sudo systemctl enable bot-manager

# بررسی وضعیت
sudo systemctl status bot-manager
```

## 🎯 استفاده از سیستم

### برای کاربران:
1. ارسال `/start` به ربات اصلی
2. عضویت در کانال مورد نظر
3. ایجاد ربات جدید با "Create New Bot"
4. ارائه توکن ربات از @BotFather
5. انتخاب پلن اشتراک
6. ارسال مدرک پرداخت
7. انتظار برای تأیید ادمین

### برای ادمین:
1. ارسال `/admin` برای دسترسی به پنل ادمین
2. بررسی پرداخت‌های در انتظار
3. تأیید یا رد پرداخت‌ها
4. مدیریت کاربران و ربات‌ها
5. تنظیم قیمت‌ها و پیکربندی سیستم

## 🔍 عیب‌یابی

### بررسی لاگ‌ها
```bash
# مشاهده لاگ‌های سیستم
sudo journalctl -u bot-manager -f

# مشاهده لاگ‌های فایل
tail -f logs/bot_manager.log
```

### مشکلات رایج

#### ربات کار نمی‌کند
```bash
# بررسی وضعیت سرویس
sudo systemctl status bot-manager

# راه‌اندازی مجدد
sudo systemctl restart bot-manager
```

#### خطای توکن
- بررسی صحت توکن ربات
- اطمینان از دسترسی ربات به کانال
- بررسی محدودیت‌های API تلگرام

#### خطای دیتابیس
```bash
# بررسی فایل دیتابیس
ls -la bot_manager.db

# ایجاد مجدد دیتابیس
rm bot_manager.db
python3 -c "from database import db; import asyncio; asyncio.run(db.init_db())"
```

## 📊 مدیریت سیستم

### دستورات مفید
```bash
# شروع سرویس
sudo systemctl start bot-manager

# توقف سرویس
sudo systemctl stop bot-manager

# راه‌اندازی مجدد
sudo systemctl restart bot-manager

# بررسی وضعیت
sudo systemctl status bot-manager

# مشاهده لاگ‌ها
sudo journalctl -u bot-manager -f
```

### پشتیبان‌گیری
```bash
# پشتیبان‌گیری از دیتابیس
cp bot_manager.db backup_$(date +%Y%m%d).db

# پشتیبان‌گیری از تنظیمات
cp .env backup_env_$(date +%Y%m%d).env
```

## 🔒 امنیت

### نکات امنیتی
- توکن ربات را محرمانه نگه دارید
- فایل `.env` را در دسترس عموم قرار ندهید
- به‌طور منظم سیستم را به‌روزرسانی کنید
- از فایروال مناسب استفاده کنید

### تغییر رمز عبور
```bash
# تغییر رمز عبور کاربر سیستم
sudo passwd botmanager
```

## 📞 پشتیبانی

### در صورت مشکل:
1. بررسی لاگ‌های سیستم
2. بررسی وضعیت سرویس
3. راه‌اندازی مجدد سیستم
4. تماس با پشتیبانی

### اطلاعات مفید برای پشتیبانی:
- نسخه سیستم عامل
- نسخه Python
- پیام خطا
- لاگ‌های مربوطه

## 🎉 تبریک!

سیستم مدیریت ربات تلگرام شما آماده است! 

حالا می‌توانید:
- ربات‌های کاربران را مدیریت کنید
- اشتراک‌ها را کنترل کنید
- پرداخت‌ها را تأیید کنید
- سیستم را مانیتور کنید

**موفق باشید! 🚀**