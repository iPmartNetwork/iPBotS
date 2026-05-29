# Changelog

All notable changes to iPBotS will be documented in this file.

## [1.0.0-rc1] - 2026-05-29

### 🚀 Initial Release Candidate

First public release of iPBotS - Professional V2Ray Shop Bot for Telegram.

### ✨ Features
- Complete shop system with plan categories, custom plans, bundles
- Free trial system for new users
- Auto-renewal from wallet
- Server selection by users
- QR Code generation for subscription links
- Multi-panel support: 3x-ui, Hiddify, Marzban
- Payment gateways: ZarinPal, NowPayments, Cryptomus, Card-to-Card
- Internal wallet with deposit/withdraw/history
- Referral system with commission
- Loyalty points & rewards (Bronze → Diamond)
- Reseller/Agency system with tiered discounts
- Support ticket system
- Connection tutorials for all platforms
- Telegram Mini App (WebApp)
- AI-powered support chatbot
- Marketing automation (inactive users, expired offers)
- Server health monitoring
- Daily & weekly automated reports
- Admin dashboard with real-time stats
- User management (ban, credit, message)
- Broadcast messaging
- Automatic database backups
- Professional installer with CLI (`ipbots` command)
- Nginx reverse proxy with SSL & rate limiting
- Docker Compose deployment
- Multi-language support (Persian + English)

### 🐛 Bug Fixes (during RC)
- Fixed `pydantic` version conflict with `aiogram 3.13.1`
- Fixed `ADMIN_IDS` validation error (string to list parsing)
- Fixed Docker Compose V2 compatibility (wrapper script)
- Fixed `/etc/os-release` readonly variable conflict in installer
- Fixed handlers not registering in webhook mode
- Fixed admin reply keyboard not showing after `/admin`
- Fixed all model enums not exported from `__init__.py`
- Fixed FSM state conflicts between menu items (state.clear on each menu)
- Fixed "back" button in shop not working
- Fixed loyalty/reseller/tutorial not accessible from reply keyboard

### 🔒 Security
- AES encryption for panel passwords
- Nginx rate limiting & security headers
- HSTS + TLS 1.2/1.3
- UFW firewall auto-configuration
- Audit logging for admin actions
- `.env` file permission 600

### 📦 Infrastructure
- Docker Compose with PostgreSQL 16 + Redis 7
- Alembic migrations
- APScheduler with 12 background jobs
- Loguru structured logging
- Auto-start on reboot (cron)
- SSL auto-renewal

---

© iPmart Network | https://github.com/iPmartNetwork/iPBotS
