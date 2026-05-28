#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# iPBotS - Professional V2Ray Shop Bot Installer & Manager
# © iPmart Network (آی‌پیمارت نتورک)
# GitHub: https://github.com/iPmartNetwork/iPBotS
# Supported: Ubuntu 20.04 / 22.04 / 24.04 | Debian 11 / 12
# ═══════════════════════════════════════════════════════════════

# Exit on error
set -euo pipefail

# ─── Constants ────────────────────────────────────────────────
readonly IPBOTS_VERSION="1.0.0"
readonly INSTALL_DIR="/opt/iPBotS"
readonly REPO_URL="https://github.com/iPmartNetwork/iPBotS.git"
readonly BRANCH="master"
readonly NGINX_CONF="/etc/nginx/sites-available/ipbots"
readonly NGINX_ENABLED="/etc/nginx/sites-enabled/ipbots"
readonly LOG_FILE="/var/log/ipbots-install.log"
readonly BACKUP_DIR="/opt/iPBotS/backups"
readonly MIN_RAM_MB=512
readonly MIN_DISK_GB=5
readonly REQUIRED_PORTS=(80 443 8443)

# ─── Colors & Formatting ─────────────────────────────────────
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly CYAN='\033[0;36m'
readonly MAGENTA='\033[0;35m'
readonly BOLD='\033[1m'
readonly DIM='\033[2m'
readonly NC='\033[0m'

# ─── Global Variables ─────────────────────────────────────────
DOMAIN=""
BOT_TOKEN=""
ADMIN_ID=""
DB_PASS=""
INSTALL_MODE="interactive"  # interactive or silent

# ═══════════════════════════════════════════════════════════════
# UI Functions
# ═══════════════════════════════════════════════════════════════

print_banner() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
    
    ██╗██████╗ ██████╗  ██████╗ ████████╗███████╗
    ██║██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝██╔════╝
    ██║██████╔╝██████╔╝██║   ██║   ██║   ███████╗
    ██║██╔═══╝ ██╔══██╗██║   ██║   ██║   ╚════██║
    ██║██║     ██████╔╝╚██████╔╝   ██║   ███████║
    ╚═╝╚═╝     ╚═════╝  ╚═════╝    ╚═╝   ╚══════╝
    
EOF
    echo -e "${NC}"
    echo -e "    ${BOLD}V2Ray Shop Bot${NC} ${DIM}v${IPBOTS_VERSION}${NC}"
    echo -e "    ${DIM}© iPmart Network | github.com/iPmartNetwork/iPBotS${NC}"
    echo -e ""
    echo -e "    ${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_step() {
    echo -e "\n${BOLD}${BLUE}  ┌─ $1${NC}"
    echo -e "${BLUE}  └────────────────────────────────────────────${NC}\n"
}

success() { echo -e "  ${GREEN}  ✓${NC} $1"; }
warning() { echo -e "  ${YELLOW}  ⚠${NC} $1"; }
error()   { echo -e "  ${RED}  ✗${NC} $1"; }
info()    { echo -e "  ${CYAN}  ℹ${NC} $1"; }
debug()   { echo -e "  ${DIM}    $1${NC}"; }

spinner() {
    local pid=$1
    local msg=$2
    local spin='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    local i=0
    while kill -0 "$pid" 2>/dev/null; do
        printf "\r  ${CYAN}  ${spin:$i:1}${NC} $msg"
        i=$(( (i+1) % ${#spin} ))
        sleep 0.1
    done
    printf "\r"
}

confirm() {
    local msg=$1
    local default=${2:-n}
    if [ "$default" = "y" ]; then
        read -p "  $msg [Y/n]: " -n 1 -r REPLY
    else
        read -p "  $msg [y/N]: " -n 1 -r REPLY
    fi
    echo
    REPLY=${REPLY:-$default}
    [[ $REPLY =~ ^[Yy]$ ]]
}

# ═══════════════════════════════════════════════════════════════
# System Check Functions
# ═══════════════════════════════════════════════════════════════

check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "Root access required. Run: ${BOLD}sudo bash install.sh${NC}"
        exit 1
    fi
}

check_os() {
    if [ ! -f /etc/os-release ]; then
        error "Cannot detect operating system"
        exit 1
    fi

    # Read os-release in a way that doesn't conflict with our readonly vars
    local os_id=$(grep "^ID=" /etc/os-release | cut -d= -f2 | tr -d '"')
    local os_version=$(grep "^VERSION_ID=" /etc/os-release | cut -d= -f2 | tr -d '"')
    local os_pretty=$(grep "^PRETTY_NAME=" /etc/os-release | cut -d= -f2 | tr -d '"')

    case "$os_id" in
        ubuntu)
            if [[ ! "$os_version" =~ ^(20.04|22.04|24.04)$ ]]; then
                warning "Ubuntu $os_version not officially tested"
            fi
            ;;
        debian)
            if [[ ! "$os_version" =~ ^(11|12)$ ]]; then
                warning "Debian $os_version not officially tested"
            fi
            ;;
        *)
            warning "OS '$os_id' not officially supported"
            if ! confirm "Continue anyway?"; then
                exit 1
            fi
            ;;
    esac

    success "OS: $os_pretty"
}

