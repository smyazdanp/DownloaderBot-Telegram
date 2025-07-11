# 🚀 راهنمای نصب و راه‌اندازی ربات دانلودر تلگرام

## ✨ ویژگی‌های ربات

### 💎 ویژگی‌های کلیدی:
- ✅ دانلود فایل تا 2 گیگابایت
- ✅ تقسیم خودکار فایل‌های بزرگتر
- ✅ انتخاب نوع ارسال (عکس/ویدیو/صدا/فایل)
- ✅ سیستم محدودیت روزانه
- ✅ پنل مدیریت کامل
- ✅ دیتابیس SQLite
- ✅ آمار و نمودار
- ✅ سیستم VIP

### 🔧 پنل مدیریت:
- 📊 مشاهده آمار کلی و روزانه
- 📈 نمودار گرافیکی 7 روزه
- 👥 مدیریت کاربران
- ⭐ تنظیم VIP برای کاربران
- 🚫 تنظیم محدودیت شخصی و عمومی
- 📤 آپلود فایل و دریافت لینک

## 📋 پیش‌نیازها

### نصب Python:
```bash
# بررسی نسخه (باید 3.8 یا بالاتر باشد)
python --version

# در صورت نیاز:
# Windows: دانلود از python.org
# Linux: sudo apt install python3 python3-pip
# macOS: brew install python3
```

### نصب کتابخانه‌ها:
```bash
pip install -r requirements.txt

# یا به صورت دستی:
pip install aiogram==3.7.0 aiohttp aiofiles python-magic matplotlib
```

### برای ویندوز (حل مشکل python-magic):
```bash
pip install python-magic-bin
```

## 🤖 ایجاد ربات در تلگرام

1. به [@BotFather](https://t.me/botfather) پیام دهید
2. دستور `/newbot` را ارسال کنید
3. نام ربات را وارد کنید (مثل: Super Downloader)
4. یوزرنیم ربات را وارد کنید (باید به bot ختم شود مثل: super_downloader_bot)
5. توکن را کپی کنید

## ⚙️ پیکربندی ربات

### روش 1: ویرایش مستقیم کد
```python
# خط 62 را پیدا کنید:
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# توکن خود را جایگزین کنید:
BOT_TOKEN = os.environ.get("BOT_TOKEN", "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz")
```

### روش 2: متغیر محیطی (پیشنهادی)
```bash
# Linux/macOS:
export BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
export ADMIN_IDS="123456789,987654321"  # آیدی ادمین‌ها

# Windows Command Prompt:
set BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
set ADMIN_IDS=123456789,987654321

# Windows PowerShell:
$env:BOT_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
$env:ADMIN_IDS="123456789,987654321"
```

### دریافت آیدی تلگرام خود:
1. به [@userinfobot](https://t.me/userinfobot) پیام دهید
2. آیدی عددی خود را کپی کنید
3. در ADMIN_IDS قرار دهید

## 🏃 اجرای ربات

### اجرای معمولی:
```bash
python telegram_bot.py
```

### اجرا در پس‌زمینه:

**Linux/macOS با nohup:**
```bash
nohup python telegram_bot.py > bot.log 2>&1 &

# مشاهده لاگ:
tail -f bot.log

# توقف ربات:
ps aux | grep telegram_bot.py
kill PID
```

**Linux/macOS با screen:**
```bash
# نصب screen:
sudo apt install screen  # Debian/Ubuntu
sudo yum install screen  # CentOS

# ایجاد session:
screen -S bot

# اجرای ربات:
python telegram_bot.py

# خروج از screen: Ctrl+A سپس D

# بازگشت به screen:
screen -r bot
```

**Windows (پنجره جدید):**
```bash
start python telegram_bot.py
```

## 📱 استفاده از ربات

### دستورات عمومی:
- `/start` - شروع و نمایش منو
- `/help` - راهنمای استفاده
- `/mystats` - آمار شخصی

### دستورات ادمین:
- `/admin` - ورود به پنل مدیریت

### نحوه دانلود:
1. لینک مستقیم فایل را ارسال کنید
2. نوع ارسال را انتخاب کنید
3. منتظر دریافت فایل باشید

## 🌐 راه‌اندازی روی سرور

### استفاده از systemd (Linux):
```bash
# ایجاد فایل service:
sudo nano /etc/systemd/system/telegram-bot.service

# محتوای فایل:
[Unit]
Description=Telegram Downloader Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/bot
Environment="BOT_TOKEN=YOUR_TOKEN"
Environment="ADMIN_IDS=YOUR_ID"
ExecStart=/usr/bin/python3 /path/to/bot/telegram_bot.py
Restart=always

[Install]
WantedBy=multi-user.target

# فعال‌سازی و شروع:
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# بررسی وضعیت:
sudo systemctl status telegram-bot
```

### استفاده از Docker:
```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y libmagic1
COPY telegram_bot.py .
CMD ["python", "telegram_bot.py"]

# ساخت و اجرا:
docker build -t telegram-bot .
docker run -d --name bot \
  -e BOT_TOKEN=YOUR_TOKEN \
  -e ADMIN_IDS=YOUR_ID \
  telegram-bot
```

## 🔧 عیب‌یابی

### خطای import کتابخانه‌ها:
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### خطای python-magic در Windows:
```bash
pip uninstall python-magic python-magic-bin
pip install python-magic-bin
```

### ربات جواب نمی‌دهد:
1. توکن را بررسی کنید
2. اینترنت را چک کنید
3. لاگ‌ها را بررسی کنید

### مشکل دسترسی به دیتابیس:
```bash
# دسترسی به فایل:
chmod 644 bot_database.db

# یا حذف و ایجاد مجدد:
rm bot_database.db
python telegram_bot.py
```

## 📊 نکات تکمیلی

### بکاپ از دیتابیس:
```bash
# ایجاد بکاپ:
cp bot_database.db backup_$(date +%Y%m%d).db

# بکاپ خودکار روزانه با cron:
0 2 * * * cp /path/to/bot_database.db /path/to/backups/backup_$(date +\%Y\%m\%d).db
```

### محدودیت‌های تلگرام:
- حداکثر حجم فایل: 2GB
- حداکثر طول پیام: 4096 کاراکتر
- محدودیت درخواست: 30 پیام در ثانیه

### بهینه‌سازی:
- از VPS با رم حداقل 1GB استفاده کنید
- برای ترافیک بالا از Redis برای کش استفاده کنید
- لاگ‌ها را دوره‌ای پاکسازی کنید

## 🆘 پشتیبانی

در صورت بروز مشکل:
1. لاگ‌ها را بررسی کنید
2. مستندات aiogram را مطالعه کنید
3. در گروه‌های تلگرامی Python سوال بپرسید

موفق باشید! 🎉