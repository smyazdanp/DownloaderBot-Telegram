# 🤖 Telegram File Downloader Bot

<div align="center">

![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)
![Aiogram](https://img.shields.io/badge/aiogram-v3.7.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

A powerful and professional Telegram bot for downloading files with advanced features and admin panel.

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Admin Panel](#admin-panel) • [Contributing](#contributing)

</div>

---

## ✨ Features

### 📥 Download Capabilities
- ✅ Download files up to 2GB (Telegram limit)
- ✅ Automatic file splitting for larger files
- ✅ Resume support for interrupted downloads
- ✅ Real-time progress tracking with speed and ETA
- ✅ Support for all file types
- ✅ Multiple send formats (photo, video, audio, document)

### 👥 User Management
- ✅ Daily download limits
- ✅ VIP system with unlimited downloads
- ✅ User statistics and activity tracking
- ✅ Ban/unban functionality
- ✅ Personal usage charts

### 🔧 Admin Panel
- ✅ Comprehensive statistics dashboard
- ✅ 14-day activity charts
- ✅ User management interface
- ✅ File upload with unique codes
- ✅ System settings control
- ✅ Broadcast messaging
- ✅ Automatic cleanup

### 🛡️ Security & Performance
- ✅ SQLite database with transactions
- ✅ Rate limiting protection
- ✅ Error handling and retry logic
- ✅ Automatic backup system
- ✅ Detailed logging

## 📋 Requirements

- Python 3.8+
- Ubuntu 20.04+ (or any Linux distribution)
- 1GB RAM minimum
- 10GB free disk space

## 🚀 Installation

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/telegram-downloader-bot.git
cd telegram-downloader-bot
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt

# For Linux/Mac only:
pip uninstall python-magic-bin -y
```

4. **Configure the bot**
```bash
# Create .env file
cp .env.example .env

# Edit .env with your values
nano .env
```

5. **Run the bot**
```bash
python telegram_bot.py
```

### Detailed Installation

For complete setup instructions including systemd service, monitoring, and optimization, see [INSTALL.md](INSTALL.md).

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Bot Configuration
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321

# Optional Settings
MAX_FILE_SIZE=2147483648  # 2GB in bytes
DEFAULT_DAILY_LIMIT=10
DOWNLOAD_TIMEOUT=3600
```

### Getting Bot Token

1. Open [@BotFather](https://t.me/botfather) in Telegram
2. Send `/newbot` command
3. Choose a name for your bot
4. Choose a username (must end with 'bot')
5. Copy the token provided

### Getting Your Telegram ID

1. Open [@userinfobot](https://t.me/userinfobot) in Telegram
2. Send any message
3. Copy your numeric ID

## 📱 Usage

### For Users

1. **Start the bot**
   ```
   /start - Initialize bot and see your status
   ```

2. **Download a file**
   - Send any direct download link
   - Choose send format when prompted
   - Receive the file

3. **Check your stats**
   ```
   /mystats - View your download statistics
   ```

4. **Download with code**
   ```
   /dl CODE - Download file using admin-provided code
   ```

### For Admins

1. **Access admin panel**
   ```
   /admin - Open admin control panel
   ```

2. **Admin features**:
   - 📊 View system statistics
   - 📈 Generate activity charts
   - 👥 Manage users (VIP, ban, limits)
   - ⚙️ Configure system settings
   - 📤 Upload files with unique codes
   - 🗑️ Clean up old files
   - 📢 Broadcast messages

## 📊 Admin Panel

### Statistics Dashboard
- Total users and downloads
- Daily active users
- Storage usage
- Download trends

### User Management
- Search and filter users
- Grant/revoke VIP status
- Set custom limits
- Ban/unban users

### System Settings
- Toggle download functionality
- Set global daily limits
- Enable/disable maintenance mode
- Configure welcome messages

## 🗂️ Project Structure

```
telegram-downloader-bot/
├── telegram_bot.py      # Main bot code
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore         # Git ignore file
├── README.md          # This file
├── LICENSE            # MIT License
├── INSTALL.md         # Detailed installation guide
├── CONTRIBUTING.md    # Contribution guidelines
├── docker-compose.yml # Docker configuration
├── Dockerfile         # Docker image
└── scripts/           # Utility scripts
    ├── backup.sh      # Backup script
    ├── monitor.sh     # Monitoring script
    └── setup.sh       # Initial setup script
```

## 🐳 Docker Support

### Using Docker Compose

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

See [docker-compose.yml](docker-compose.yml) for configuration.

## 📈 Performance

- Handles 100+ concurrent downloads
- Average response time: <200ms
- Memory usage: ~100-200MB
- Supports files up to 2GB

## 🛡️ Security

- Input validation on all user inputs
- Rate limiting to prevent abuse
- Secure file handling
- Admin-only command protection
- Automatic cleanup of temporary files

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repo
git clone https://github.com/yourusername/telegram-downloader-bot.git

# Create branch
git checkout -b feature/your-feature

# Make changes and test
python telegram_bot.py

# Commit and push
git add .
git commit -m "Add your feature"
git push origin feature/your-feature
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot API framework
- [aiohttp](https://github.com/aio-libs/aiohttp) - Async HTTP client
- [python-magic](https://github.com/ahupp/python-magic) - File type detection

## 📞 Support

- 📧 Email: your.email@example.com
- 💬 Telegram: [@yourusername](https://t.me/yourusername)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/telegram-downloader-bot/issues)

## 📊 Stats

![GitHub stars](https://img.shields.io/github/stars/yourusername/telegram-downloader-bot?style=social)
![GitHub forks](https://img.shields.io/github/forks/yourusername/telegram-downloader-bot?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/yourusername/telegram-downloader-bot?style=social)

---

<div align="center">
Made with ❤️ by <a href="https://github.com/yourusername">Your Name</a>
</div>