check_resources() {
    # RAM check
    local ram_mb=$(free -m | awk '/^Mem:/{print $2}')
    if [ "$ram_mb" -lt "$MIN_RAM_MB" ]; then
        error "Insufficient RAM: ${ram_mb}MB (minimum: ${MIN_RAM_MB}MB)"
        exit 1
    fi
    success "RAM: ${ram_mb}MB"

    # Disk check
    local disk_gb=$(df -BG / | awk 'NR==2{print $4}' | tr -d 'G')
    if [ "$disk_gb" -lt "$MIN_DISK_GB" ]; then
        error "Insufficient disk: ${disk_gb}GB free (minimum: ${MIN_DISK_GB}GB)"
        exit 1
    fi
    success "Disk: ${disk_gb}GB free"

    # CPU
    local cpu_cores=$(nproc)
    success "CPU: ${cpu_cores} cores"
}

check_ports() {
    local blocked=()
    for port in "${REQUIRED_PORTS[@]}"; do
        if ss -tlnp | grep -q ":${port} "; then
            local process=$(ss -tlnp | grep ":${port} " | awk '{print $NF}' | head -1)
            blocked+=("$port ($process)")
        fi
    done

    if [ ${#blocked[@]} -gt 0 ]; then
        warning "Ports in use: ${blocked[*]}"
        info "These will be reconfigured during installation"
    else
        success "Required ports available (80, 443, 8443)"
    fi
}

check_existing_install() {
    if [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/docker-compose.yml" ]; then
        warning "Existing installation detected at $INSTALL_DIR"
        echo ""
        echo -e "  ${YELLOW}Options:${NC}"
        echo -e "    1) Update existing installation"
        echo -e "    2) Fresh install (backup & replace)"
        echo -e "    3) Cancel"
        echo ""
        read -p "  Select [1-3]: " choice
        case $choice in
            1) do_update; exit 0 ;;
            2) 
                backup_existing
                ;;
            *) exit 0 ;;
        esac
    fi
}

backup_existing() {
    if [ -f "$INSTALL_DIR/.env" ]; then
        local backup_name="/tmp/ipbots-backup-$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_name"
        cp "$INSTALL_DIR/.env" "$backup_name/"
        
        # Backup database
        if docker-compose -f "$INSTALL_DIR/docker-compose.yml" ps postgres 2>/dev/null | grep -q "Up"; then
            docker-compose -f "$INSTALL_DIR/docker-compose.yml" exec -T postgres \
                pg_dump -U postgres v2ray_shop > "$backup_name/database.sql" 2>/dev/null || true
        fi
        
        success "Backup saved to: $backup_name"
    fi
}

# ═══════════════════════════════════════════════════════════════
# Installation Functions
# ═══════════════════════════════════════════════════════════════

install_docker() {
    if command -v docker &> /dev/null; then
        local ver=$(docker --version | awk '{print $3}' | tr -d ',')
        success "Docker already installed: v$ver"
    else
        info "Installing Docker..."
        curl -fsSL https://get.docker.com | sh >> "$LOG_FILE" 2>&1
        systemctl enable docker >> "$LOG_FILE" 2>&1
        systemctl start docker
        success "Docker installed"
    fi

    # Docker Compose
    if command -v docker-compose &> /dev/null; then
        success "Docker Compose available"
    elif docker compose version &> /dev/null; then
        # Docker Compose V2 (plugin)
        alias docker-compose='docker compose'
        success "Docker Compose V2 available"
    else
        info "Installing Docker Compose..."
        local compose_ver=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep '"tag_name"' | cut -d'"' -f4)
        curl -fsSL "https://github.com/docker/compose/releases/download/${compose_ver}/docker-compose-$(uname -s)-$(uname -m)" \
            -o /usr/local/bin/docker-compose >> "$LOG_FILE" 2>&1
        chmod +x /usr/local/bin/docker-compose
        success "Docker Compose installed"
    fi
}

install_packages() {
    info "Installing system packages..."
    
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq >> "$LOG_FILE" 2>&1
    apt-get install -y -qq \
        curl wget git openssl \
        nginx certbot python3-certbot-nginx \
        ufw jq htop \
        >> "$LOG_FILE" 2>&1

    success "System packages installed"
}

