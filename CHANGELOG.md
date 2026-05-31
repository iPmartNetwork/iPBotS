# Changelog

All notable changes to iPBotS will be documented in this file.

## [1.4.0] - 2026-05-30

### ✨ Level 1 — Revenue Features
- **Cloudflare Worker** - Sub link proxy for anti-filtering
- **Recurring Subscription** - Auto-payment model (monthly/custom interval)
- **Dedicated IP** - Sell static IPs to users
- **Credit System** - Buy now, pay later model
- **CF_WORKER_URL** config for automatic proxied links

### 🛡️ Level 2 — Stability Features
- **GitHub Actions CI/CD** - Lint + Docker build on every push
- **Sentry Integration** - Automatic error tracking in production
- **Migration Helper** - `scripts/migrate.sh` for DB migrations
- 3 new database models (26 total)

## [1.3.0-rc2] - 2026-05-30

### 🐛 Critical Bug Fixes (Comprehensive Audit)
- Fixed 11 missing callback handlers (admin:users:list, admin:servers:list, admin:settings:*, admin:cancel:*, admin:giftcard:add, admin:discount:list)
- Fixed `plan_id` not nullable in Subscription model (trial subscriptions crashed)
- Fixed `send_expiry_notifications` using internal user_id instead of telegram_id
- Fixed `hmac.new` → `hmac.HMAC` in NowPayments IPN verification
- Fixed `setting_value` state handler not detecting menu buttons (state conflict)
- Added missing `wallet_withdraw_amount` handler (users were stuck in state)
- Fixed `sub.server` None dereference crash in subscription detail

## [1.3.0-rc1] - 2026-05-30

### ✨ New Panel Support
- **IBSng** - Radius/ISP panel service
- **Mikrotik** - RouterOS REST API service
- **WGDashboard** - WireGuard management panel
- PanelType enum updated (now 7 panels total)

## [1.3.0] - 2026-05-29

### ✨ New Features
- **Forced Channel Join** - Unlimited mandatory channels with membership check
- **Anti-Spam** - Redis-based rate limiting (5 msg/10s per user)
- **Forward Broadcast** - Forward any message type (photo/video/file) to all users
- **Marzneshin Panel** - Full support for Marzneshin (compatible with Marzban API)
- **IDPay Gateway** - Iranian Rial payment via IDPay.ir
- **Scheduled Messages** - Database model for time-based message scheduling
- **Protocol Management** - Configure protocols per server (vless/vmess/trojan/ss)
- **Bot Text Customization** - Admin-editable bot texts via database
- **Phone Verification** - FSM state for phone number verification flow
- **PanelType.MARZNESHIN** - Added to server enum

### 🔧 Infrastructure
- New middlewares: ForcedJoinMiddleware, AntiSpamMiddleware
- Forward broadcast button in admin keyboard
- IDPay config in .env.example
- 4 new database models

## [1.2.0] - 2026-05-29

### ✨ New Features
- **Pagination utility** for all list views
- **Subscription Upgrade** - real implementation showing eligible plans
- **Admin CSV Export** - `/export_users` and `/export_payments` commands
- **Status Page** - public HTML page at `/status` showing server health
- **Family Plan model** - share one subscription with multiple users
- **Subscription Transfer** - transfer active service to another user
- **Review/Rating model** - users can rate after purchase

### 🔧 Improvements
- All incomplete features from rc2 are now functional
- New database models: FamilyGroup, FamilyMember, Review
- Admin export router registered
- Pagination noop callback handler

## [1.0.0-rc2] - 2026-05-29

### 🔴 Critical Fixes
- Auto-create subscription after card2card payment approval (full panel integration)
- Nullable plan_id handling for trial subscriptions (no more crashes)
- `admin:plans:list` callback handler added (back button works)
- Auth middleware error handling (bot doesn't crash if DB is down)
- Order cancel handler (`order:cancel:` callback)

### 🟠 Important UX Improvements
- Admin: Assign category to plan (from edit menu)
- Admin: Assign server to plan (from edit menu)
- Admin: View user wallet info with transactions
- Wallet: Card-to-card charge flow
- Deep Link support (`/start plan_5` → direct to plan)
- Notification channel posting on each purchase
- Rebuy expired subscription handler

### 🟡 Improvements
- Graceful error handling in auth middleware
- Subscription detail shows "تست رایگان" for trial subs
- All broken callback handlers now have proper responses

### 🔧 Previous (rc1) Fixes Included
- Password encryption for panel credentials
- Referral bonus auto-applied on purchase
- Loyalty points auto-awarded on purchase
- Auto-renew with panel update
- Card2Card receipt handler with admin notification
- Crypto payment handlers (NowPayments)
- Admin: Edit plan (name/price/data/duration/category/server/delete)
- Admin: Edit server (location/flag/max_users/toggle default)
- Admin: User unban button
- Docker Compose V2 compatibility
- Webhook mode handler registration fix
- FSM state conflicts resolved

---

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
