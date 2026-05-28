#!/bin/bash

# ============================================
# iPBotS - V2Ray Shop Bot Installer & Manager
# © iPmart Network (آی‌پیمارت نتورک)
# GitHub: https://github.com/iPmartNetwork/iPBotS
# Tested on Ubuntu 20.04 / 22.04 / 24.04
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Variables
INSTALL_DIR="/opt/iPBotS"
REPO_URL="https://github.com/iPmartNetwork/iPBotS.git"
BRANCH="main"
NGINX_CONF="/etc/nginx/sites-available/ipbots"
NGINX_ENABLED="/etc/nginx/sites-enabled/ipbots"
VERSION="1.0.0"

# ============================================
# Helper Functions
# ============================================

print_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║                                                   ║"
    echo "║     🚀 iPBotS - V2Ray Shop Bot                   ║"
    echo "║     © iPmart Network                              ║"
    echo "║     Version: ${VERSION}                               ║"
    echo "║                                                   ║"
    echo "║     github.com/iPmartNetwork/iPBotS               ║"
    echo "║                                                   ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

success() { echo -e "  ${GREEN}✓ $1${NC}"; }
warning() { echo -e "  ${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "  ${RED}❌ $1${NC}"; }
info() { echo -e "  ${CYAN}ℹ️  $1${NC}"; }

check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "Please run as root: sudo bash install.sh"
        exit 1
    fi
}

check_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
    else
        error "Cannot detect OS"
        exit 1
    fi

    if [[ "$OS" != "ubuntu" && "$OS" != "debian" ]]; then
        warning "This script is optimized for Ubuntu/Debian. Your OS: $OS"
        read -p "  Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

check_docker() {
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
        success "Docker found: v$DOCKER_VERSION"
        return 0
    fi
    return 1
}

check_running() {
    if [ -f "$INSTALL_DIR/docker-compose.yml" ]; then
        if docker-compose -f "$INSTALL_DIR/docker-compose.yml" ps 2>/dev/null | grep -q "Up"; then
            return 0
        fi
    fi
    return 1
}

wait_for_healthy() {
    local service=$1
    local max_wait=$2
    local count=0

    while [ $count -lt $max_wait ]; do
        if docker-compose -f "$INSTALL_DIR/docker-compose.yml" ps "$service" 2>/dev/null | grep -q "healthy\|Up"; then
            return 0
        fi
        sleep 2
        count=$((count + 2))
    done
    return 1
}

# ============================================
# Installation
# ============================================

install_dependencies() {
    print_step "[1/8] Installing system dependencies"

    apt-get update -qq > /dev/null 2>&1
    apt-get install -y -qq \
        curl \
        wget \
        git \
        openssl \
        certbot \
        nginx \
        ufw \
        jq \
        > /dev/null 2>&1

    success "System packages installed"

    # Install Docker if not present
    if ! check_docker; then
        info "Installing Docker..."
        curl -fsSL https://get.docker.com | sh > /dev/null 2>&1
        systemctl enable docker > /dev/null 2>&1
        systemctl start docker > /dev/null 2>&1
        success "Docker installed"
    fi

    # Install docker-compose if not present
    if ! command -v docker-compose &> /dev/null; then
        info "Installing Docker Compose..."
        COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | jq -r .tag_name)
        curl -fsSL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        success "Docker Compose installed"
    else
        success "Docker Compose found"
    fi
}

setup_project() {
    print_step "[2/8] Setting up project"

    # Backup existing .env if upgrading
    if [ -f "$INSTALL_DIR/.env" ]; then
        cp "$INSTALL_DIR/.env" "/tmp/ipbots-env-backup-$(date +%s)"
        warning "Existing .env backed up to /tmp/"
    fi

    # Clone or update
    if [ -d "$INSTALL_DIR/.git" ]; then
        info "Updating existing installation..."
        cd "$INSTALL_DIR"
        git fetch origin > /dev/null 2>&1
        git reset --hard "origin/$BRANCH" > /dev/null 2>&1
        success "Repository updated"
    else
        rm -rf "$INSTALL_DIR" 2>/dev/null || true
        git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR" > /dev/null 2>&1
        success "Repository cloned"
    fi

    cd "$INSTALL_DIR"

    # Create required directories
    mkdir -p backups logs
    chmod 755 backups logs

    success "Project directory ready: $INSTALL_DIR"
}