clone_repository() {
    if [ -d "$INSTALL_DIR/.git" ]; then
        info "Updating repository..."
        cd "$INSTALL_DIR"
        git fetch origin >> "$LOG_FILE" 2>&1
        git reset --hard "origin/$BRANCH" >> "$LOG_FILE" 2>&1
        success "Repository updated"
    else
        info "Cloning repository..."
        rm -rf "$INSTALL_DIR" 2>/dev/null || true
        git clone -b "$BRANCH" --depth 1 "$REPO_URL" "$INSTALL_DIR" >> "$LOG_FILE" 2>&1
        success "Repository cloned"
    fi

    cd "$INSTALL_DIR"
    mkdir -p backups logs
    chmod 700 backups
    chmod 755 logs
}

configure_environment() {
    cd "$INSTALL_DIR"

    if [ -f ".env" ] && [ "$1" != "force" ]; then
        if confirm "Existing .env found. Reconfigure?"; then
            cp .env ".env.bak.$(date +%s)"
        else
            success "Keeping existing configuration"
            return
        fi
    fi

    cp .env.example .env

    echo ""
    echo -e "  ${BOLD}${CYAN}Configuration Wizard${NC}"
    echo -e "  ${DIM}─────────────────────────────────────────${NC}"
    echo ""

    # Bot Token
    while true; do
        read -p "  🤖 Bot Token (from @BotFather): " BOT_TOKEN
        if [[ "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]]; then
            break
        fi
        error "Invalid format. Example: 123456789:ABCdef-GHIjklMNO"
    done

    # Admin ID
    while true; do
        read -p "  👤 Your Telegram ID (numeric): " ADMIN_ID
        if [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; then
            break
        fi
        error "Must be numeric. Get from @userinfobot"
    done

    # Bot Username
    read -p "  📱 Bot username (without @): " BOT_USERNAME
    BOT_USERNAME=${BOT_USERNAME:-mybot}

    # Domain
    echo ""
    echo -e "  ${CYAN}Connection Mode:${NC}"
    echo -e "    1) Webhook (requires domain + SSL) ${GREEN}[recommended]${NC}"
    echo -e "    2) Polling (no domain needed)"
    echo ""
    read -p "  Select [1/2]: " conn_mode

    if [ "$conn_mode" = "1" ]; then
        while true; do
            read -p "  🌐 Domain (e.g., bot.example.com): " DOMAIN
            if [[ "$DOMAIN" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*\.)+[a-zA-Z]{2,}$ ]]; then
                break
            fi
            error "Invalid domain format"
        done
    fi

    # Database password
    DB_PASS=$(openssl rand -base64 32 | tr -d '/+=' | head -c 24)

    # Secret key
    local SECRET_KEY=$(openssl rand -hex 32)

    # Payment gateways
    echo ""
    echo -e "  ${CYAN}Payment Gateways (Enter to skip):${NC}"
    read -p "  💳 ZarinPal Merchant ID: " ZARINPAL_ID
    read -p "  🪙 NowPayments API Key: " NOWPAY_KEY
    read -p "  🔐 Cryptomus Merchant ID: " CRYPTOMUS_ID
    read -p "  🔐 Cryptomus API Key: " CRYPTOMUS_KEY

    # Card2Card
    echo ""
    if confirm "  🏦 Enable Card-to-Card payment?" "n"; then
        read -p "  💳 Card Number: " CARD_NUMBER
        read -p "  👤 Card Holder Name: " CARD_HOLDER
        sed -i "s|CARD2CARD_ENABLED=.*|CARD2CARD_ENABLED=true|" .env
        sed -i "s|CARD2CARD_NUMBER=.*|CARD2CARD_NUMBER=$CARD_NUMBER|" .env
        sed -i "s|CARD2CARD_HOLDER=.*|CARD2CARD_HOLDER=$CARD_HOLDER|" .env
    fi

    # Apply configuration
    sed -i "s|BOT_TOKEN=.*|BOT_TOKEN=$BOT_TOKEN|" .env
    sed -i "s|ADMIN_IDS=.*|ADMIN_IDS=$ADMIN_ID|" .env
    sed -i "s|BOT_USERNAME=.*|BOT_USERNAME=$BOT_USERNAME|" .env
    sed -i "s|APP_SECRET_KEY=.*|APP_SECRET_KEY=$SECRET_KEY|" .env
    sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=$DB_PASS|" .env
    sed -i "s|BACKUP_CHAT_ID=.*|BACKUP_CHAT_ID=$ADMIN_ID|" .env
    sed -i "s|SUPPORT_CHAT_ID=.*|SUPPORT_CHAT_ID=$ADMIN_ID|" .env

    if [ -n "$DOMAIN" ]; then
        sed -i "s|WEBHOOK_ENABLED=.*|WEBHOOK_ENABLED=true|" .env
        sed -i "s|WEBHOOK_HOST=.*|WEBHOOK_HOST=https://$DOMAIN|" .env
        sed -i "s|ZARINPAL_CALLBACK_URL=.*|ZARINPAL_CALLBACK_URL=https://$DOMAIN/api/payment/zarinpal/callback|" .env
        sed -i "s|NOWPAYMENTS_CALLBACK_URL=.*|NOWPAYMENTS_CALLBACK_URL=https://$DOMAIN/api/payment/nowpayments/callback|" .env
        sed -i "s|CRYPTOMUS_CALLBACK_URL=.*|CRYPTOMUS_CALLBACK_URL=https://$DOMAIN/api/payment/cryptomus/callback|" .env
    else
        sed -i "s|WEBHOOK_ENABLED=.*|WEBHOOK_ENABLED=false|" .env
    fi

    [ -n "$ZARINPAL_ID" ] && sed -i "s|ZARINPAL_MERCHANT_ID=.*|ZARINPAL_MERCHANT_ID=$ZARINPAL_ID|" .env
    [ -n "$NOWPAY_KEY" ] && sed -i "s|NOWPAYMENTS_API_KEY=.*|NOWPAYMENTS_API_KEY=$NOWPAY_KEY|" .env
    [ -n "$CRYPTOMUS_ID" ] && sed -i "s|CRYPTOMUS_MERCHANT_ID=.*|CRYPTOMUS_MERCHANT_ID=$CRYPTOMUS_ID|" .env
    [ -n "$CRYPTOMUS_KEY" ] && sed -i "s|CRYPTOMUS_API_KEY=.*|CRYPTOMUS_API_KEY=$CRYPTOMUS_KEY|" .env

    chmod 600 .env
    success "Configuration saved"
}

setup_ssl() {
    if [ -z "$DOMAIN" ]; then
        info "Polling mode - SSL not required"
        return
    fi

    if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
        success "SSL certificate exists for $DOMAIN"
        return
    fi

    info "Obtaining SSL certificate..."

    # Stop nginx if running (need port 80)
    systemctl stop nginx 2>/dev/null || true

    certbot certonly --standalone \
        -d "$DOMAIN" \
        --non-interactive \
        --agree-tos \
        --email "admin@$DOMAIN" \
        --preferred-challenges http \
        >> "$LOG_FILE" 2>&1 && {
        success "SSL certificate obtained"
    } || {
        warning "SSL failed. Ensure:"
        warning "  • Domain $DOMAIN points to this server's IP"
        warning "  • Port 80 is open and not blocked"
        warning "  Retry later: certbot certonly --standalone -d $DOMAIN"
    }
}

setup_nginx() {
    if [ -z "$DOMAIN" ]; then
        info "No domain - skipping Nginx"
        return
    fi

    info "Configuring Nginx..."

    cat > "$NGINX_CONF" << NGINXEOF
# iPBotS Nginx Configuration
# Auto-generated by install.sh - $(date)
# © iPmart Network

# Rate limiting
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=webhook:10m rate=30r/s;

# HTTP -> HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # Telegram Webhook
    location /api/telegram/webhook {
        limit_req zone=webhook burst=50 nodelay;
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }

    # Payment Callbacks
    location /api/payment/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebApp API
    location /api/webapp/ {
        limit_req zone=api burst=30 nodelay;
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Mini App (static)
    location /webapp {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host \$host;
        proxy_cache_valid 200 1h;
        expires 1h;
    }

    # Health Check
    location /health {
        proxy_pass http://127.0.0.1:8443;
        access_log off;
    }

    # Block all other paths
    location / {
        return 444;
    }
}
NGINXEOF

    # Enable site
    ln -sf "$NGINX_CONF" "$NGINX_ENABLED" 2>/dev/null
    rm -f /etc/nginx/sites-enabled/default 2>/dev/null

    # Test and start
    if nginx -t >> "$LOG_FILE" 2>&1; then
        systemctl enable nginx >> "$LOG_FILE" 2>&1
        systemctl restart nginx
        success "Nginx configured with SSL + rate limiting"
    else
        error "Nginx config error. Check: nginx -t"
    fi
}

setup_firewall() {
    info "Configuring firewall..."

    ufw --force reset >> "$LOG_FILE" 2>&1
    ufw default deny incoming >> "$LOG_FILE" 2>&1
    ufw default allow outgoing >> "$LOG_FILE" 2>&1
    ufw allow 22/tcp comment 'SSH' >> "$LOG_FILE" 2>&1
    ufw allow 80/tcp comment 'HTTP' >> "$LOG_FILE" 2>&1
    ufw allow 443/tcp comment 'HTTPS' >> "$LOG_FILE" 2>&1
    # Don't expose 8443 directly - Nginx proxies it
    ufw --force enable >> "$LOG_FILE" 2>&1

    success "Firewall: SSH(22), HTTP(80), HTTPS(443)"
}

start_services() {
    cd "$INSTALL_DIR"

    info "Building and starting containers..."

    # Stop existing
    docker-compose down --remove-orphans 2>/dev/null || true

    # Build and start
    docker-compose up -d --build >> "$LOG_FILE" 2>&1

    # Wait for PostgreSQL
    info "Waiting for database..."
    local retries=0
    while [ $retries -lt 30 ]; do
        if docker-compose exec -T postgres pg_isready -U postgres >> "$LOG_FILE" 2>&1; then
            success "PostgreSQL ready"
            break
        fi
        retries=$((retries + 1))
        sleep 2
    done

    if [ $retries -ge 30 ]; then
        warning "PostgreSQL slow to start. Check: docker-compose logs postgres"
    fi

    # Wait for Redis
    sleep 2
    if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        success "Redis ready"
    fi

    # Wait for bot
    sleep 5
    if docker-compose ps bot 2>/dev/null | grep -q "Up"; then
        success "Bot container running"
    else
        warning "Bot starting... Check: ipbots logs"
    fi
}

seed_database() {
    cd "$INSTALL_DIR"

    info "Seeding database..."
    docker-compose exec -T bot python -m core.database.seed >> "$LOG_FILE" 2>&1 && {
        success "Database seeded (categories, plans, rewards)"
    } || {
        info "Seed skipped (may already exist)"
    }
}

setup_webhook() {
    if [ -z "$DOMAIN" ]; then
        info "Polling mode active - no webhook needed"
        return
    fi

    # Read token from .env
    source "$INSTALL_DIR/.env" 2>/dev/null || true

    sleep 3
    local webhook_url="https://$DOMAIN/api/telegram/webhook"
    info "Setting webhook: $webhook_url"

    local result=$(curl -s "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook?url=${webhook_url}&drop_pending_updates=true&max_connections=100")

    if echo "$result" | jq -r '.ok' 2>/dev/null | grep -q "true"; then
        success "Webhook active"
    else
        local err=$(echo "$result" | jq -r '.description' 2>/dev/null)
        warning "Webhook failed: $err"
        info "Manual: https://api.telegram.org/bot<TOKEN>/setWebhook?url=$webhook_url"
    fi
}

setup_cron() {
    info "Setting up scheduled tasks..."

    # Remove old cron entries
    crontab -l 2>/dev/null | grep -v "ipbots\|iPBotS\|certbot" | crontab - 2>/dev/null || true

    # Add new entries
    (crontab -l 2>/dev/null; cat << 'CRON'
# iPBotS - Auto start on reboot
@reboot cd /opt/iPBotS && docker-compose up -d

# iPBotS - SSL renewal (twice daily)
0 3,15 * * * certbot renew --quiet --post-hook "systemctl reload nginx"

# iPBotS - Docker cleanup (weekly)
0 4 * * 0 docker system prune -f > /dev/null 2>&1

# iPBotS - Log rotation (daily)
0 0 * * * find /opt/iPBotS/logs -name "*.log" -mtime +30 -delete 2>/dev/null
CRON
    ) | crontab -

    success "Cron jobs configured (auto-start, SSL renewal, cleanup)"
}

install_cli() {
    cat > /usr/local/bin/ipbots << 'CLIEOF'
#!/bin/bash
# iPBotS CLI - Quick management commands
# © iPmart Network

INSTALL_DIR="/opt/iPBotS"

case "${1:-help}" in
    status)
        echo "═══ iPBotS Status ═══"
        cd "$INSTALL_DIR" && docker-compose ps
        echo ""
        echo "═══ Health ═══"
        curl -s http://127.0.0.1:8443/health 2>/dev/null && echo "" || echo "API: Not responding"
        ;;
    logs)
        cd "$INSTALL_DIR" && docker-compose logs -f --tail=100 "${2:-bot}"
        ;;
    restart)
        cd "$INSTALL_DIR" && docker-compose restart "${2:-}"
        echo "✓ Restarted"
        ;;
    stop)
        cd "$INSTALL_DIR" && docker-compose down
        echo "✓ Stopped"
        ;;
    start)
        cd "$INSTALL_DIR" && docker-compose up -d
        echo "✓ Started"
        ;;
    update)
        sudo bash "$INSTALL_DIR/install.sh" update
        ;;
    backup)
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        cd "$INSTALL_DIR"
        docker-compose exec -T postgres pg_dump -U postgres v2ray_shop > "backups/backup_${TIMESTAMP}.sql"
        echo "✓ Backup: backups/backup_${TIMESTAMP}.sql"
        ;;
    config)
        sudo nano "$INSTALL_DIR/.env"
        echo "Restart required: ipbots restart"
        ;;
    seed)
        cd "$INSTALL_DIR" && docker-compose exec -T bot python -m core.database.seed
        ;;
    uninstall)
        sudo bash "$INSTALL_DIR/install.sh" uninstall
        ;;
    *)
        echo "iPBotS v1.0.0 - © iPmart Network"
        echo ""
        echo "Usage: ipbots <command>"
        echo ""
        echo "Commands:"
        echo "  status      Show service status"
        echo "  start       Start all services"
        echo "  stop        Stop all services"
        echo "  restart     Restart services"
        echo "  logs [svc]  View logs (bot/postgres/redis)"
        echo "  update      Update to latest version"
        echo "  backup      Create database backup"
        echo "  config      Edit configuration"
        echo "  seed        Seed database"
        echo "  uninstall   Remove iPBotS"
        ;;
