# 📦 Installation Guide

This guide provides detailed instructions for installing and configuring the Telegram File Downloader Bot.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Manual Installation](#manual-installation)
4. [Docker Installation](#docker-installation)
5. [Configuration](#configuration)
6. [Running the Bot](#running-the-bot)
7. [Systemd Service](#systemd-service)
8. [Nginx Proxy](#nginx-proxy)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04+ / Debian 10+ / CentOS 8+
- **Python**: 3.8 or higher
- **RAM**: Minimum 1GB (2GB recommended)
- **Storage**: 10GB free space
- **Network**: Stable internet connection

### Required Packages

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    libmagic1 \
    libmagic-dev \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libfreetype6-dev \
    build-essential
```

## Installation Methods

### Method 1: Automated Installation Script (Recommended for Linux)

This script guides you through the process, including dependency installation, virtual environment setup, configuration, and optional systemd service and cronjob setup.

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone https://github.com/yourusername/telegram-downloader-bot.git
    cd telegram-downloader-bot
    ```
2.  **Make the script executable and run it:**
    ```bash
    chmod +x install.sh
    ./install.sh
    ```
    Follow the on-screen prompts. You will be asked for your Bot Token and Admin ID(s).

### Method 2: Manual Installation

See [Manual Installation](#manual-installation) section below.

### Method 3: Docker

See [Docker Installation](#docker-installation) section below.

## Manual Installation

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/telegram-downloader-bot.git
cd telegram-downloader-bot
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# For Linux/Mac only (remove Windows-specific package)
pip uninstall python-magic-bin -y
```

### 4. Create Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

Update the following values:
- `BOT_TOKEN`: Your bot token from @BotFather
- `ADMIN_IDS`: Your Telegram user ID

### 5. Create Required Directories

```bash
# Create directories
mkdir -p downloads uploads temp logs backups

# Set permissions
chmod 755 downloads uploads temp logs backups
```

### 6. Initialize Database

The database will be created automatically on first run.

## Docker Installation

### 1. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Configure Docker

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: telegram-downloader-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./downloads:/app/downloads
      - ./uploads:/app/uploads
      - ./temp:/app/temp
      - ./logs:/app/logs
      - ./backups:/app/backups
      - ./bot_database.db:/app/bot_database.db
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 3. Build and Run

```bash
# Build the image
docker-compose build

# Run the container
docker-compose up -d

# View logs
docker-compose logs -f
```

## Configuration

### Environment Variables

All configuration is done through environment variables in the `.env` file.

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` |
| `ADMIN_IDS` | Admin user IDs (comma-separated) | `123456789,987654321` |

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_FILE_SIZE` | Maximum file size in bytes | `2147483648` (2GB) |
| `DEFAULT_DAILY_LIMIT` | Daily download limit | `10` |
| `DOWNLOAD_TIMEOUT` | Download timeout in seconds | `3600` |
| `DATABASE_PATH` | Database file path | `bot_database.db` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Advanced Configuration

For advanced configuration options, see the `.env.example` file.

## Running the Bot

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Run the bot
python telegram_bot.py
```

### Production Mode

```bash
# Using screen
screen -S bot
python telegram_bot.py
# Detach: Ctrl+A, D

# Using nohup
nohup python telegram_bot.py > bot.log 2>&1 &

# Using PM2 (recommended for Node.js projects, but can manage Python scripts)
# Ensure you have Node.js and npm installed
npm install -g pm2
pm2 start telegram_downloader_bot.py --name telegram-downloader-bot --interpreter python3
pm2 save
sudo pm2 startup # This will provide a command to run to enable startup script
# For more details on PM2: https://pm2.keymetrics.io/docs/usage/quick-start/

### Systemd Service (Recommended for Linux Servers)

The automated `install.sh` script can help you set this up.
If you chose not to use the script or want to do it manually:

1.  **Create a service file:**
    Create a file named `telegram_downloader_bot.service` (or your preferred name) in `/etc/systemd/system/` with the following content. Adjust paths and username as necessary.

    ```ini
    [Unit]
    Description=Telegram Downloader Bot Service
    After=network.target

    [Service]
    Type=simple
    User=your_username # Replace with the user running the bot
    Group=your_group   # Replace with the group of the user
    WorkingDirectory=/path/to/your/telegram-downloader-bot # Replace with your project path
    EnvironmentFile=/path/to/your/telegram-downloader-bot/.env # Path to your .env file
    ExecStart=/path/to/your/telegram-downloader-bot/venv/bin/python /path/to/your/telegram-downloader-bot/telegram_downloader_bot.py
    Restart=always
    RestartSec=10
    StandardOutput=append:/path/to/your/telegram-downloader-bot/logs/bot.log
    StandardError=append:/path/to/your/telegram-downloader-bot/logs/error.log

    [Install]
    WantedBy=multi-user.target
    ```

2.  **Reload systemd, enable and start the service:**
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable telegram_downloader_bot.service
    sudo systemctl start telegram_downloader_bot.service
    ```

3.  **Check status:**
    ```bash
    sudo systemctl status telegram_downloader_bot.service
    # View logs
    sudo journalctl -fu telegram_downloader_bot.service
    ```