configure_env() {
    print_step "[3/8] Configuring environment"

    cd "$INSTALL_DIR"

    if [ -f ".env" ] && [ "$1" != "force" ]; then
        warning ".env already exists. Keeping current config."
        info "To reconfigure: sudo bash install.sh config"
        return
    fi

    cp .env.example .env

    echo -e "${CYAN}  Please provide the following information:${NC}\n"

    # Bot Token
    while true; do
        read -p "  🤖 Telegram Bot Token: " BOT_TOKEN
        if [[ "$BOT_TOKEN" =~ ^[0-9]+:.+$ ]]; then
            break
        fi
        error "Invalid token format. Should be like: 123456789:ABCdefGHI..."
    done

    # Admin ID
    while true; do
        read -p "  👤 Admin Telegram ID (numeric): " ADMIN_ID
        if [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; then
            break
        fi
        error "Must be a number. Get it from @userinfobot"
    done

    # Domain
    read -p "  🌐 Domain (e.g., bot.example.com, or press Enter for polling mode): " DOMAIN

    # Database password
    DB_PASS=$(openssl rand -base64 24 | tr -d '/+=' | head -c 20)
    info "Generated DB password: $DB_PASS"

    # Secret key
    SECRET_KEY=$(openssl rand -hex 32)

    # Payment
    read -p "  💳 ZarinPal Merchant ID (Enter to skip): " ZARINPAL_ID
    read -p "  🪙 NowPayments API Key (Enter to skip): " NOWPAY_KEY

    # Bot username
    read -p "  📱 Bot username (without @): " BOT_USERNAME

    # Apply to .env
    sed -i "s|BOT_TOKEN=.*|BOT_TOKEN=$BOT_TOKEN|" .env
    sed -i "s|ADMIN_IDS=.*|ADMIN_IDS=$ADMIN_ID|" .env
    sed -i "s|APP_SECRET_KEY=.*|APP_SECRET_KEY=$SECRET_KEY|" .env
    sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASS|" .env
    sed -i "s|BOT_USERNAME=.*|BOT_USERNAME=$BOT_USERNAME|" .env

    if [ -n "$DOMAIN" ]; then
        sed -i "s|WEBHOOK_ENABLED=.*|WEBHOOK_ENABLED=true|" .env
        sed -i "s|WEBHOOK_HOST=.*|WEBHOOK_HOST=https://$DOMAIN|" .env
        sed -i "s|ZARINPAL_CALLBACK_URL=.*|ZARINPAL_CALLBACK_URL=https://$DOMAIN/api/payment/zarinpal/callback|" .env
        sed -i "s|NOWPAYMENTS_CALLBACK_URL=.*|NOWPAYMENTS_CALLBACK_URL=https://$DOMAIN/api/payment/nowpayments/callback|" .env
        sed -i "s|CRYPTOMUS_CALLBACK_URL=.*|CRYPTOMUS_CALLBACK_URL=https://$DOMAIN/api/payment/cryptomus/callback|" .env
    else
        sed -i "s|WEBHOOK_ENABLED=.*|WEBHOOK_ENABLED=false|" .env
        info "Polling mode enabled (no domain needed)"
    fi

    if [ -n "$ZARINPAL_ID" ]; then
        sed -i "s|ZARINPAL_MERCHANT_ID=.*|ZARINPAL_MERCHANT_ID=$ZARINPAL_ID|" .env
    fi

    if [ -n "$NOWPAY_KEY" ]; then
        sed -i "s|NOWPAYMENTS_API_KEY=.*|NOWPAYMENTS_API_KEY=$NOWPAY_KEY|" .env
    fi

    # Set backup chat to admin
    sed -i "s|BACKUP_CHAT_ID=.*|BACKUP_CHAT_ID=$ADMIN_ID|" .env

    chmod 600 .env
    success "Environment configured"
}

setup_ssl() {
    print_step "[4/8] Setting up SSL"

    if [ -z "$DOMAIN" ]; then
        info "No domain configured. Skipping SSL."
        return
    fi

    # Stop nginx temporarily for standalone cert
    systemctl stop nginx 2>/dev/null || true

    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        success "SSL certificate already exists"
    else
        info "Obtaining SSL certificate for $DOMAIN..."
        certbot certonly --standalone \
            -d "$DOMAIN" \
            --non-interactive \
            --agree-tos \
            --email "admin@$DOMAIN" \
            --preferred-challenges http 2>/dev/null && {
            success "SSL certificate obtained"
        } || {
            warning "SSL failed. Make sure:"
            warning "  1. Domain $DOMAIN points to this server"
            warning "  2. Port 80 is open"
            warning "  You can retry later: certbot certonly --standalone -d $DOMAIN"
        }
    fi
}

setup_nginx() {
    print_step "[5/8] Configuring Nginx reverse proxy"

    if [ -z "$DOMAIN" ]; then
        info "No domain. Skipping Nginx."
        return
    fi

    # Create Nginx config
    cat > "$NGINX_CONF" << NGINX_EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Telegram Webhook
    location /api/telegram/webhook {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Payment callbacks
    location /api/payment/ {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebApp API
    location /api/webapp/ {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Mini App static files
    location /webapp {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host \$host;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8443;
    }

    # Block everything else
    location / {
        return 444;
    }
}
NGINX_EOF

    # Enable site
    ln -sf "$NGINX_CONF" "$NGINX_ENABLED" 2>/dev/null
    rm -f /etc/nginx/sites-enabled/default 2>/dev/null

    # Test and restart
    nginx -t > /dev/null 2>&1 && {
        systemctl enable nginx > /dev/null 2>&1
        systemctl restart nginx
        success "Nginx configured and running"
    } || {
        error "Nginx config test failed"
    }
}

setup_firewall() {
    print_step "[6/8] Configuring firewall"

    ufw --force reset > /dev/null 2>&1
    ufw default deny incoming > /dev/null 2>&1
    ufw default allow outgoing > /dev/null 2>&1
    ufw allow 22/tcp > /dev/null 2>&1    # SSH
    ufw allow 80/tcp > /dev/null 2>&1    # HTTP
    ufw allow 443/tcp > /dev/null 2>&1   # HTTPS
    ufw --force enable > /dev/null 2>&1

    success "Firewall enabled (SSH, HTTP, HTTPS)"
}

start_services() {
    print_step "[7/8] Starting services"

    cd "$INSTALL_DIR"

    # Stop if running
    docker-compose down 2>/dev/null || true

    # Build and start
    info "Building containers (this may take a few minutes)..."
    docker-compose up -d --build 2>&1 | tail -5

    # Wait for services
    info "Waiting for services to be ready..."

    # Wait for PostgreSQL
    local pg_ready=false
    for i in $(seq 1 30); do
        if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
            pg_ready=true
            break
        fi
        sleep 2
    done

    if [ "$pg_ready" = true ]; then
        success "PostgreSQL ready"
    else
        warning "PostgreSQL may still be starting..."
    fi

    # Wait for Redis
    if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        success "Redis ready"
    fi

    # Wait for bot
    sleep 5
    if docker-compose ps bot 2>/dev/null | grep -q "Up"; then
        success "Bot container running"
    else
        warning "Bot may still be starting. Check: docker-compose logs bot"
    fi

    # Run seed data
    info "Seeding database with initial data..."
    docker-compose exec -T bot python -m core.database.seed 2>/dev/null && {
        success "Database seeded (categories, plans, configs)"
    } || {
        warning "Seed may have already been applied or failed. Check logs."
    }

    success "All services started"
}

setup_webhook() {
    print_step "[8/8] Finalizing"

    cd "$INSTALL_DIR"

    # Source .env to get variables
    source .env 2>/dev/null || true

    if [ "$WEBHOOK_ENABLED" = "true" ] && [ -n "$DOMAIN" ]; then
        sleep 3
        WEBHOOK_URL="https://$DOMAIN/api/telegram/webhook"
        info "Setting webhook: $WEBHOOK_URL"

        RESULT=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook?url=${WEBHOOK_URL}&drop_pending_updates=true")

        if echo "$RESULT" | jq -r '.ok' 2>/dev/null | grep -q "true"; then
            success "Webhook configured"
        else
            warning "Webhook setup failed. Error: $(echo $RESULT | jq -r '.description' 2>/dev/null)"
            info "Set manually: https://api.telegram.org/bot<TOKEN>/setWebhook?url=$WEBHOOK_URL"
        fi
    else
        info "Polling mode - no webhook needed"
    fi

    # Health check
    sleep 2
    if curl -s "http://127.0.0.1:8443/health" 2>/dev/null | grep -q "ok"; then
        success "Health check passed ✓"
    else
        info "Health endpoint not responding yet (may need more time)"
    fi

    # Setup auto-renewal for SSL
    if [ -n "$DOMAIN" ]; then
        (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | sort -u | crontab -
        success "SSL auto-renewal configured"
    fi

    # Setup auto-start on reboot
    (crontab -l 2>/dev/null; echo "@reboot cd $INSTALL_DIR && docker-compose up -d") | sort -u | crontab -
    success "Auto-start on reboot configured"
}

# ============================================
# Management Functions
# ============================================

do_install() {
    print_banner
    check_root
    check_os

    echo -e "${GREEN}  Starting fresh installation...${NC}\n"

    install_dependencies
    setup_project
    configure_env
    setup_ssl
    setup_nginx
    setup_firewall
    start_services
    setup_webhook

    # Final summary
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════╗"
    echo "║                                                   ║"
    echo "║     ✅ Installation Complete!                     ║"
    echo "║     © iPmart Network                              ║"
    echo "║                                                   ║"
    echo "╚═══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}  📁 Directory: $INSTALL_DIR${NC}"
    echo -e "${GREEN}  📝 Config: $INSTALL_DIR/.env${NC}"
    if [ -n "$DOMAIN" ]; then
        echo -e "${GREEN}  🌐 WebApp: https://$DOMAIN/webapp${NC}"
    fi
    echo ""
    echo -e "${YELLOW}  Quick commands:${NC}"
    echo "    ipbots status    - Check status"
    echo "    ipbots logs      - View logs"
    echo "    ipbots restart   - Restart bot"
    echo "    ipbots update    - Update to latest"
    echo "    ipbots backup    - Manual backup"
    echo ""
    echo -e "${CYAN}  🤖 Send /start to your bot to begin!${NC}"
    echo ""
}

do_update() {
    print_banner
    check_root
    echo -e "${BLUE}  Updating iPBotS...${NC}\n"

    cd "$INSTALL_DIR"

    # Backup .env
    cp .env /tmp/ipbots-env-backup

    # Pull latest
    git fetch origin > /dev/null 2>&1
    git reset --hard "origin/$BRANCH" > /dev/null 2>&1
    success "Code updated"

    # Restore .env
    cp /tmp/ipbots-env-backup .env
    success ".env preserved"

    # Rebuild
    docker-compose up -d --build 2>&1 | tail -3
    success "Containers rebuilt"

    # Run migrations
    docker-compose exec -T bot python -c "
import asyncio
from core.database.engine import create_tables
asyncio.run(create_tables())
print('Tables updated')
" 2>/dev/null && success "Database updated" || warning "DB update skipped"

    echo ""
    success "Update complete! Version: $VERSION"
    echo ""
}

do_uninstall() {
    print_banner
    check_root

    echo -e "${RED}  ⚠️  This will remove iPBotS completely!${NC}"
    echo -e "${RED}  Database and backups will be DELETED.${NC}\n"
    read -p "  Are you sure? Type 'YES' to confirm: " CONFIRM

    if [ "$CONFIRM" != "YES" ]; then
        info "Cancelled."
        exit 0
    fi

    cd "$INSTALL_DIR" 2>/dev/null || true

    # Stop containers
    docker-compose down -v 2>/dev/null || true
    success "Containers stopped and volumes removed"

    # Remove nginx config
    rm -f "$NGINX_CONF" "$NGINX_ENABLED" 2>/dev/null
    systemctl reload nginx 2>/dev/null || true
    success "Nginx config removed"

    # Remove project
    rm -rf "$INSTALL_DIR"
    success "Project directory removed"

    # Remove CLI command
    rm -f /usr/local/bin/ipbots 2>/dev/null

    echo ""
    success "iPBotS has been completely removed."
    echo ""
}

do_status() {
    print_banner
    echo -e "${BOLD}  Service Status:${NC}\n"

    cd "$INSTALL_DIR" 2>/dev/null || {
        error "iPBotS not installed at $INSTALL_DIR"
        exit 1
    }

    # Docker status
    echo -e "  ${CYAN}Container Status:${NC}"
    docker-compose ps 2>/dev/null | tail -n +2 | while read line; do
        if echo "$line" | grep -q "Up"; then
            echo -e "    ${GREEN}●${NC} $line"
        else
            echo -e "    ${RED}●${NC} $line"
        fi
    done

    echo ""

    # Health check
    echo -e "  ${CYAN}Health Check:${NC}"
    if curl -s "http://127.0.0.1:8443/health" 2>/dev/null | grep -q "ok"; then
        echo -e "    ${GREEN}● API: Healthy${NC}"
    else
        echo -e "    ${RED}● API: Not responding${NC}"
    fi

    # Disk usage
    echo ""
    echo -e "  ${CYAN}Disk Usage:${NC}"
    echo -e "    $(du -sh $INSTALL_DIR 2>/dev/null | awk '{print $1}') total"

    # Database size
    DB_SIZE=$(docker-compose exec -T postgres psql -U postgres -d v2ray_shop -t -c "SELECT pg_size_pretty(pg_database_size('v2ray_shop'));" 2>/dev/null | tr -d ' ')
    if [ -n "$DB_SIZE" ]; then
        echo -e "    ${DB_SIZE} database"
    fi

    echo ""
}

do_logs() {
    cd "$INSTALL_DIR" 2>/dev/null || {
        error "iPBotS not installed"
        exit 1
    }

    local service="${1:-bot}"
    docker-compose logs -f --tail=50 "$service"
}

do_restart() {
    cd "$INSTALL_DIR" 2>/dev/null || {
        error "iPBotS not installed"
        exit 1
    }

    info "Restarting services..."
    docker-compose restart
    success "Services restarted"
}

do_stop() {
    cd "$INSTALL_DIR" 2>/dev/null || {
        error "iPBotS not installed"
        exit 1
    }

    docker-compose down
    success "Services stopped"
}

do_backup() {
    cd "$INSTALL_DIR" 2>/dev/null || {
        error "iPBotS not installed"
        exit 1
    }

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$INSTALL_DIR/backups/backup_${TIMESTAMP}.sql"

    info "Creating backup..."
    docker-compose exec -T postgres pg_dump -U postgres v2ray_shop > "$BACKUP_FILE" 2>/dev/null && {
        success "Backup created: $BACKUP_FILE"
        echo -e "    Size: $(du -h $BACKUP_FILE | awk '{print $1}')"
    } || {
        error "Backup failed"
    }
}

do_config() {
    cd "$INSTALL_DIR" 2>/dev/null || {
        error "iPBotS not installed"
        exit 1
    }

    configure_env "force"
    info "Restart required. Run: ipbots restart"
}

do_seed() {
    cd "$INSTALL_DIR" 2>/dev/null || {
        error "iPBotS not installed"
        exit 1
    }

    info "Seeding database..."
    docker-compose exec -T bot python -m core.database.seed
}

# ============================================
# CLI Command Installation
# ============================================

install_cli() {
    # Create global 'ipbots' command
    cat > /usr/local/bin/ipbots << 'CLI_EOF'
#!/bin/bash
INSTALL_DIR="/opt/iPBotS"
SCRIPT="$INSTALL_DIR/install.sh"

if [ ! -f "$SCRIPT" ]; then
    echo "iPBotS not installed. Run: sudo bash install.sh"
    exit 1
fi

sudo bash "$SCRIPT" "$@"
CLI_EOF

    chmod +x /usr/local/bin/ipbots
}

# ============================================
# Main Menu
# ============================================

show_menu() {
    print_banner

    echo -e "${BOLD}  Management Menu:${NC}\n"
    echo -e "  ${GREEN}1)${NC} Install (Fresh)"
    echo -e "  ${GREEN}2)${NC} Update"
    echo -e "  ${GREEN}3)${NC} Status"
    echo -e "  ${GREEN}4)${NC} Restart"
    echo -e "  ${GREEN}5)${NC} View Logs"
    echo -e "  ${GREEN}6)${NC} Backup Database"
    echo -e "  ${GREEN}7)${NC} Reconfigure (.env)"
    echo -e "  ${GREEN}8)${NC} Seed Database"
    echo -e "  ${GREEN}9)${NC} Stop"
    echo -e "  ${RED}10)${NC} Uninstall"
    echo -e "  ${YELLOW}0)${NC} Exit"
    echo ""
    read -p "  Select option: " CHOICE

    case $CHOICE in
        1) do_install ;;
        2) do_update ;;
        3) do_status ;;
        4) do_restart ;;
        5) do_logs ;;
        6) do_backup ;;
        7) do_config ;;
        8) do_seed ;;
        9) do_stop ;;
        10) do_uninstall ;;
        0) exit 0 ;;
        *) error "Invalid option"; show_menu ;;
    esac
}

# ============================================
# Entry Point
# ============================================

# Handle CLI arguments
case "${1:-}" in
    install)    check_root; do_install ;;
    update)     check_root; do_update ;;
    status)     do_status ;;
    restart)    check_root; do_restart ;;
    stop)       check_root; do_stop ;;
    logs)       do_logs "${2:-bot}" ;;
    backup)     check_root; do_backup ;;
    config)     check_root; do_config ;;
    seed)       check_root; do_seed ;;
    uninstall)  check_root; do_uninstall ;;
    "")         check_root; show_menu ;;
    *)
        echo "Usage: $0 {install|update|status|restart|stop|logs|backup|config|seed|uninstall}"
        echo ""
        echo "Commands:"
        echo "  install    - Fresh installation"
        echo "  update     - Update to latest version"
        echo "  status     - Show service status"
        echo "  restart    - Restart all services"
        echo "  stop       - Stop all services"
        echo "  logs [svc] - View logs (bot/postgres/redis)"
        echo "  backup     - Create database backup"
        echo "  config     - Reconfigure .env"
        echo "  seed       - Seed database with sample data"
        echo "  uninstall  - Remove completely"
        exit 1
        ;;
esac

# Install CLI command
install_cli 2>/dev/null || true
