# Requirements: iPBotS v2.0 Completion

## Requirement 1: Unit Tests (pytest)
### Title
راه‌اندازی زیرساخت تست و نوشتن تست‌های واحد برای سرویس‌ها و هندلرها

### User Story
به عنوان توسعه‌دهنده، می‌خوام تست‌های خودکار داشته باشم تا از صحت عملکرد سرویس‌ها مطمئن بشم.

### Acceptance Criteria
- [ ] pytest + pytest-asyncio + pytest-cov نصب و کانفیگ شده
- [ ] فیکسچرهای پایه (mock database, mock bot, mock redis) ساخته شده
- [ ] تست‌های واحد برای payment services (ZarinPal, Stripe, NowPayments)
- [ ] تست‌های واحد برای DynamicPricingService
- [ ] تست‌های واحد برای CurrencyService
- [ ] تست‌های واحد برای ABTest و get_variant
- [ ] تست‌های واحد برای ChurnPredictionService
- [ ] CI pipeline آپدیت شده برای اجرای تست‌ها
- [ ] Coverage حداقل 60% برای core/services

---

## Requirement 2: Swagger API Documentation
### Title
فعال‌سازی مستندات خودکار API با Swagger/OpenAPI

### User Story
به عنوان توسعه‌دهنده/ادمین، می‌خوام مستندات API رو ببینم و تست کنم.

### Acceptance Criteria
- [ ] docs_url و redoc_url در FastAPI فعال شده
- [ ] همه endpointها response_model دارن
- [ ] Pydantic schemas برای request/response تعریف شده
- [ ] Authentication (API Key) در Swagger قابل تست باشه
- [ ] Public API router در app.py رجیستر شده
- [ ] Stripe callback endpoint اضافه شده
- [ ] IDPay callback endpoint اضافه شده

---

## Requirement 3: A/B Testing & Dynamic Pricing Handlers
### Title
تکمیل هندلرهای بات برای A/B Testing و Dynamic Pricing

### User Story
به عنوان ادمین، می‌خوام تست‌های A/B رو مدیریت کنم و قیمت‌گذاری پویا رو کنترل کنم.

### Acceptance Criteria
- [ ] مدل ABTest به core/database/models منتقل شده و migration ساخته شده
- [ ] هندلر ادمین برای ساخت/ویرایش/حذف A/B test
- [ ] هندلر ادمین برای مشاهده نتایج A/B test
- [ ] Dynamic Pricing در فلوی خرید (shop handler) اینتگریت شده
- [ ] نمایش تخفیف پویا به کاربر هنگام خرید
- [ ] هندلر ادمین برای تنظیم پارامترهای Dynamic Pricing

---

## Requirement 4: Stripe & Multi-Currency Handlers
### Title
تکمیل پرداخت Stripe و پشتیبانی چندارزی

### User Story
به عنوان کاربر بین‌المللی، می‌خوام با Stripe و ارز خودم پرداخت کنم.

### Acceptance Criteria
- [ ] STRIPE_SECRET_KEY و STRIPE_CALLBACK_URL به Settings اضافه شده
- [ ] StripeService در payment/__init__.py اکسپورت شده
- [ ] Stripe callback endpoint در api/app.py اضافه شده
- [ ] انتخاب ارز در فلوی خرید (USD, EUR, TRY, RUB, AED)
- [ ] نمایش قیمت به ارز انتخابی کاربر
- [ ] ذخیره ارز ترجیحی کاربر در دیتابیس
- [ ] CurrencyService در shop handler اینتگریت شده

---

## Requirement 5: Admin Web Panel (React)
### Title
پنل وب مدیریت با React

### User Story
به عنوان ادمین، می‌خوام از طریق مرورگر بات رو مدیریت کنم.

### Acceptance Criteria
- [ ] پروژه React (Vite + TypeScript) ساخته شده در پوشه admin-panel/
- [ ] صفحه لاگین با API Key
- [ ] داشبورد با آمار کلی (users, subscriptions, revenue)
- [ ] مدیریت کاربران (لیست، جستجو، بن/آنبن)
- [ ] مدیریت پلن‌ها (CRUD)
- [ ] مدیریت سرورها (لیست، وضعیت)
- [ ] مشاهده پرداخت‌ها
- [ ] API endpoints مورد نیاز پنل ساخته شده

---

## Requirement 6: Bot API to Mini App Connection
### Title
اتصال کامل Bot API به Telegram Mini App

### User Story
به عنوان کاربر، می‌خوام از Mini App داخل تلگرام خرید و مدیریت سرویس انجام بدم.

### Acceptance Criteria
- [ ] WebApp API endpoints تکمیل شده (خرید، پرداخت، تمدید)
- [ ] endpoint خرید پلن از Mini App
- [ ] endpoint ایجاد سفارش و redirect به درگاه
- [ ] باگ hmac.new → hmac.new در webapp.py رفع شده
- [ ] Mini App frontend (HTML/JS) آپدیت شده
- [ ] Deep linking از بات به Mini App
