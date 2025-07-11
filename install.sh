#!/bin/bash

# Telegram Downloader Bot - Enhanced Installation Script
# Automates the installation and initial configuration of the bot.

# --- Globals ---
# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Defaults
PROJECT_DIR_NAME="telegram-downloader-bot" # Assuming the script is run from within or alongside this dir
VENV_DIR="venv"
SERVICE_NAME="telegram_downloader_bot"
MIN_PYTHON_VERSION_MAJOR=3
MIN_PYTHON_VERSION_MINOR=8
REQUIREMENTS_FILE="requirements.txt"
ENV_EXAMPLE_FILE=".env.example"
ENV_FILE=".env"

# User inputs (will be populated by get_user_inputs)
BOT_TOKEN=""
ADMIN_IDS=""
INSTALL_SYSTEMD_SERVICE=true
SETUP_CRONJOBS=true

# --- Helper Functions ---
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

prompt_yes_no() {
    local prompt_message=$1
    local default_yes=$2 # true for yes, false for no

    while true; do
        if [ "$default_yes" = true ]; then
            read -r -p "$prompt_message [Y/n]: " response
            response=${response:-Y} # Default to Yes
        else
            read -r -p "$prompt_message [y/N]: " response
            response=${response:-N} # Default to No
        fi

        case "$response" in
            [yY][eE][sS]|[yY])
                return 0 # Yes
                ;;
            [nN][oO]|[nN])
                return 1 # No
                ;;
            *)
                print_warning "Invalid input. Please enter 'y' or 'n'."
                ;;
        esac
    done
}

check_command() {
    local cmd=$1
    if ! command -v "$cmd" &> /dev/null; then
        print_error "$cmd command not found. Please install it and try again."
        # Optionally, attempt to install:
        # if prompt_yes_no "Attempt to install $cmd?"; then
        #     sudo apt update && sudo apt install -y <package_providing_cmd>
        # else
        #     exit 1
        # fi
        exit 1
    fi
}

check_python_version() {
    print_info "Checking Python version..."
    local current_major=$(python3 -c 'import sys; print(sys.version_info[0])')
    local current_minor=$(python3 -c 'import sys; print(sys.version_info[1])')

    if [ "$current_major" -lt "$MIN_PYTHON_VERSION_MAJOR" ] || \
       ( [ "$current_major" -eq "$MIN_PYTHON_VERSION_MAJOR" ] && \
         [ "$current_minor" -lt "$MIN_PYTHON_VERSION_MINOR" ] ); then
        print_error "Python $MIN_PYTHON_VERSION_MAJOR.$MIN_PYTHON_VERSION_MINOR or higher is required."
        print_error "Found: Python $current_major.$current_minor"
        exit 1
    fi
    print_success "Python version $current_major.$current_minor is compatible."
}

validate_telegram_token() {
    local token=$1
    # Basic validation: format like 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
    if [[ "$token" =~ ^[0-9]+:[a-zA-Z0-9_-]+$ ]]; then
        return 0
    else
        return 1
    fi
}

validate_telegram_id() {
    local id=$1
    # Basic validation: should be a number
    if [[ "$id" =~ ^[0-9]+$ ]]; then
        return 0
    else
        return 1
    fi
}

# --- Main Installation Functions ---
welcome_message() {
    echo -e "${BLUE}=============================================${NC}"
    echo -e "${BLUE}  Telegram Downloader Bot Installation Script  ${NC}"
    echo -e "${BLUE}=============================================${NC}"
    echo "This script will guide you through the installation process."
    echo ""
}

initial_checks() {
    print_info "Performing initial system checks..."
    if [ "$EUID" -eq 0 ]; then
        print_error "This script should not be run as root. Please run as a regular user."
        exit 1
    fi

    check_command "git"
    check_command "python3"
    check_command "pip3"
    check_python_version
    print_success "Initial checks passed."
}

