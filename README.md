<p align="center">
  <img src="img/iPBotS.png" alt="iPBotS Logo" width="300">
</p>


<p align="center">
  <b>Professional V2Ray VPN Shop Telegram Bot</b><br>
  <i>Sell VPN configs with ease — supports 3x-ui, Hiddify & Marzban</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Version-1.4.0-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/License-AGPL--3.0-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Aiogram-3.x-009688?style=flat-square" alt="Aiogram">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker">
</p>

<p align="center">
  <a href="https://github.com/iPmartNetwork/iPBotS/stargazers"><img src="https://img.shields.io/github/stars/iPmartNetwork/iPBotS?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/iPmartNetwork/iPBotS/network/members"><img src="https://img.shields.io/github/forks/iPmartNetwork/iPBotS?style=flat-square" alt="Forks"></a>
  <a href="https://github.com/iPmartNetwork/iPBotS/issues"><img src="https://img.shields.io/github/issues/iPmartNetwork/iPBotS?style=flat-square" alt="Issues"></a>
  <a href="https://github.com/iPmartNetwork/iPBotS/commits/master"><img src="https://img.shields.io/github/last-commit/iPmartNetwork/iPBotS?style=flat-square" alt="Last Commit"></a>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-panels">Panels</a> •
  <a href="#-payments">Payments</a> •
  <a href="#-deployment">Deployment</a> •
  <a href="README_FA.md">فارسی</a>
</p>

---

## 📋 Overview

iPBotS is a full-featured Telegram bot for selling V2Ray/Xray VPN configurations. It connects to popular panels (3x-ui, Hiddify, Marzban), handles payments, manages subscriptions, and provides a complete shop experience — all through Telegram.

Built with modern async Python (Aiogram 3 + FastAPI + SQLAlchemy), it's designed for performance, scalability, and ease of deployment.

## ⚡ Quick Start

```bash
# One-line install:
sudo bash -c "$(curl -sL https://raw.githubusercontent.com/iPmartNetwork/iPBotS/master/install.sh)"
```

Or manually:

```bash
git clone https://github.com/iPmartNetwork/iPBotS.git
cd iPBotS
sudo bash install.sh
```

After installation, use the `ipbots` command:

```bash
ipbots status     # Service status
ipbots logs       # View logs
ipbots restart    # Restart
ipbots update     # Update to latest
ipbots backup     # Database backup
```

## ✨ Features

### 🛒 Shop & Sales

| Feature | Description |
|---------|-------------|
| Plan Categories | Organized plans with icons and sorting |
| Custom Plans | Users build their own plan (data + duration + IPs) |
| Free Trial | Attract new users with limited free service |
| Bundles | Sell multiple plans together at discount |
| Discount Codes | Percentage or fixed amount coupons |
| Auto-Renewal | Automatic renewal from wallet before expiry |
| Server Selection | Users choose their preferred location |
| QR Code | Generate QR for subscription links |
| Deep Link | Direct link to specific plan (`/start plan_5`) |
| Subscription Upgrade | Upgrade to higher plan from bot |
| Subscription Transfer | Transfer service to another user |

### 💳 Payments

| Gateway | Type |
|---------|------|
| ZarinPal | Iranian Rial (online) |
| NowPayments | Cryptocurrency |
| Cryptomus | Cryptocurrency |
| Card-to-Card | Manual with admin approval + auto-activation |
| IDPay | Iranian Rial (online) |
| Wallet | Internal balance |

### 👥 User System

| Feature | Description |
|---------|-------------|
| Wallet | Deposit, withdraw, transaction history |
| Referral | Invite friends, earn commission (auto-applied) |
| Loyalty Points | Earn points per purchase, redeem rewards |
| Reseller | Agency system with tiered discounts |
| Tickets | Support ticket system |
| Tutorials | Connection guides for all platforms |
| Family Plan | Share subscription with family members |
| Review/Rating | Rate service after purchase |

### 🛡️ Admin Panel

