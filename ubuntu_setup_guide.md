# 🚀 راهنمای جامع راه‌اندازی ربات تلگرام روی Ubuntu

این راهنما برای Ubuntu 20.04 و بالاتر نوشته شده و فرض می‌کند سرور کاملاً خام است.

## 📋 فهرست مطالب
1. [آماده‌سازی سرور](#1-آماده‌سازی-سرور)
2. [نصب Python و پیش‌نیازها](#2-نصب-python-و-پیش‌نیازها)
3. [ایجاد ربات در تلگرام](#3-ایجاد-ربات-در-تلگرام)
4. [دانلود و نصب کد ربات](#4-دانلود-و-نصب-کد-ربات)
5. [پیکربندی ربات](#5-پیکربندی-ربات)
6. [اجرای آزمایشی](#6-اجرای-آزمایشی)
7. [راه‌اندازی دائمی با systemd](#7-راه‌اندازی-دائمی-با-systemd)
8. [مانیتورینگ و نگهداری](#8-مانیتورینگ-و-نگهداری)
9. [عیب‌یابی](#9-عیب‌یابی)
10. [بهینه‌سازی و امنیت](#10-بهینه‌سازی-و-امنیت)

---

## 1. آماده‌سازی سرور

### اتصال به سرور
```bash
# اتصال از طریق SSH
ssh root@your-server-ip

# یا با کلید SSH
ssh -i your-key.pem ubuntu@your-server-ip
```

### به‌روزرسانی سیستم
```bash
# به‌روزرسانی لیست پکیج‌ها
sudo apt update

# ارتقاء پکیج‌های نصب شده
sudo apt upgrade -y

# نصب ابزارهای پایه
sudo apt install -y curl wget git nano vim htop screen tmux build-essential software-properties-common
```

### ایجاد کاربر جدید (اختیاری اما توصیه می‌شود)
```bash
# ایجاد کاربر جدید
sudo adduser botuser

# افزودن به گروه sudo
sudo usermod -aG sudo botuser

# تغییر به کاربر جدید
su - botuser
```

### تنظیم فایروال
```bash
# نصب و فعال‌سازی UFW
sudo apt install -y ufw

# اجازه SSH
sudo ufw allow ssh

# اجازه پورت‌های دیگر در صورت نیاز
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS

# فعال‌سازی فایروال
sudo ufw --force enable

# بررسی وضعیت
sudo ufw status
```

---

## 2. نصب Python و پیش‌نیازها

### نصب Python 3.11 (توصیه می‌شود)
```bash
# افزودن repository
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# نصب Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils

# نصب pip
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# ایجاد alias (اختیاری)
echo "alias python=python3.11" >> ~/.bashrc
echo "alias pip=pip3.11" >> ~/.bashrc
source ~/.bashrc

# بررسی نسخه
python3.11 --version
pip3.11 --version
```

### نصب کتابخانه‌های سیستمی مورد نیاز
```bash
# برای python-magic
sudo apt install -y libmagic1 libmagic-dev

# برای matplotlib و Pillow
sudo apt install -y libjpeg-dev zlib1g-dev libpng-dev libfreetype6-dev liblcms2-dev libtiff5-dev

# برای عملیات فایل
sudo apt install -y ffmpeg unzip p7zip-full

# فونت‌های فارسی (برای نمودارها)
sudo apt install -y fonts-liberation fonts-dejavu-core fonts-noto

# ابزارهای مانیتورینگ
sudo apt install -y htop iotop nethogs
```

---

## 3. ایجاد ربات در تلگرام

### مراحل ساخت ربات

#### برای ربات جدید:

1. **باز کردن BotFather**
   - در تلگرام به [@BotFather](https://t.me/botfather) پیام دهید

2. **ایجاد ربات جدید**
   ```
   /newbot
   ```

3. **انتخاب نام**
   ```
   Super Downloader Bot
   ```

4. **انتخاب username**
   ```
   super_downloader_bot
   ```
   توجه: باید به `bot` ختم شود و یونیک باشد

5. **دریافت توکن**
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz...
   ```

#### برای استفاده از توکن موجود:
توکن شما: `8041569656:AAHaC9c6SoFMy0rlk5Hap3DD6tfUtBaAixw`

### دریافت آیدی خودتان

#### روش 1: استفاده از ربات
1. به [@userinfobot](https://t.me/userinfobot) پیام دهید
2. آیدی عددی خود را کپی کنید

#### روش 2: استفاده از آیدی موجود
آیدی شما: `111111111`

---

## 4. دانلود و نصب کد ربات

### ایجاد دایرکتوری پروژه
```bash
# ایجاد پوشه
mkdir -p ~/telegram-bot
cd ~/telegram-bot

# ایجاد محیط مجازی
python3.11 -m venv venv

# فعال‌سازی محیط مجازی
source venv/bin/activate
```

### ایجاد فایل‌های پروژه

#### 1. ایجاد فایل اصلی ربات
```bash
nano telegram_bot.py
```
سپس کد کامل ربات را کپی و paste کنید (Ctrl+Shift+V)
ذخیره: Ctrl+X سپس Y سپس Enter

#### 2. ایجاد فایل requirements.txt
```bash
nano requirements.txt
```
محتوای فایل requirements.txt را کپی و paste کنید

#### 3. نصب کتابخانه‌ها
```bash
# نصب همه کتابخانه‌ها
pip install -r requirements.txt

# برای Linux/Mac، python-magic-bin را حذف کنید:
pip uninstall python-magic-bin -y

# بررسی نصب
pip list
```

---

## 5. پیکربندی ربات

### توکن و آیدی‌های شما:
- **توکن ربات**: `8041569656:AAHaC9c6SoFMy0rlk5Hap3DD6tfUtBaAixw`
- **آیدی ادمین**: `111111111`

### روش 1: ویرایش مستقیم کد (ساده‌تر)
کد از قبل با توکن و آیدی شما تنظیم شده است. نیازی به تغییر نیست!

### روش 2: استفاده از متغیرهای محیطی (برای امنیت بیشتر)

#### ایجاد فایل .env
```bash
nano .env
```

محتوا:
```bash
# توکن ربات
BOT_TOKEN=8041569656:AAHaC9c6SoFMy0rlk5Hap3DD6tfUtBaAixw

# آیدی ادمین‌ها (با کاما جدا شوند)
ADMIN_IDS=111111111
```

#### تغییر کد برای خواندن از محیط
```bash
nano telegram_bot.py
```

خطوط 78-79 را به این شکل تغییر دهید:
```python
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8041569656:AAHaC9c6SoFMy0rlk5Hap3DD6tfUtBaAixw")
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "111111111").split(",") if x.strip()]
```

#### ایجاد اسکریپت راه‌انداز
```bash
nano start_bot.sh
```

محتوا:
```bash
#!/bin/bash
# بارگذاری متغیرهای محیطی
export $(cat .env | xargs)

# اجرای ربات
/home/botuser/telegram-bot/venv/bin/python /home/botuser/telegram-bot/telegram_bot.py
```

دسترسی اجرا:
```bash
chmod +x start_bot.sh
```

---

## 6. اجرای آزمایشی

### اجرای ساده
```bash
# با محیط مجازی فعال
python telegram_bot.py

# یا با اسکریپت
./start_bot.sh
```

### اجرا با screen (برای تست طولانی)
```bash
# ایجاد session جدید
screen -S bot

# اجرای ربات
python telegram_bot.py

# خروج از screen: Ctrl+A سپس D

# بازگشت به screen
screen -r bot

# لیست screen ها
screen -ls
```

### بررسی عملکرد
1. به ربات در تلگرام پیام `/start` بدهید
2. باید منوی اصلی را ببینید با دکمه "پنل ادمین"
3. یک لینک دانلود تست کنید، مثلا:
   ```
   https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf
   ```

---

## 7. راه‌اندازی دائمی با systemd

### ایجاد فایل service
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

محتوا (با توکن و آیدی شما):
```ini
[Unit]
Description=Telegram Downloader Bot
After=network.target

[Service]
Type=simple
User=botuser
Group=botuser
WorkingDirectory=/home/botuser/telegram-bot

# مسیرها را با مسیر واقعی خود جایگزین کنید
Environment="PATH=/home/botuser/telegram-bot/venv/bin"
Environment="BOT_TOKEN=8041569656:AAHaC9c6SoFMy0rlk5Hap3DD6tfUtBaAixw"
Environment="ADMIN_IDS=111111111"

ExecStart=/home/botuser/telegram-bot/venv/bin/python /home/botuser/telegram-bot/telegram_bot.py

# تنظیمات Restart
Restart=always
RestartSec=10

# محدودیت‌ها
LimitNOFILE=4096
StandardOutput=append:/home/botuser/telegram-bot/bot.log
StandardError=append:/home/botuser/telegram-bot/error.log

[Install]
WantedBy=multi-user.target
```

### فعال‌سازی و شروع سرویس
```bash
# بارگذاری مجدد systemd
sudo systemctl daemon-reload

# فعال‌سازی برای شروع خودکار
sudo systemctl enable telegram-bot.service

# شروع سرویس
sudo systemctl start telegram-bot.service

# بررسی وضعیت
sudo systemctl status telegram-bot.service

# مشاهده لاگ‌ها
sudo journalctl -u telegram-bot.service -f
```

### دستورات مدیریت سرویس
```bash
# توقف
sudo systemctl stop telegram-bot.service

# ری‌استارت
sudo systemctl restart telegram-bot.service

# غیرفعال کردن شروع خودکار
sudo systemctl disable telegram-bot.service
```

---

## 8. مانیتورینگ و نگهداری

### تنظیم logrotate
```bash
sudo nano /etc/logrotate.d/telegram-bot
```

محتوا:
```
/home/botuser/telegram-bot/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 botuser botuser
    postrotate
        systemctl reload telegram-bot.service > /dev/null 2>&1 || true
    endscript
}
```

### ایجاد اسکریپت مانیتورینگ
```bash
nano ~/monitor_bot.sh
```

محتوا:
```bash
#!/bin/bash

BOT_TOKEN="8041569656:AAHaC9c6SoFMy0rlk5Hap3DD6tfUtBaAixw"
ADMIN_ID="111111111"

# بررسی وضعیت سرویس
if ! systemctl is-active --quiet telegram-bot.service; then
    echo "Bot is down! Restarting..."
    sudo systemctl restart telegram-bot.service
    
    # ارسال هشدار به تلگرام
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
         -d "chat_id=$ADMIN_ID&text=⚠️ ربات ری‌استارت شد!"
fi

# بررسی مصرف منابع
echo "=== Resource Usage ==="
ps aux | grep telegram_bot.py | grep -v grep

# بررسی دیسک
echo -e "\n=== Disk Usage ==="
df -h /home/botuser/telegram-bot

# تعداد فایل‌های temp
echo -e "\n=== Temp Files ==="
find /home/botuser/telegram-bot/temp -type f | wc -l

# حجم دیتابیس
echo -e "\n=== Database Size ==="
du -sh /home/botuser/telegram-bot/bot_database.db
```

دسترسی اجرا:
```bash
chmod +x ~/monitor_bot.sh
```

### افزودن به crontab
```bash
crontab -e
```

اضافه کنید:
```cron
# بررسی هر 5 دقیقه
*/5 * * * * /home/botuser/monitor_bot.sh >> /home/botuser/monitor.log 2>&1

# پاکسازی فایل‌های قدیمی روزانه
0 3 * * * find /home/botuser/telegram-bot/temp -type f -mtime +1 -delete

# بکاپ دیتابیس هفتگی
0 2 * * 0 cp /home/botuser/telegram-bot/bot_database.db /home/botuser/backups/bot_db_$(date +\%Y\%m\%d).db

# پاکسازی لاگ‌های قدیمی
0 4 * * * find /home/botuser/telegram-bot -name "*.log" -mtime +30 -delete
```

### مانیتورینگ real-time
```bash
# مشاهده لاگ‌ها
tail -f ~/telegram-bot/bot.log

# مانیتور منابع
htop

# مانیتور شبکه
sudo nethogs

# مانیتور دیسک
iotop
```

---

## 9. عیب‌یابی

### بررسی لاگ‌ها
```bash
# لاگ سیستمی
sudo journalctl -u telegram-bot.service -n 100

# لاگ فایل
tail -f ~/telegram-bot/bot.log

# لاگ خطاها
tail -f ~/telegram-bot/error.log
```

### مشکلات رایج و راه‌حل

#### 1. خطای Import کتابخانه‌ها
```bash
# بررسی نصب
source ~/telegram-bot/venv/bin/activate
pip list

# نصب مجدد
pip install --upgrade -r requirements.txt
```

#### 2. خطای دسترسی به فایل
```bash
# تغییر مالکیت
sudo chown -R botuser:botuser ~/telegram-bot

# دسترسی‌ها
chmod -R 755 ~/telegram-bot
chmod 600 ~/telegram-bot/.env
```

#### 3. مشکل python-magic
```bash
# نصب مجدد
sudo apt install --reinstall libmagic1
pip uninstall python-magic python-magic-bin
pip install python-magic
```

#### 4. ربات جواب نمی‌دهد
```bash
# بررسی توکن
grep BOT_TOKEN ~/telegram-bot/telegram_bot.py

# تست اتصال
curl https://api.telegram.org/bot8041569656:AAHaC9c6SoFMy0rlk5Hap3DD6tfUtBaAixw/getMe

# بررسی فایروال
sudo ufw status
```

#### 5. مشکل matplotlib
```bash
# نصب backend
sudo apt install python3-tk

# تنظیم متغیر محیطی
export MPLBACKEND=Agg
```

### دیباگ کردن
```bash
# اجرای دستی با نمایش خطاها
cd ~/telegram-bot
source venv/bin/activate
python -u telegram_bot.py
```

### بررسی عملکرد دیتابیس
```bash
# دسترسی به SQLite
sqlite3 ~/telegram-bot/bot_database.db

# دستورات مفید
.tables
.schema users
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM downloads WHERE DATE(download_date) = DATE('now');
.exit
```

---

## 10. بهینه‌سازی و امنیت

### بهینه‌سازی عملکرد

#### 1. تنظیمات Python
```bash
# افزودن به start_bot.sh
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
```

#### 2. افزایش محدودیت‌های سیستم
```bash
# ویرایش limits
sudo nano /etc/security/limits.conf
```

اضافه کنید:
```
botuser soft nofile 65536
botuser hard nofile 65536
botuser soft nproc 32768
botuser hard nproc 32768
```

#### 3. بهینه‌سازی دیتابیس
```bash
# vacuum دیتابیس (ماهانه)
sqlite3 ~/telegram-bot/bot_database.db "VACUUM;"
```

### امنیت

#### 1. محدود کردن دسترسی SSH
```bash
# فقط با کلید
sudo nano /etc/ssh/sshd_config
```

تغییر دهید:
```
PasswordAuthentication no
PermitRootLogin no
```

```bash
sudo systemctl restart ssh
```

#### 2. نصب Fail2ban
```bash
sudo apt install -y fail2ban

# پیکربندی
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local

# فعال‌سازی
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

#### 3. بکاپ خودکار
```bash
# اسکریپت بکاپ
nano ~/backup.sh
```

محتوا:
```bash
#!/bin/bash
BACKUP_DIR="/home/botuser/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# ایجاد پوشه بکاپ
mkdir -p $BACKUP_DIR

# بکاپ دیتابیس
cp ~/telegram-bot/bot_database.db $BACKUP_DIR/db_$DATE.db

# بکاپ کد
tar -czf $BACKUP_DIR/code_$DATE.tar.gz ~/telegram-bot/*.py ~/telegram-bot/requirements.txt

# بکاپ تنظیمات
cp ~/telegram-bot/.env $BACKUP_DIR/env_$DATE

# آپلود به سرور خارجی (اختیاری)
# rsync -avz $BACKUP_DIR/ user@backup-server:/path/to/backups/

# حذف بکاپ‌های قدیمی (بیش از 30 روز)
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

```bash
chmod +x ~/backup.sh
# افزودن به cron برای اجرای روزانه
```

#### 4. مانیتورینگ امنیتی
```bash
# نصب ابزارهای امنیتی
sudo apt install -y rkhunter lynis

# اسکن با rkhunter
sudo rkhunter --check

# اسکن با lynis
sudo lynis audit system
```

---

## 📊 چک‌لیست نهایی

- [x] سرور Ubuntu به‌روز شده
- [x] Python 3.11 نصب شده
- [x] محیط مجازی ایجاد شده
- [x] کتابخانه‌ها نصب شده
- [x] توکن ربات: `8041569656:AAHaC9c6SoFMy0rlk5Hap3DD6tfUtBaAixw`
- [x] آیدی ادمین: `111111111`
- [ ] ربات تست شده
- [ ] سرویس systemd راه‌اندازی شده
- [ ] لاگ‌ها بررسی شده
- [ ] بکاپ خودکار تنظیم شده
- [ ] مانیتورینگ فعال شده

---

## 🎉 تبریک!

ربات شما آماده استفاده است. با توکن و آیدی‌های داده شده:

1. ربات را اجرا کنید
2. به آدرس ربات در تلگرام بروید
3. `/start` را ارسال کنید
4. از پنل ادمین استفاده کنید

## 🆘 نیاز به کمک؟

در صورت بروز مشکل:
1. لاگ‌ها را بررسی کنید
2. مستندات aiogram را مطالعه کنید: https://docs.aiogram.dev
3. در گروه‌های تلگرامی Python/Bot Development سوال بپرسید

موفق باشید! 🚀