get_user_inputs() {
    print_info "Collecting required information..."

    while true; do
        read -s -p "Enter your Telegram Bot Token: " BOT_TOKEN
        echo # Newline after secret input
        if validate_telegram_token "$BOT_TOKEN"; then
            break
        else
            print_warning "Invalid Telegram Bot Token format. It should look like '123456:ABC-DEF...'. Please try again."
        fi
    done

    while true; do
        read -p "Enter your Telegram Admin User ID(s) (comma-separated for multiple): " ADMIN_IDS
        local all_valid=true
        IFS=',' read -ra ids_array <<< "$ADMIN_IDS"
        if [ ${#ids_array[@]} -eq 0 ]; then
            print_warning "Admin ID cannot be empty. Please try again."
            all_valid=false
        else
            for id in "${ids_array[@]}"; do
                if ! validate_telegram_id "$id"; then
                    print_warning "Invalid Telegram User ID: '$id'. It should be a number. Please try again."
                    all_valid=false
                    break
                fi
            done
        fi
        if [ "$all_valid" = true ]; then
            break
        fi
    done

    if ! prompt_yes_no "Install as a systemd service for automatic startup?" true; then
        INSTALL_SYSTEMD_SERVICE=false
    fi

    if ! prompt_yes_no "Setup cronjobs for monitoring and backup?" true; then
        SETUP_CRONJOBS=false
    fi
    print_success "User inputs collected."
}

setup_project_directory() {
    print_info "Setting up project directory..."
    # Assuming the script is inside or next to the project directory.
    # If the script is intended to be run from anywhere, cloning logic would be here.
    # For now, we assume the project files (requirements.txt, .env.example) are accessible.
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        print_error "$REQUIREMENTS_FILE not found. Make sure you are in the project directory."
        # Example cloning logic (if needed):
        # print_info "Cloning repository..."
        # git clone <repo_url> $PROJECT_DIR_NAME
        # cd $PROJECT_DIR_NAME
        exit 1
    fi
    print_success "Project directory is set up."
}

setup_virtual_environment() {
    print_info "Setting up Python virtual environment..."
    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment '$VENV_DIR' already exists."
        if ! prompt_yes_no "Do you want to recreate it? (this will remove the existing one)" false; then
            print_info "Skipping virtual environment creation."
            return 0
        fi
        rm -rf "$VENV_DIR"
        print_info "Existing virtual environment removed."
    fi
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment '$VENV_DIR' created."
    print_info "Note: To activate it manually in your current shell, run: source $VENV_DIR/bin/activate"
}

install_dependencies() {
    print_info "Installing Python dependencies..."
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment '$VENV_DIR' not found. Please run setup_virtual_environment first."
        exit 1
    fi
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"

    # Attempt to uninstall python-magic-bin, ignore if not found or fails
    print_info "Attempting to uninstall python-magic-bin (for Linux compatibility)..."
    "$VENV_DIR/bin/pip" uninstall -y python-magic-bin > /dev/null 2>&1 || true

    print_success "Python dependencies installed."
}

configure_environment_file() {
    print_info "Configuring environment file ($ENV_FILE)..."
    if [ ! -f "$ENV_EXAMPLE_FILE" ] && [ ! -f "$ENV_FILE" ]; then
        print_warning "$ENV_EXAMPLE_FILE not found. Cannot create $ENV_FILE from template."
        print_warning "A basic $ENV_FILE will be created. You may need to add other configurations manually."
        touch "$ENV_FILE"
    elif [ ! -f "$ENV_FILE" ]; then
        cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
        print_info "$ENV_FILE created from $ENV_EXAMPLE_FILE."
    else
        print_warning "$ENV_FILE already exists."
        if ! prompt_yes_no "Do you want to overwrite BOT_TOKEN and ADMIN_IDS in the existing $ENV_FILE?" true; then
            print_info "Skipping $ENV_FILE configuration."
            return 0
        fi
    fi

    # Update BOT_TOKEN
    if grep -q "^BOT_TOKEN=" "$ENV_FILE"; then
        sed -i "s|^BOT_TOKEN=.*|BOT_TOKEN=$BOT_TOKEN|" "$ENV_FILE"
    else
        echo "BOT_TOKEN=$BOT_TOKEN" >> "$ENV_FILE"
    fi

    # Update ADMIN_IDS
    if grep -q "^ADMIN_IDS=" "$ENV_FILE"; then
        sed -i "s|^ADMIN_IDS=.*|ADMIN_IDS=$ADMIN_IDS|" "$ENV_FILE"
    else
        echo "ADMIN_IDS=$ADMIN_IDS" >> "$ENV_FILE"
    fi

    print_success "$ENV_FILE configured."
}

create_required_directories() {
    print_info "Creating required directories..."
    mkdir -p downloads uploads temp logs backups
    chmod 755 downloads uploads temp logs backups # Or more restrictive if needed
    print_success "Required directories created."
}

setup_systemd_service() {
    if [ "$INSTALL_SYSTEMD_SERVICE" = false ]; then
        print_info "Skipping systemd service setup as per user request."
        return 0
    fi

    print_info "Setting up systemd service ($SERVICE_NAME)..."
    local current_user=$(whoami)
    local project_path=$(pwd)
    local service_file_content="[Unit]
Description=Telegram Downloader Bot Service
After=network.target

[Service]
Type=simple
User=$current_user
Group=$current_user
WorkingDirectory=$project_path
EnvironmentFile=$project_path/$ENV_FILE
ExecStart=$project_path/$VENV_DIR/bin/python $project_path/telegram_downloader_bot.py
Restart=always
RestartSec=10
StandardOutput=append:$project_path/logs/bot.log
StandardError=append:$project_path/logs/error.log

[Install]
WantedBy=multi-user.target"

    echo "$service_file_content" | sudo tee "/etc/systemd/system/$SERVICE_NAME.service" > /dev/null

    print_info "Reloading systemd daemon..."
    sudo systemctl daemon-reload
    print_info "Enabling $SERVICE_NAME service to start on boot..."
    sudo systemctl enable "$SERVICE_NAME.service"
    print_info "Starting $SERVICE_NAME service..."
    sudo systemctl start "$SERVICE_NAME.service"

    # Give it a moment to start
    sleep 3

    if sudo systemctl is-active --quiet "$SERVICE_NAME.service"; then
        print_success "$SERVICE_NAME service is active and running."
    else
        print_error "$SERVICE_NAME service failed to start. Check logs for details:"
        print_error "sudo journalctl -u $SERVICE_NAME -n 50 --no-pager"
        print_error "cat $project_path/logs/error.log"
    fi
}

setup_cron_jobs() {
    if [ "$SETUP_CRONJOBS" = false ]; then
        print_info "Skipping cronjob setup as per user request."
        return 0
    fi

    print_info "Setting up cronjobs for monitoring and backup..."
    local project_path=$(pwd)

    # --- Monitor Script ---
    local monitor_script_path="$project_path/monitor.sh"
    cat > "$monitor_script_path" << EOF
#!/bin/bash
# Monitor script for Telegram Downloader Bot

# Source environment variables if .env exists and SERVICE_NAME is set
if [ -f "$project_path/$ENV_FILE" ]; then
    source "$project_path/$ENV_FILE"
fi

SERVICE_NAME_TO_CHECK="${SERVICE_NAME:-telegram_downloader_bot}" # Use default if not in .env
LOG_FILE="$project_path/logs/monitor.log"
ADMIN_ID_FOR_NOTIF=\$(echo "\$ADMIN_IDS" | cut -d',' -f1) # Get first admin ID

echo "\$(date): Checking status of \$SERVICE_NAME_TO_CHECK" >> "\$LOG_FILE"

if ! systemctl is-active --quiet "\$SERVICE_NAME_TO_CHECK.service"; then
    echo "\$(date): \$SERVICE_NAME_TO_CHECK is down! Attempting restart..." >> "\$LOG_FILE"
    sudo systemctl restart "\$SERVICE_NAME_TO_CHECK.service"
    sleep 5 # Wait for restart attempt

    if systemctl is-active --quiet "\$SERVICE_NAME_TO_CHECK.service"; then
        RESTART_MSG="\$(date): \$SERVICE_NAME_TO_CHECK was down and has been restarted successfully."
    else
        RESTART_MSG="\$(date): \$SERVICE_NAME_TO_CHECK is still down after attempting restart. Please check manually."
    fi

    echo "\$RESTART_MSG" >> "\$LOG_FILE"

    # Send Telegram notification if BOT_TOKEN and ADMIN_ID are available
    if [ ! -z "\$BOT_TOKEN" ] && [ ! -z "\$ADMIN_ID_FOR_NOTIF" ]; then
        curl -s -X POST "https://api.telegram.org/bot\$BOT_TOKEN/sendMessage" \
             -d chat_id="\$ADMIN_ID_FOR_NOTIF" \
             -d text="⚠ Telegram Bot Alert: \$RESTART_MSG" \
             --connect-timeout 10 >> "\$LOG_FILE" 2>&1
    fi
else
    echo "\$(date): \$SERVICE_NAME_TO_CHECK is active." >> "\$LOG_FILE"
fi
EOF
    chmod +x "$monitor_script_path"
    print_success "Monitor script created at $monitor_script_path"

    # --- Backup Script ---
    local backup_script_path="$project_path/backup.sh"
    cat > "$backup_script_path" << EOF
#!/bin/bash
# Backup script for Telegram Downloader Bot

BACKUP_DIR="$project_path/backups"
DB_FILE="$project_path/bot_database.db" # Assuming this is the DB name
ENV_FILE_TO_BACKUP="$project_path/$ENV_FILE"
DATE=\$(date +%Y%m%d_%H%M%S)
LOG_FILE="$project_path/logs/backup.log"

echo "\$(date): Starting backup process..." >> "\$LOG_FILE"
mkdir -p "\$BACKUP_DIR"

# Backup database
if [ -f "\$DB_FILE" ]; then
    cp "\$DB_FILE" "\$BACKUP_DIR/db_backup_\$DATE.db"
    echo "\$(date): Database backed up to \$BACKUP_DIR/db_backup_\$DATE.db" >> "\$LOG_FILE"
else
    echo "\$(date): Database file \$DB_FILE not found. Skipping database backup." >> "\$LOG_FILE"
fi

# Backup .env file
if [ -f "\$ENV_FILE_TO_BACKUP" ]; then
    cp "\$ENV_FILE_TO_BACKUP" "\$BACKUP_DIR/env_backup_\$DATE.env"
    echo "\$(date): Environment file backed up to \$BACKUP_DIR/env_backup_\$DATE.env" >> "\$LOG_FILE"
else
    echo "\$(date): Environment file \$ENV_FILE_TO_BACKUP not found. Skipping .env backup." >> "\$LOG_FILE"
fi

# Remove old backups (older than 30 days)
find "\$BACKUP_DIR" -type f -name "*.db" -mtime +30 -exec rm -f {} \;
find "\$BACKUP_DIR" -type f -name "*.env" -mtime +30 -exec rm -f {} \;
echo "\$(date): Old backups (older than 30 days) cleaned up." >> "\$LOG_FILE"
echo "\$(date): Backup process completed." >> "\$LOG_FILE"
EOF
    chmod +x "$backup_script_path"
    print_success "Backup script created at $backup_script_path"

    # --- Add to crontab ---
    # Ensure no duplicate cronjobs are added
    CRON_MONITOR_JOB="*/5 * * * * $monitor_script_path"
    CRON_BACKUP_JOB="0 2 * * * $backup_script_path"

    (crontab -l 2>/dev/null | grep -v -F "$monitor_script_path" | grep -v -F "$backup_script_path"; \
     echo "$CRON_MONITOR_JOB"; \
     echo "$CRON_BACKUP_JOB") | crontab -

    print_success "Cronjobs for monitoring and backup added/updated."
    print_info "Monitor log: $project_path/logs/monitor.log"
    print_info "Backup log: $project_path/logs/backup.log"
}

final_summary() {
    echo ""
    print_success "============================================"
    print_success " Installation Completed Successfully! "
    print_success "============================================"
    echo ""
    print_info "What's next:"
    echo "1. The bot should now be running if you chose to install the systemd service."
    echo "   - Check status: sudo systemctl status $SERVICE_NAME"
    echo "   - Stop service: sudo systemctl stop $SERVICE_NAME"
    echo "   - Start service: sudo systemctl start $SERVICE_NAME"
    echo "   - View logs: sudo journalctl -fu $SERVICE_NAME"
    echo "   - Application logs: cat $(pwd)/logs/bot.log"
    echo ""
    echo "2. If you didn't install the systemd service, you can run the bot manually:"
    echo "   source $VENV_DIR/bin/activate"
    echo "   python telegram_downloader_bot.py"
    echo ""
    echo "3. Test your bot in Telegram by sending commands."
    echo ""
    if [ "$SETUP_CRONJOBS" = true ]; then
        echo "4. Monitoring and backup scripts have been set up via cron."
        echo "   - Monitor script runs every 5 minutes."
        echo "   - Backup script runs daily at 2 AM."
    fi
    echo ""
    print_info "Thank you for using the Telegram Downloader Bot!"
}

# --- Main Execution ---
main() {
    # Ensure script exits if any command fails
    set -e
    # Ensure that commands in a pipeline that fail will cause the script to exit
    set -o pipefail


    welcome_message
    initial_checks
    get_user_inputs
    setup_project_directory # Assumes script is in/near project dir
    setup_virtual_environment
    install_dependencies
    configure_environment_file
    create_required_directories
    setup_systemd_service
    setup_cron_jobs
    final_summary

    # Unset pipefail and errexit if they are not desired for the rest of the shell session
    # (though for a script that exits, this is less critical)
    set +o pipefail
    set +e
}

# Run the main function
main