esac
CLIEOF

    chmod +x /usr/local/bin/ipbots
    success "CLI installed: use 'ipbots' command anywhere"
}

health_check_final() {
    echo ""
    echo -e "  ${BOLD}${CYAN}Final Health Check${NC}"
    echo -e "  ${DIM}─────────────────────────────────────────${NC}"

    local all_ok=true

    # Docker containers
    if docker-compose -f "$INSTALL_DIR/docker-compose.yml" ps 2>/dev/null | grep -q "Up"; then
        success "Containers: Running"
    else
        error "Containers: Not running"
        all_ok=false
    fi

    # API health
    sleep 2
    if curl -s "http://127.0.0.1:8443/health" 2>/dev/null | grep -q "ok"; then
        success "API: Healthy"
    else
        warning "API: Starting (may need 10-20s)"
    fi

    # Nginx
    if [ -n "$DOMAIN" ]; then
        if systemctl is-active nginx > /dev/null 2>&1; then
            success "Nginx: Active"
        else
            error "Nginx: Inactive"
            all_ok=false
        fi

        # SSL
        if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
            success "SSL: Valid"
        else
            warning "SSL: Not configured"
        fi
    fi

    # Disk space
    local disk_free=$(df -BG / | awk 'NR==2{print $4}' | tr -d 'G')
    success "Disk free: ${disk_free}GB"

    echo ""
    if [ "$all_ok" = true ]; then
        echo -e "  ${GREEN}${BOLD}All systems operational ✓${NC}"
    else
        echo -e "  ${YELLOW}Some issues detected. Check: ipbots logs${NC}"
    fi
}