| Feature | Description |
|---------|-------------|
| Dashboard | Revenue, users, orders, real-time stats |
| User Management | Search, ban/unban, credit, message, wallet view |
| Server Management | Add/edit/test/delete VPN servers |
| Plan Management | Create/edit/delete plans, assign category & server |
| Payment Management | Approve/reject card-to-card payments |
| Broadcast | Send messages to all/active/selected users |
| Backup | Automatic + manual database backups |
| Daily Reports | Auto-generated revenue & growth reports |
| CSV Export | Export users and payments to CSV |
| Status Page | Public server health page at `/status` |

### 🤖 Smart Features

| Feature | Description |
|---------|-------------|
| AI Support | FAQ matching + optional GPT integration |
| Marketing Automation | Re-engage inactive users, expired offers |
| Health Monitoring | Server uptime checks every 5 minutes |
| Traffic Alerts | Notify users at 80% traffic usage |
| Expiry Notifications | Warn 3 days before subscription ends |
| Audit Log | Track all admin actions |
| Forced Channel Join | Require users to join channels before use |
| Anti-Spam | Redis rate limiting (5 msg/10s) |
| Forward Broadcast | Forward any message type to all users |
| Scheduled Messages | Time-based message scheduling |
| Protocol Management | Configure protocols per server |
| Bot Text Customization | Admin can change all bot texts |

### �️ Panels

| Panel | Status |
|-------|--------|
| 3x-ui (Sanaei) | ✅ Full support |
| Hiddify Manager | ✅ Full support |
| Marzban | ✅ Full support |
| Marzneshin | ✅ Full support |

### 🌐 Mini App (WebApp)

Modern Telegram Mini App with:
- Shop browsing with categories
- Service management with traffic charts
- Wallet with transaction history
- Profile and referral system
- Responsive dark theme UI

## 🛠️ Tech Stack

<p>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Aiogram-3.13-009688?style=flat-square">
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square">
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white">
  <img src="https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white">
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white">
  <img src="https://img.shields.io/badge/Nginx-Reverse_Proxy-009639?style=flat-square&logo=nginx&logoColor=white">
</p>

## 🚀 Deployment

### Requirements

| Requirement | Minimum |
|-------------|---------|
| OS | Ubuntu 20.04+ / Debian 11+ |
| RAM | 512 MB |
| Disk | 5 GB |
| Domain | Optional (for webhook mode) |

### Installation

See [INSTALL.md](INSTALL.md) for detailed instructions.

### Configuration

All settings in `.env` file. See [.env.example](.env.example) for all options.

### Management

```bash
ipbots status      # Check status
ipbots start       # Start services
ipbots stop        # Stop services
ipbots restart     # Restart
ipbots logs        # View bot logs
ipbots logs redis  # View Redis logs
ipbots update      # Update to latest
ipbots backup      # Create backup
ipbots config      # Edit .env
ipbots seed        # Seed sample data
ipbots uninstall   # Remove completely
```

## 📁 Project Structure

```
iPBotS/
├── bot/                 Telegram bot (Aiogram 3)
│   ├── handlers/        Message & callback handlers
│   │   ├── user/        User handlers (17 modules)
│   │   └── admin/       Admin handlers (8 modules)
│   ├── keyboards/       Inline & reply keyboards
│   ├── middlewares/     Auth, throttle, locale
│   ├── states/          FSM states
│   └── utils/           Helpers, QR code
├── core/                Business logic
│   ├── database/        Models, repositories, engine
│   ├── services/        Panel, payment, AI, marketing
│   └── scheduler/       Background jobs (12 tasks)
├── api/                 FastAPI (webhook + WebApp API)
├── webapp/              Telegram Mini App (HTML/CSS/JS)
├── locales/             i18n (Persian + English)
├── templates/           Payment result pages
├── migrations/          Alembic migrations
├── docker-compose.yml   Docker orchestration
├── install.sh           Auto-installer & manager
└── nginx.conf.example   Nginx reverse proxy config
```

## 🔒 Security

- AES encryption for panel passwords in database
- Nginx with rate limiting & security headers
- HSTS + TLS 1.2/1.3
- Firewall (UFW) auto-configured
- Audit logging for admin actions
- Input validation on all user inputs
- Redis-based rate limiting

## 📄 License

[AGPL-3.0](LICENSE)

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/iPmartNetwork">iPmart Network</a>
</p>
