# 🏆 iPBotS v1.5.0 — Complete Feature Set

<p align="center">
  <img src="https://raw.githubusercontent.com/iPmartNetwork/iPBotS/master/img/iPBotS.png" width="100">
</p>

<p align="center">
  <b>تمام ویژگی‌ها تکمیل شد — آماده Production</b><br>
  <sub>© <a href="https://github.com/iPmartNetwork">iPmart Network</a></sub>
</p>

---

## 🆕 ویژگی‌های جدید

### ⭐ تجربه کاربری (سطح 3)

| ویژگی | توضیح |
|--------|--------|
| ⭐ نظرسنجی بعد خرید | امتیاز 1-5 + نظر متنی |
| 🏆 لیدربورد نمایندگان | رتبه‌بندی بر اساس فروش |
| 🔗 Webhook خارجی | ارسال رویدادها به Discord/Zapier |
| 🌐 3 زبان جدید | عربی، ترکی، روسی |

### 🤖 هوش و اتوماسیون (سطح 4)

| ویژگی | توضیح |
|--------|--------|
| 📊 قیمت‌گذاری پویا | تخفیف خودکار ساعات/روزهای کم‌تقاضا |
| 📉 پیش‌بینی ریزش | امتیاز ریسک 0-100 با تحلیل عوامل |
| 🧪 A/B Testing | تخصیص قطعی + ردیابی نرخ تبدیل |
| 🔌 Bot API عمومی | REST API با احراز هویت |

### 🌐 بین‌المللی (سطح 5)

| ویژگی | توضیح |
|--------|--------|
| 💳 Stripe | پرداخت کارت بین‌المللی (USD) |
| 💱 چند ارز | تبدیل IRT/USD/EUR/TRY/RUB/AED |

---

## 📊 آمار نهایی پروژه

| متریک | مقدار |
|--------|-------|
| فایل‌ها | **165+** |
| خطوط کد | **20,000+** |
| مدل دیتابیس | **27** |
| پنل VPN | **7** |
| درگاه پرداخت | **6** |
| زبان | **5** |
| سرویس هوشمند | **6** |
| Middleware | **5** |
| Scheduled Job | **12** |

---

## 🖥️ پنل‌ها

```
3x-ui • Hiddify • Marzban • Marzneshin • IBSng • Mikrotik • WGDashboard
```

## 💳 درگاه‌ها

```
ZarinPal • IDPay • NowPayments • Cryptomus • Card2Card • Stripe
```

## 🌐 زبان‌ها

```
فارسی • English • العربية • Türkçe • Русский
```

---

## 🔌 Bot API

```bash
# آمار
curl -H "X-API-KEY: your-secret" https://domain.com/api/v1/stats

# اطلاعات کاربر
curl -H "X-API-KEY: your-secret" https://domain.com/api/v1/user/123456789

# لیست پلن‌ها
curl -H "X-API-KEY: your-secret" https://domain.com/api/v1/plans
```

---

## ⚡ نصب / آپدیت

```bash
# نصب:
sudo bash -c "$(curl -sL https://raw.githubusercontent.com/iPmartNetwork/iPBotS/master/install.sh)"

# آپدیت:
cd /opt/iPBotS
git fetch origin && git reset --hard origin/master
docker compose build --no-cache && docker compose up -d --force-recreate
```

---

## 🏆 مقایسه نهایی

| ویژگی | iPBotS | MirzaBot | ZanborPanel | PowerPs |
|--------|:------:|:--------:|:-----------:|:-------:|
| پنل‌ها | **7** | 7+ | 2 | 2 |
| درگاه | **6** | 3 | 4 | 3 |
| زبان | **5** | 1 | 1 | 1 |
| Docker | ✅ | ❌ | ❌ | ❌ |
| Mini App | ✅ | ❌ | ❌ | ✅ |
| AI Support | ✅ | ❌ | ❌ | ❌ |
| A/B Testing | ✅ | ❌ | ❌ | ❌ |
| Dynamic Pricing | ✅ | ❌ | ❌ | ❌ |
| Churn Prediction | ✅ | ❌ | ❌ | ❌ |
| Bot API | ✅ | ❌ | ❌ | ❌ |
| Stripe | ✅ | ❌ | ❌ | ❌ |
| Multi-Currency | ✅ | ❌ | ❌ | ❌ |
| Webhook | ✅ | ❌ | ❌ | ❌ |
| CI/CD | ✅ | ❌ | ❌ | ❌ |

---

<p align="center">
  <sub><b>© 2024-2026 iPmart Network</b></sub><br>
  <sub>The most complete V2Ray shop bot. Period. 🏆</sub>
</p>
