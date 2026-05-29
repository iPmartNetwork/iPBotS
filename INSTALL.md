# 📖 راهنمای نصب و راه‌اندازی V2Ray Shop Bot

<p align="center">
  <b>© iPmart Network (آی‌پیمارت نتورک)</b>
</p>

## 📋 پیش‌نیازها

- سرور لینوکس (Ubuntu 22.04 یا 24.04)
- حداقل 1GB RAM و 10GB فضا
- دامنه (برای webhook و webapp)
- پنل VPN نصب شده (3x-ui یا Marzban یا Hiddify)

## 🚀 نصب سریع (خودکار)

```bash
sudo bash -c "$(curl -sL https://raw.githubusercontent.com/iPmartNetwork/iPBotS/main/install.sh)"
```

## 🔧 نصب دستی

### 1. نصب Docker

```bash
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo systemctl enable docker
sudo systemctl start docker
```

### 2. دانلود پروژه

```bash
cd /opt
git clone https://github.com/iPmartNetwork/iPBotS.git
cd iPBotS
```

### 3. تنظیم Environment

```bash
cp .env.example .env
nano .env
```

مقادیر زیر را حتماً تنظیم کنید:

| متغیر | توضیح |
|--------|--------|
| `BOT_TOKEN` | توکن بات از @BotFather |
| `ADMIN_IDS` | شناسه تلگرام ادمین (عدد) |
| `APP_SECRET_KEY` | یک رشته تصادفی (openssl rand -hex 32) |
| `DB_PASSWORD` | رمز دیتابیس |
| `WEBHOOK_HOST` | آدرس دامنه (https://bot.example.com) |

### 4. اجرا

```bash
docker-compose up -d
```

### 5. Seed دیتابیس (اختیاری - داده‌های نمونه)

```bash
docker-compose exec bot python -m core.database.seed
```

### 6. تنظیم Webhook

```bash
# جایگزین کنید: TOKEN و DOMAIN
curl "https://api.telegram.org/botTOKEN/setWebhook?url=https://DOMAIN/api/telegram/webhook"
```

### 7. SSL Certificate

```bash
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

## ✅ بررسی نصب

1. به ربات پیام `/start` بدهید
2. باید پیام خوش‌آمدگویی دریافت کنید
3. دستور `/admin` را بزنید (فقط ادمین‌ها)

## 🖥️ اضافه کردن سرور VPN

1. در ربات: `/admin` → 🖥️ سرورها → ➕ افزودن سرور
2. نام، آدرس، پورت، یوزر و پسورد پنل را وارد کنید
3. تست اتصال بزنید

## 📱 فعال‌سازی Mini App

1. به @BotFather بروید
2. `/mybots` → بات خود → Bot Settings → Menu Button
3. URL را تنظیم کنید: `https://your-domain.com/webapp`

## 🔄 بروزرسانی

```bash
ipbots update
```

یا دستی:

```bash
cd /opt/iPBotS
git fetch origin && git reset --hard origin/master
docker compose build --no-cache
docker compose up -d --force-recreate
```

## 🛠️ دستورات مفید

```bash
# مدیریت سریع
ipbots status              # وضعیت
ipbots logs                # لاگ بات
ipbots logs postgres       # لاگ دیتابیس
ipbots restart             # ری‌استارت
ipbots backup              # پشتیبان‌گیری
ipbots config              # تنظیم مجدد .env

# یا مستقیم Docker
cd /opt/iPBotS
docker-compose logs -f bot
docker-compose restart bot
docker-compose down
docker-compose up -d
docker-compose exec postgres psql -U postgres v2ray_shop
```

## ❓ مشکلات رایج

### بات پاسخ نمی‌دهد
- لاگ‌ها را بررسی کنید: `docker-compose logs bot`
- توکن بات را چک کنید
- Webhook را مجدد تنظیم کنید

### خطای دیتابیس
- صبر کنید PostgreSQL بالا بیاید: `docker-compose logs postgres`
- مایگریشن اجرا کنید: `docker-compose exec bot alembic upgrade head`

### خطای اتصال به پنل
- آدرس و پورت پنل را بررسی کنید
- فایروال سرور پنل را چک کنید
- یوزر/پسورد را مجدد وارد کنید

## 📞 پشتیبانی

- تلگرام: [@your_support](https://t.me/your_support)
- گیت‌هاب: Issues
