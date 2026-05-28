# 🚀 V2Ray Shop Bot

<p align="center">
  <b>Developed by iPmart Network (آی‌پیمارت نتورک)</b><br>
  © 2024-2026 iPmart Network. All rights reserved.
</p>

---

یک ربات تلگرام حرفه‌ای و کامل برای فروش کانفیگ‌های V2Ray با پشتیبانی از پنل‌های 3x-ui و Hiddify و Marzban

## ✨ ویژگی‌ها

### 👤 بخش کاربر
- ثبت‌نام و احراز هویت خودکار
- خرید کانفیگ (سابسکریپشن و تکی)
- کیف‌پول (شارژ، برداشت، تاریخچه)
- مشاهده سرویس‌های فعال و مصرف ترافیک
- تمدید و ارتقای سرویس
- سیستم زیرمجموعه‌گیری (Referral)
- پشتیبانی تیکتی
- QR Code برای کانفیگ‌ها

### 🛡️ بخش ادمین
- داشبورد مالی کامل
- مدیریت کاربران (مسدود، حذف، ویرایش)
- مدیریت سرورها و پنل‌ها
- مدیریت پلن‌ها و قیمت‌گذاری
- مدیریت تخفیف‌ها و کدهای هدیه
- ارسال پیام انبوه و زمان‌بندی‌شده
- پشتیبان‌گیری خودکار و دستی
- گزارش‌گیری پیشرفته
- مدیریت فروشندگان (نمایندگی)

### 💳 درگاه‌های پرداخت
- زرین‌پال (ریالی)
- کارت به کارت (دستی با تأیید ادمین)
- NowPayments (ارز دیجیتال)
- Cryptomus (ارز دیجیتال)

### 🖥️ پنل‌های پشتیبانی
- 3x-ui (Sanaei)
- Hiddify Manager

### 🔧 فنی
- معماری Async کامل با Aiogram 3
- PostgreSQL + Redis
- Docker Compose برای دیپلوی
- Alembic برای مایگریشن دیتابیس
- FastAPI برای Webhook و API
- لاگینگ حرفه‌ای
- Rate Limiting
- Multi-language (فارسی/انگلیسی)

## 🚀 نصب سریع

```bash
# نصب یک‌خطی:
sudo bash -c "$(curl -sL https://raw.githubusercontent.com/iPmartNetwork/iPBotS/main/install.sh)"
```

یا:

```bash
git clone https://github.com/iPmartNetwork/iPBotS.git
cd iPBotS
sudo bash install.sh
```

## 🎛️ مدیریت

بعد از نصب، دستور `ipbots` در دسترس خواهد بود:

```bash
ipbots status     # وضعیت سرویس‌ها
ipbots logs       # مشاهده لاگ‌ها
ipbots restart    # ری‌استارت
ipbots update     # بروزرسانی
ipbots backup     # پشتیبان‌گیری
ipbots config     # تنظیم مجدد
ipbots stop       # توقف
ipbots uninstall  # حذف کامل
```

یا منوی تعاملی:

```bash
sudo bash install.sh
```

## ⚙️ تنظیمات

تمام تنظیمات در فایل `.env` قرار دارد. فایل `.env.example` را کپی کرده و مقادیر را تنظیم کنید.

## 📄 لایسنس

MIT License - © 2024-2026 iPmart Network (آی‌پیمارت نتورک)