# ═══════════════════════════════════════════════════════════════
# Main Actions
# ═══════════════════════════════════════════════════════════════

do_install() {
    print_banner

    print_step "System Requirements Check"
    check_root
    check_os
    check_resources
    check_ports
    check_existing_install

    print_step "Installing Dependencies"
    install_packages
    install_docker

    print_step "Downloading iPBotS"
    clone_repository

    print_step "Configuration"
    configure_environment

    print_step "SSL & Security"
    setup_ssl
    setup_firewall

    print_step "Nginx Reverse Proxy"
    setup_nginx

    print_step "Starting Services"
    start_services
    seed_database

    print_step "Finalizing"
    setup_webhook
    setup_cron
    install_cli
    health_check_final

    # Success banner
    echo ""
    echo -e "${GREEN}"
    echo "  ╔═══════════════════════════════════════════════╗"
    echo "  ║                                               ║"
    echo "  ║   ✅ iPBotS Installed Successfully!          ║"
    echo "  ║                                               ║"
    echo "  ║   © iPmart Network                           ║"
    echo "  ║                                               ║"
    echo "  ╚═══════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo -e "  ${BOLD}Quick Start:${NC}"
    echo -e "    • Send ${CYAN}/start${NC} to your bot"
    echo -e "    • Admin panel: ${CYAN}/admin${NC}"
    echo -e "    • Add server: Admin → 🖥️ Servers → ➕ Add"
    echo ""
    if [ -n "$DOMAIN" ]; then
        echo -e "  ${BOLD}URLs:${NC}"
        echo -e "    • WebApp: ${CYAN}https://$DOMAIN/webapp${NC}"
        echo -e "    • Health: ${CYAN}https://$DOMAIN/health${NC}"
        echo ""
    fi
    echo -e "  ${BOLD}Management:${NC}"
    echo -e "    ${DIM}ipbots status${NC}    - Check status"
    echo -e "    ${DIM}ipbots logs${NC}      - View logs"
    echo -e "    ${DIM}ipbots restart${NC}   - Restart"
    echo -e "    ${DIM}ipbots update${NC}    - Update"
    echo -e "    ${DIM}ipbots backup${NC}    - Backup DB"
    echo ""
    echo -e "  ${DIM}Log file: $LOG_FILE${NC}"
    echo ""
}

