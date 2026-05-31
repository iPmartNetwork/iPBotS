# Tasks: iPBotS v2.0 Completion

## Phase 1: Bug Fixes & Wiring (Quick Wins)

### Task 1.1: Register missing routers and handlers
- [x] Add `public_api` router to `api/app.py`
- [x] Add `leaderboard` and `test_connection` routers to admin `__init__.py`
- [x] Add `review` router to user `__init__.py`
- [x] Export `StripeService` in `core/services/payment/__init__.py`
- [x] Verified `hmac.new` is correct (no bug)

### Task 1.2: Add Stripe config to Settings
- [x] Add `STRIPE_SECRET_KEY`, `STRIPE_CALLBACK_URL`, `STRIPE_WEBHOOK_SECRET` to `bot/config.py`
- [x] Add `preferred_currency` field to User model
- [x] Create Alembic migration

---

## Phase 2: Unit Tests

### Task 2.1: Setup test infrastructure
- [x] Add test dependencies to `requirements.txt`
- [x] Create `pyproject.toml` with pytest config
- [x] Create `tests/__init__.py`
- [x] Create `tests/conftest.py` with shared fixtures

### Task 2.2: Write service tests
- [x] `tests/test_services/test_dynamic_pricing.py`
- [x] `tests/test_services/test_currency.py`
- [x] `tests/test_services/test_ab_testing.py`
- [x] `tests/test_services/test_churn_prediction.py`

### Task 2.3: Write payment service tests
- [x] `tests/test_services/test_payments/test_stripe.py`
- [x] `tests/test_services/test_payments/test_zarinpal.py`

### Task 2.4: Write API tests
- [x] `tests/test_api/test_public_api.py`
- [x] `tests/test_api/test_health.py` (included in test_public_api.py)

### Task 2.5: Update CI pipeline
- [x] Add pytest step to `.github/workflows/ci.yml`
- [x] Add coverage reporting

---

## Phase 3: Swagger API Documentation

### Task 3.1: Enable Swagger and add schemas
- [x] Enable `docs_url` and `redoc_url` in `api/app.py`
- [x] Add OpenAPI security scheme for API Key
- [x] Create Pydantic response/request models in `api/schemas.py`
- [x] Add response_model to all existing endpoints

### Task 3.2: Add missing callback endpoints
- [x] Add Stripe callback endpoint to `api/app.py`
- [x] Add IDPay callback endpoint to `api/app.py`
- [x] Document all endpoints with descriptions

---

## Phase 4: Stripe & Multi-Currency

### Task 4.1: Complete Stripe integration
- [x] Add Stripe callback endpoint (verify session, update order)
- [x] Add Stripe as payment option in shop handler
- [x] Create inline keyboard for payment method selection (ZarinPal/Stripe/Crypto)

### Task 4.2: Multi-currency in bot
- [x] Add currency selection to user settings/shop flow (preferred_currency in User model)
- [x] Integrate `CurrencyService` in webapp order/pay flow
- [x] Show prices in user's preferred currency (Stripe uses USD conversion)
- [x] Store user currency preference

---

## Phase 5: A/B Testing & Dynamic Pricing Handlers

### Task 5.1: A/B Testing setup
- [x] Move ABTest model to `core/database/models/ab_test.py`
- [x] Register in models `__init__.py`
- [x] Create Alembic migration
- [x] Create admin handler `bot/handlers/admin/ab_testing.py`
- [x] Register in admin `__init__.py`

### Task 5.2: Dynamic Pricing integration
- [x] Create admin handler `bot/handlers/admin/dynamic_pricing.py`
- [x] Integrate into webapp order creation flow (dynamic pricing applied)
- [x] Integrate into `bot/handlers/user/shop.py` purchase flow
- [x] Show dynamic discount to user with strikethrough original price

---

## Phase 6: Mini App Connection

### Task 6.1: Complete WebApp API
- [x] Add `POST /api/webapp/order/create` endpoint
- [x] Add `POST /api/webapp/order/pay` endpoint
- [x] Add `GET /api/webapp/order/{id}` endpoint
- [x] Add `POST /api/webapp/wallet/charge` endpoint
- [x] Verified hmac verification is correct

### Task 6.2: Bot ↔ Mini App integration
- [x] Add WebApp button to main menu keyboard
- [x] Handle Mini App deep links
- [x] Send order confirmation back to bot chat after Mini App purchase

---

## Phase 7: Admin Web Panel (React)

### Task 7.1: Project setup
- [x] Initialize Vite + React + TypeScript project in `admin-panel/`
- [x] Setup TailwindCSS
- [x] Setup React Router
- [x] Create base layout (sidebar, header)

### Task 7.2: Admin API endpoints
- [x] Create `api/routes/admin_api.py` with all admin endpoints
- [x] Dashboard stats endpoint
- [x] Users CRUD endpoints
- [x] Plans CRUD endpoints
- [x] Servers list endpoint
- [x] Payments list endpoint

### Task 7.3: React pages
- [x] Login page
- [x] Dashboard page with cards
- [x] Users management page
- [x] Plans management page
- [x] Servers status page
- [x] Payments page

### Task 7.4: Build & deploy config
- [x] Vite config with API proxy
- [x] Serve built files from FastAPI (static/admin mount)
- [x] Add to Docker setup (multi-stage build with Node.js)
