# نصب سریع (لینوکس)

## پیش‌نیازها
- Python 3.11+
- Git

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
```

## دانلود و اجرا
```bash
# کلون پروژه
git clone <این ریپو> bot-manager && cd bot-manager

# ساخت محیط مجازی و نصب وابستگی‌ها
python3 -m venv .venv
. .venv/bin/activate
pip install --no-cache-dir -r requirements.txt

# تنظیم متغیرها
cp .env.example .env
# مقداردهی MAIN_BOT_TOKEN و ADMIN_USER_ID و ... در فایل .env

# اجرای برنامه
python run.py
```

## نکات
- لاگ‌ها داخل پوشه `logs/` هستند (حجم محدود شده).
- دیتابیس داخل `data/bot_manager.db` ذخیره می‌شود.
- برای توقف اجرا در ترمینال: Ctrl+C.
- برای پاکسازی سریع: `rm -rf __pycache__ logs/* *.pid`.