do_update() {
    print_banner
    check_root

    print_step "Updating iPBotS"

    cd "$INSTALL_DIR" || { error "Not installed"; exit 1; }

    # Backup
    cp .env ".env.pre-update.$(date +%s)"
    success ".env backed up"

    # Pull latest
    git fetch origin >> "$LOG_FILE" 2>&1
    git reset --hard "origin/$BRANCH" >> "$LOG_FILE" 2>&1
    success "Code updated to latest"

    # Restore .env
    success "Configuration preserved"

    # Rebuild
    docker-compose up -d --build >> "$LOG_FILE" 2>&1
    success "Containers rebuilt"

    # Update database
    sleep 5
    docker-compose exec -T bot python -c "
import asyncio
from core.database.engine import create_tables
asyncio.run(create_tables())
" >> "$LOG_FILE" 2>&1 && success "Database schema updated" || info "DB update skipped"

    install_cli
    health_check_final

    echo ""
    success "Update complete! v$IPBOTS_VERSION"
    echo ""
}

do_uninstall() {
    print_banner
    check_root

    echo -e "  ${RED}${BOLD}⚠️  UNINSTALL iPBotS${NC}"
    echo -e "  ${RED}This will permanently delete:${NC}"
    echo -e "  ${RED}  • All containers and volumes${NC}"
    echo -e "  ${RED}  • Database and user data${NC}"
    echo -e "  ${RED}  • Configuration files${NC}"
    echo ""

    read -p "  Type 'DELETE' to confirm: " confirm_text
    if [ "$confirm_text" != "DELETE" ]; then
        info "Cancelled"
        exit 0
    fi

    echo ""

    # Backup before delete
    if confirm "Create final backup before deletion?" "y"; then
        local final_backup="/tmp/ipbots-final-$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$final_backup"
        cp "$INSTALL_DIR/.env" "$final_backup/" 2>/dev/null || true
        docker-compose -f "$INSTALL_DIR/docker-compose.yml" exec -T postgres \
            pg_dump -U postgres v2ray_shop > "$final_backup/database.sql" 2>/dev/null || true
        success "Final backup: $final_backup"
    fi

    # Stop and remove
    cd "$INSTALL_DIR" 2>/dev/null || true
    docker-compose down -v --remove-orphans 2>/dev/null || true
    success "Containers removed"

    # Remove nginx
    rm -f "$NGINX_CONF" "$NGINX_ENABLED" 2>/dev/null
    systemctl reload nginx 2>/dev/null || true
    success "Nginx config removed"

    # Remove cron
    crontab -l 2>/dev/null | grep -v "iPBotS\|ipbots" | crontab - 2>/dev/null || true
    success "Cron jobs removed"

    # Remove files
    rm -rf "$INSTALL_DIR"
    rm -f /usr/local/bin/ipbots
    success "Files removed"

    echo ""
    echo -e "  ${GREEN}iPBotS has been completely removed.${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════════
# Interactive Menu
# ═══════════════════════════════════════════════════════════════

show_menu() {
    print_banner

    local installed=false
    [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/docker-compose.yml" ] && installed=true

    if [ "$installed" = true ]; then
        # Check if running
        local running=false
        docker-compose -f "$INSTALL_DIR/docker-compose.yml" ps 2>/dev/null | grep -q "Up" && running=true

        if [ "$running" = true ]; then
            echo -e "  Status: ${GREEN}● Running${NC}"
        else
            echo -e "  Status: ${RED}● Stopped${NC}"
        fi
    else
        echo -e "  Status: ${YELLOW}● Not Installed${NC}"
    fi
    echo ""

    echo -e "  ${BOLD}Select an option:${NC}"
    echo ""
    echo -e "    ${GREEN}1)${NC}  🚀 Install (Fresh)"
    echo -e "    ${GREEN}2)${NC}  🔄 Update"
    echo -e "    ${GREEN}3)${NC}  📊 Status"
    echo -e "    ${GREEN}4)${NC}  🔁 Restart"
    echo -e "    ${GREEN}5)${NC}  📋 View Logs"
    echo -e "    ${GREEN}6)${NC}  💾 Backup Database"
    echo -e "    ${GREEN}7)${NC}  ⚙️  Reconfigure"
    echo -e "    ${GREEN}8)${NC}  🌱 Seed Database"
    echo -e "    ${GREEN}9)${NC}  ⏹️  Stop Services"
    echo -e "    ${GREEN}10)${NC} ▶️  Start Services"
    echo -e "    ${RED}11)${NC} 🗑️  Uninstall"
    echo -e "    ${YELLOW}0)${NC}  Exit"
    echo ""
    read -p "  ➤ " choice

    case $choice in
        1) do_install ;;
        2) do_update ;;
        3) do_status ;;
        4) cd "$INSTALL_DIR" 2>/dev/null && docker-compose restart && success "Restarted" || error "Not installed" ;;
        5) cd "$INSTALL_DIR" 2>/dev/null && docker-compose logs -f --tail=50 bot || error "Not installed" ;;
        6) do_backup ;;
        7) cd "$INSTALL_DIR" 2>/dev/null && configure_environment "force" && info "Run: ipbots restart" || error "Not installed" ;;
        8) cd "$INSTALL_DIR" 2>/dev/null && docker-compose exec -T bot python -m core.database.seed || error "Not installed" ;;
        9) cd "$INSTALL_DIR" 2>/dev/null && docker-compose down && success "Stopped" || error "Not installed" ;;
        10) cd "$INSTALL_DIR" 2>/dev/null && docker-compose up -d && success "Started" || error "Not installed" ;;
        11) do_uninstall ;;
        0) exit 0 ;;
        *) show_menu ;;
    esac
}

