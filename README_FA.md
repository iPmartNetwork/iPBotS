<p align="center">
  <img src="img/iPBotS.png" alt="iPBotS Logo" width="200">
</p>

<h1 align="center">iPBotS</h1>

<p align="center">
  <b>ربات حرفه‌ای فروش VPN در تلگرام</b><br>
  <i>فروش کانفیگ V2Ray با پشتیبانی از 3x-ui، Hiddify و Marzban</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/نسخه-1.3.0-blue?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/لایسنس-AGPL--3.0-green?style=flat-square" alt="License">
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
  <a href="#-نصب-سریع">نصب سریع</a> •
  <a href="#-ویژگیها">ویژگی‌ها</a> •
  <a href="#-پنلها">پنل‌ها</a> •
  <a href="#-پرداخت">پرداخت</a> •
  <a href="#-استقرار">استقرار</a> •
  <a href="README.md">English</a>
</p>

---

## 📋 معرفی

iPBotS یک ربات تلگرام کامل و حرفه‌ای برای فروش کانفیگ‌های V2Ray/Xray است. این ربات به پنل‌های محبوب (3x-ui، Hiddify، Marzban) متصل می‌شود، پرداخت‌ها را مدیریت می‌کند، اشتراک‌ها را کنترل می‌کند و یک تجربه فروشگاهی کامل را از طریق تلگرام ارائه می‌دهد.

با Python مدرن و async (Aiogram 3 + FastAPI + SQLAlchemy) ساخته شده و برای عملکرد بالا، مقیاس‌پذیری و سادگی استقرار طراحی شده.

## ⚡ نصب سریع

```bash
# نصب یک‌خطی:
sudo bash -c "$(curl -sL https://raw.githubusercontent.com/iPmartNetwork/iPBotS/master/install.sh)"
```

یا دستی:

```bash
git clone https://github.com/iPmartNetwork/iPBotS.git
cd iPBotS
sudo bash install.sh
```

بعد از نصب، از دستور `ipbots` استفاده کنید:

```bash
ipbots status     # وضعیت سرویس‌ها
ipbots logs       # مشاهده لاگ‌ها
ipbots restart    # ری‌استارت
ipbots update     # بروزرسانی
ipbots backup     # پشتیبان‌گیری
```

## ✨ ویژگی‌ها

### 🛒 فروشگاه

| ویژگی | توضیح |
|--------|--------|
| دسته‌بندی پلن‌ها | پلن‌های مرتب با آیکون و ترتیب |
| پلن سفارشی | کاربر خودش حجم + مدت + تعداد IP انتخاب می‌کنه |
| تست رایگان | جذب کاربر جدید با سرویس محدود رایگان |
| باندل | فروش چند پلن با هم با تخفیف |
| کد تخفیف | درصدی یا مبلغ ثابت |
| تمدید خودکار | تمدید خودکار از کیف پول قبل از انقضا |
| انتخاب سرور | کاربر لوکیشن دلخواه رو انتخاب می‌کنه |
| QR Code | تولید QR برای لینک اشتراک |
| Deep Link | لینک مستقیم به پلن (`/start plan_5`) |
| ارتقای سرویس | ارتقا به پلن بالاتر از داخل بات |
| انتقال سرویس | انتقال سرویس به شخص دیگه |

### 💰 پرداخت

| درگاه | نوع |
|--------|------|
| زرین‌پال | ریالی (آنلاین) |
| NowPayments | ارز دیجیتال |
| Cryptomus | ارز دیجیتال |
| کارت به کارت | دستی با تأیید ادمین + فعال‌سازی خودکار |
| IDPay | ریالی (آنلاین) |
| کیف پول | موجودی داخلی |

### 👥 سیستم کاربری

| ویژگی | توضیح |
|--------|--------|
| کیف پول | شارژ، برداشت، تاریخچه تراکنش |
| زیرمجموعه | دعوت دوستان، کسب پورسانت (خودکار) |
| باشگاه مشتریان | کسب امتیاز با هر خرید، دریافت جایزه |
| نمایندگی | سیستم نمایندگی با تخفیف پلکانی |
| تیکت | سیستم پشتیبانی تیکتی |
| آموزش | راهنمای اتصال برای تمام پلتفرم‌ها |
| پلن خانوادگی | اشتراک‌گذاری سرویس با اعضای خانواده |
| امتیازدهی | امتیاز و نظر بعد از خرید |

### 🛡️ پنل ادمین

| ویژگی | توضیح |
|--------|--------|
| داشبورد | درآمد، کاربران، سفارشات، آمار لحظه‌ای |
| مدیریت کاربران | جستجو، مسدود/رفع، شارژ، پیام، کیف پول |
| مدیریت سرورها | افزودن/ویرایش/تست/حذف سرور VPN |
| مدیریت پلن‌ها | ساخت/ویرایش/حذف، تخصیص دسته‌بندی و سرور |
| مدیریت پرداخت | تأیید/رد پرداخت‌های کارت به کارت |
| ارسال انبوه | ارسال پیام به همه/فعال‌ها/انتخابی |
| پشتیبان‌گیری | خودکار + دستی |
| گزارش روزانه | گزارش خودکار درآمد و رشد |
| خروجی CSV | خروجی کاربران و پرداخت‌ها |
| صفحه وضعیت | صفحه عمومی سلامت سرورها (`/status`) |

