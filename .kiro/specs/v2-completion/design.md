# Design: iPBotS v2.0 Completion

## Architecture Overview

پروژه iPBotS یک Telegram Bot برای فروش سرویس V2Ray/VPN است. ساختار فعلی:

```
├── bot/          # Telegram bot (aiogram 3)
├── core/         # Business logic & services
├── api/          # FastAPI web server
├── webapp/       # Telegram Mini App (static HTML/JS)
├── admin-panel/  # [NEW] React admin panel
└── tests/        # [NEW] pytest test suite
```

---

## Design 1: Unit Tests Infrastructure

### Structure
```
tests/
├── conftest.py          # Shared fixtures
├── test_services/
│   ├── test_dynamic_pricing.py
│   ├── test_currency.py
│   ├── test_ab_testing.py
│   ├── test_churn_prediction.py
│   └── test_payments/
│       ├── test_stripe.py
│       ├── test_zarinpal.py
│       └── test_nowpayments.py
├── test_api/
│   ├── test_public_api.py
│   └── test_webapp_api.py
└── test_handlers/
    └── test_shop.py
```

### Key Decisions
- **pytest-asyncio** for async test support
- **unittest.mock + aioresponses** for mocking HTTP calls
- **Factory pattern** for test data (no real DB needed for unit tests)
- **httpx.AsyncClient** for FastAPI endpoint testing

### Configuration
- `pyproject.toml` → pytest config section
- `conftest.py` → shared fixtures (mock settings, mock session)

---

## Design 2: Swagger API Documentation

### Changes
1. Enable `docs_url="/docs"` and `redoc_url="/redoc"` in FastAPI app
2. Add `SecurityScheme` for API Key header authentication
3. Create Pydantic response models for all endpoints
4. Register `public_api` router in `app.py`
5. Add missing callback endpoints (Stripe, IDPay)

### New Endpoints
- `GET /api/payment/stripe/callback` — Stripe checkout success
- `POST /api/payment/idpay/callback` — IDPay callback
- `GET /docs` — Swagger UI
- `GET /redoc` — ReDoc UI

---

## Design 3: A/B Testing & Dynamic Pricing Handlers

### A/B Testing
1. Move `ABTest` model to `core/database/models/ab_test.py`
2. Create Alembic migration
3. Admin handler: `/admin` → "A/B Tests" button → list/create/view results
4. Integration: Use `get_variant()` in shop messages to show different texts

### Dynamic Pricing
1. Admin handler: `/admin` → "Dynamic Pricing" → configure parameters
2. Integration in `bot/handlers/user/shop.py`:
   - Before showing price, call `dynamic_pricing.calculate_discount()`
   - Show original price + discounted price + reason
3. Store config in Redis for fast access

### Bot Flow
```
User clicks "Buy" → shop handler → dynamic_pricing.calculate_discount()
  → Show: "قیمت: ~~50,000~~ → 42,500 تومان (ساعات کم‌ترافیک 15%)"
```

---

## Design 4: Stripe & Multi-Currency

### Config Changes
Add to `Settings`:
```python
STRIPE_SECRET_KEY: str = ""
STRIPE_CALLBACK_URL: str = ""
STRIPE_WEBHOOK_SECRET: str = ""
```

### Flow
1. User selects plan → chooses currency (if international payment)
2. Price converted via `CurrencyService`
3. Stripe checkout session created with correct currency
4. User redirected to Stripe → pays → callback verifies

### Database Changes
- Add `preferred_currency: str = "IRT"` to User model
- Migration for new column

### API Callback
```python
@app.get("/api/payment/stripe/callback")
async def stripe_callback(session_id: str, order_id: str):
    # Verify with Stripe API
    # Update order status
    # Create subscription
```

---

## Design 5: Admin Web Panel (React)

### Tech Stack
- Vite + React 18 + TypeScript
- TailwindCSS for styling
- React Router for navigation
- Axios for API calls
- Recharts for dashboard charts

### Pages
1. `/login` — API key authentication
2. `/dashboard` — Stats overview + charts
3. `/users` — User management table
4. `/plans` — Plan CRUD
5. `/servers` — Server status
6. `/payments` — Payment history
7. `/settings` — Bot settings

### API Requirements (new endpoints needed)
```
GET  /api/admin/dashboard    — Stats + charts data
GET  /api/admin/users        — Paginated user list
POST /api/admin/users/:id/ban
GET  /api/admin/plans        — All plans
POST /api/admin/plans        — Create plan
PUT  /api/admin/plans/:id    — Update plan
GET  /api/admin/servers      — Server list + status
GET  /api/admin/payments     — Payment history
```

---

## Design 6: Mini App Connection

### Bug Fix
`webapp.py` line: `hmac.new(...)` → `hmac.new(...)` — Python's hmac module uses `hmac.new()` which is correct, but the import might be wrong. Need to verify.

### New WebApp Endpoints
```
POST /api/webapp/order/create    — Create order from Mini App
POST /api/webapp/order/pay       — Initiate payment
GET  /api/webapp/order/:id       — Order status
POST /api/webapp/wallet/charge   — Charge wallet
```

### Bot Integration
- Add WebApp button to main menu keyboard
- Deep link: `t.me/bot?startapp=shop` → opens Mini App

---

## Dependency Changes

### New packages (requirements.txt additions)
```
# Testing
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
aioresponses==0.7.7
httpx==0.28.1

# Stripe (already using aiohttp, no new dep needed)
stripe==11.3.0  # Optional: official SDK alternative
```

---

## Implementation Priority

1. **Bug fixes & wiring** (register missing routers, fix hmac) — Quick wins
2. **Unit Tests** — Foundation for safe changes
3. **Swagger docs** — Visibility into API
4. **Stripe & Multi-Currency** — Revenue feature
5. **A/B Testing & Dynamic Pricing** — Optimization
6. **Mini App completion** — UX improvement
7. **Admin Panel (React)** — Largest scope, last