do_status() {
    print_banner
    echo -e "  ${BOLD}Service Status${NC}"
    echo -e "  ${DIM}─────────────────────────────────────────${NC}"
    echo ""

    cd "$INSTALL_DIR" 2>/dev/null || { error "Not installed"; exit 1; }

    # Containers
    echo -e "  ${CYAN}Containers:${NC}"
    docker-compose ps 2>/dev/null | tail -n +2 | while IFS= read -r line; do
        if echo "$line" | grep -q "Up"; then
            echo -e "    ${GREEN}●${NC} $line"
        else
            echo -e "    ${RED}●${NC} $line"
        fi
    done

    echo ""
    echo -e "  ${CYAN}Resources:${NC}"
    echo -e "    RAM: $(free -h | awk '/^Mem:/{print $3"/"$2}')"
    echo -e "    Disk: $(df -h / | awk 'NR==2{print $3"/"$2" ("$5" used)"}')"
    echo -e "    DB Size: $(docker-compose exec -T postgres psql -U postgres -d v2ray_shop -t -c "SELECT pg_size_pretty(pg_database_size('v2ray_shop'));" 2>/dev/null | tr -d ' ' || echo 'N/A')"

    echo ""
    echo -e "  ${CYAN}Health:${NC}"
    if curl -s "http://127.0.0.1:8443/health" 2>/dev/null | grep -q "ok"; then
        echo -e "    ${GREEN}● API: Healthy${NC}"
    else
        echo -e "    ${RED}● API: Not responding${NC}"
    fi

    if [ -n "$(grep 'WEBHOOK_ENABLED=true' $INSTALL_DIR/.env 2>/dev/null)" ]; then
        echo -e "    Mode: Webhook"
    else
        echo -e "    Mode: Polling"
    fi

    echo ""
}