### 🤖 ویژگی‌های هوشمند

| ویژگی | توضیح |
|--------|--------|
| پشتیبانی هوشمند | تطبیق FAQ + اتصال اختیاری به GPT |
| بازاریابی خودکار | بازگرداندن کاربران غیرفعال، پیشنهاد تمدید |
| مانیتورینگ سرور | بررسی سلامت هر 5 دقیقه |
| هشدار ترافیک | اعلان در 80% مصرف |
| اعلان انقضا | هشدار 3 روز قبل از انقضا |
| لاگ عملیات | ثبت تمام اقدامات ادمین |
| جوین اجباری | عضویت اجباری در کانال‌ها (نامحدود) |
| ضد اسپم | محدودیت نرخ با Redis |
| فوروارد همگانی | فوروارد عکس/ویدیو/فایل به همه |
| پیام زمان‌بندی | ارسال پیام در زمان مشخص |
| مدیریت پروتکل | تنظیم پروتکل‌ها برای هر سرور |
| تنظیم متون | تغییر متون ربات توسط ادمین |

### 🖥️ پنل‌ها

| پنل | وضعیت |
|------|--------|
| 3x-ui (سنایی) | ✅ پشتیبانی کامل |
| Hiddify Manager | ✅ پشتیبانی کامل |
| Marzban (مرزبان) | ✅ پشتیبانی کامل |
| Marzneshin (مرزنشین) | ✅ پشتیبانی کامل |

### 🌐 مینی اپ (WebApp)

مینی اپ مدرن تلگرام شامل:
- مرور فروشگاه با دسته‌بندی
- مدیریت سرویس‌ها با نمودار ترافیک
- کیف پول با تاریخچه تراکنش
- پروفایل و سیستم زیرمجموعه
- رابط کاربری ریسپانسیو با تم تاریک

## 🛠️ تکنولوژی‌ها

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

## 🚀 استقرار

### پیش‌نیازها

| مورد | حداقل |
|------|--------|
| سیستم‌عامل | Ubuntu 20.04+ / Debian 11+ |
| RAM | 512 مگابایت |
| دیسک | 5 گیگابایت |
| دامنه | اختیاری (برای حالت webhook) |

### نصب

برای راهنمای کامل نصب [INSTALL.md](INSTALL.md) را ببینید.

### تنظیمات

تمام تنظیمات در فایل `.env` قرار دارد. فایل [.env.example](.env.example) را ببینید.

### مدیریت

```bash
ipbots status      # وضعیت
ipbots start       # شروع
ipbots stop        # توقف
ipbots restart     # ری‌استارت
ipbots logs        # لاگ بات
ipbots logs redis  # لاگ Redis
ipbots update      # بروزرسانی
ipbots backup      # پشتیبان‌گیری
ipbots config      # ویرایش .env
ipbots seed        # داده‌های نمونه
ipbots uninstall   # حذف کامل
```

## 📁 ساختار پروژه

```
iPBotS/
├── bot/                 ربات تلگرام (Aiogram 3)
│   ├── handlers/        هندلرهای پیام و callback
│   │   ├── user/        هندلرهای کاربر (17 ماژول)
│   │   └── admin/       هندلرهای ادمین (8 ماژول)
│   ├── keyboards/       کیبوردهای inline و reply
│   ├── middlewares/     احراز هویت، محدودیت، زبان
│   ├── states/          حالت‌های FSM
│   └── utils/           ابزارها، QR Code
├── core/                منطق کسب‌وکار
│   ├── database/        مدل‌ها، ریپوزیتوری‌ها
│   ├── services/        پنل، پرداخت، AI، بازاریابی
│   └── scheduler/       وظایف پس‌زمینه (12 تسک)
├── api/                 FastAPI (webhook + WebApp API)
├── webapp/              مینی اپ تلگرام (HTML/CSS/JS)
├── locales/             چندزبانه (فارسی + انگلیسی)
├── templates/           صفحات نتیجه پرداخت
├── migrations/          مایگریشن Alembic
├── docker-compose.yml   ارکستراسیون Docker
├── install.sh           نصب‌کننده خودکار و مدیریت
└── nginx.conf.example   تنظیمات Nginx
```

## 🔒 امنیت

- رمزنگاری AES برای پسوردهای پنل در دیتابیس
- Nginx با Rate Limiting و هدرهای امنیتی
- HSTS + TLS 1.2/1.3
- فایروال (UFW) خودکار
- لاگ عملیات ادمین (Audit Log)
- اعتبارسنجی ورودی‌ها
- محدودیت نرخ با Redis

## 📊 آمار پروژه

| متریک | مقدار |
|--------|-------|
| فایل‌ها | 120+ |
| خطوط کد | 13,800+ |
| مدل دیتابیس | 16 |
| هندلر | 25 |
| سرویس | 12 |
| Job زمان‌بندی | 12 |

## 📄 لایسنس

[AGPL-3.0](LICENSE)

---

<p align="center">
  ساخته شده با ❤️ توسط <a href="https://github.com/iPmartNetwork">iPmart Network</a>
</p>