do_backup() {
    cd "$INSTALL_DIR" || { error "Not installed"; exit 1; }

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/backup_${timestamp}.sql"
    mkdir -p "$BACKUP_DIR"

    docker-compose exec -T postgres pg_dump -U postgres v2ray_shop > "$backup_file" 2>/dev/null && {
        local size=$(du -h "$backup_file" | awk '{print $1}')
        success "Backup created: $backup_file ($size)"

        # Cleanup old backups (keep last 10)
        ls -t "$BACKUP_DIR"/backup_*.sql 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null
        info "Old backups cleaned (keeping last 10)"
    } || {
        error "Backup failed. Is PostgreSQL running?"
    }
}

# ═══════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════

# Create log file
mkdir -p "$(dirname $LOG_FILE)"
touch "$LOG_FILE"

# Route commands
case "${1:-}" in
    install)    check_root; do_install ;;
    update)     check_root; do_update ;;
    uninstall)  check_root; do_uninstall ;;
    status)     do_status ;;
    backup)     check_root; do_backup ;;
    logs)       cd "$INSTALL_DIR" 2>/dev/null && docker-compose logs -f --tail=100 "${2:-bot}" ;;
    restart)    check_root; cd "$INSTALL_DIR" && docker-compose restart && success "Restarted" ;;
    stop)       check_root; cd "$INSTALL_DIR" && docker-compose down && success "Stopped" ;;
    start)      check_root; cd "$INSTALL_DIR" && docker-compose up -d && success "Started" ;;
    config)     check_root; cd "$INSTALL_DIR" && configure_environment "force" ;;
    seed)       check_root; cd "$INSTALL_DIR" && docker-compose exec -T bot python -m core.database.seed ;;
    "")         check_root; show_menu ;;
    -h|--help|help)
        echo "iPBotS v$IPBOTS_VERSION - © iPmart Network"
        echo "GitHub: https://github.com/iPmartNetwork/iPBotS"
        echo ""
        echo "Usage: bash install.sh [command]"
        echo ""
        echo "Commands:"
        echo "  install     Fresh installation"
        echo "  update      Update to latest version"
        echo "  status      Show service status"
        echo "  start       Start services"
        echo "  stop        Stop services"
        echo "  restart     Restart services"
        echo "  logs [svc]  View logs (bot/postgres/redis)"
        echo "  backup      Create database backup"
        echo "  config      Reconfigure .env"
        echo "  seed        Seed database with sample data"
        echo "  uninstall   Remove completely"
        echo ""
        echo "After installation, use 'ipbots' command globally."
        ;;
    *)
        error "Unknown command: $1"
        echo "Run: bash install.sh --help"
        exit 1
        ;;
esac
