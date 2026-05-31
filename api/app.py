"""FastAPI application for webhooks and payment callbacks."""

import asyncio
import os

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from loguru import logger
import uvicorn

from bot.config import settings

app = FastAPI(
    title="V2Ray Shop Bot API - iPmart Network",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    description="iPBotS API - Telegram Bot for V2Ray/VPN service management",
)


def custom_openapi():
    """Custom OpenAPI schema with API Key security."""
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
        }
    }
    openapi_schema["security"] = [{"ApiKeyHeader": []}]
    app.openapi_schema = openapi_schema
    return openapi_schema


app.openapi = custom_openapi

# Serve WebApp static files
if os.path.exists("webapp"):
    app.mount("/webapp", StaticFiles(directory="webapp", html=True), name="webapp")

# Serve Admin Panel (React build)
if os.path.exists("static/admin"):
    app.mount("/admin", StaticFiles(directory="static/admin", html=True), name="admin")


@app.post(settings.WEBHOOK_PATH)
async def telegram_webhook(request: Request) -> Response:
    """Handle Telegram webhook updates."""
    from aiogram.types import Update
    from bot.loader import bot, dp

    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot=bot, update=update)
    except Exception as e:
        logger.error(f"Webhook error: {e}")

    return Response(status_code=200)


async def _notify_user_payment_success(user_id: int, order_amount: int, method: str):
    """Send payment confirmation to user via bot after successful payment."""
    try:
        from bot.loader import bot
        from core.database.engine import get_session
        from core.database.models import User
        from sqlalchemy import select

        async with get_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

        if user:
            method_names = {
                "zarinpal": "زرین‌پال",
                "stripe": "Stripe",
                "nowpayments": "ارز دیجیتال",
                "idpay": "آیدی‌پی",
            }
            method_name = method_names.get(method, method)

            await bot.send_message(
                user.telegram_id,
                f"✅ <b>پرداخت موفق!</b>\n\n"
                f"💰 مبلغ: {order_amount:,} تومان\n"
                f"💳 روش: {method_name}\n\n"
                f"⏳ سرویس شما در حال فعال‌سازی است...\n"
                f"📱 از منوی «سرویس‌های من» وضعیت را بررسی کنید.",
            )
    except Exception as e:
        logger.error(f"Failed to notify user {user_id}: {e}")


@app.get("/api/payment/zarinpal/callback")
async def zarinpal_callback(request: Request):
    """Handle ZarinPal payment callback."""
    from core.services.payment.zarinpal import ZarinPalService
    from core.database.engine import get_session
    from core.database.models import Order, OrderStatus, Payment, PaymentStatus
    from sqlalchemy import select

    authority = request.query_params.get("Authority", "")
    status = request.query_params.get("Status", "")
    order_id = request.query_params.get("order_id", "")

    if status != "OK":
        return Response(content="Payment cancelled", status_code=200)

    async with get_session() as session:
        order = await session.get(Order, int(order_id))
        if not order:
            return Response(content="Order not found", status_code=404)

        # Verify payment
        zarinpal = ZarinPalService()
        result = await zarinpal.verify_payment(authority, order.amount)

        if result.success:
            order.status = OrderStatus.PAID
            order.payment_id = result.ref_id

            # Create payment record
            payment = Payment(
                user_id=order.user_id,
                order_id=order.id,
                method="zarinpal",
                status=PaymentStatus.COMPLETED,
                amount=order.amount,
                gateway_transaction_id=authority,
                gateway_ref_id=result.ref_id,
            )
            session.add(payment)

            logger.info(f"Payment verified: order={order_id}, ref={result.ref_id}")

            # Notify user via bot
            await _notify_user_payment_success(order.user_id, order.amount, "zarinpal")

            return Response(
                content="<h1>پرداخت موفق</h1><p>به ربات بازگردید.</p>",
                media_type="text/html",
                status_code=200,
            )
        else:
            order.status = OrderStatus.FAILED
            return Response(
                content=f"<h1>خطا در پرداخت</h1><p>{result.error}</p>",
                media_type="text/html",
                status_code=200,
            )


@app.post("/api/payment/nowpayments/callback")
async def nowpayments_callback(request: Request):
    """Handle NowPayments IPN callback."""
    from core.services.payment.nowpayments import NowPaymentsService
    from core.database.engine import get_session
    from core.database.models import Order, OrderStatus, Payment, PaymentStatus
    from sqlalchemy import select

    data = await request.json()
    signature = request.headers.get("x-nowpayments-sig", "")

    nowpay = NowPaymentsService()

    # Verify signature
    if not nowpay.verify_ipn_signature(data, signature):
        logger.warning("Invalid NowPayments IPN signature")
        return Response(status_code=400)

    payment_status = data.get("payment_status", "")
    order_id = data.get("order_id", "")

    if payment_status in ("finished", "confirmed"):
        async with get_session() as session:
            order = await session.get(Order, int(order_id))
            if order:
                order.status = OrderStatus.PAID

                payment = Payment(
                    user_id=order.user_id,
                    order_id=order.id,
                    method="nowpayments",
                    status=PaymentStatus.COMPLETED,
                    amount=order.amount,
                    gateway_transaction_id=str(data.get("payment_id", "")),
                )
                session.add(payment)

                # Notify user via bot
                await _notify_user_payment_success(order.user_id, order.amount, "nowpayments")

        logger.info(f"NowPayments confirmed: order={order_id}")

    return Response(status_code=200)


@app.get("/status")
async def status_page(request: Request):
    """Public server status page."""
    from core.services.health_check import health_checker
    from datetime import datetime

    results = health_checker._last_results

    servers_html = ""
    all_online = True

    if not results:
        servers_html = '<div class="all-ok">🔄 در حال بارگذاری...</div>'
    else:
        for server_id, result in results.items():
            status_class = "online" if result["is_online"] else "offline"
            if not result["is_online"]:
                all_online = False
            ping_text = f'{result["ping_ms"]}ms' if result["ping_ms"] else "—"
            servers_html += f'''
            <div class="server">
                <div class="status-dot {status_class}"></div>
                <div class="server-info">
                    <div class="server-name">{result["server_name"]}</div>
                    <div class="server-meta">{"🟢 آنلاین" if result["is_online"] else "🔴 آفلاین"}</div>
                </div>
                <div class="ping">{ping_text}</div>
            </div>'''

        if all_online:
            servers_html = '<div class="all-ok">✅ تمام سرورها آنلاین هستند</div>' + servers_html

    last_update = datetime.now().strftime("%H:%M:%S")

    html = open("templates/status.html").read()
    html = html.replace("{{ servers_html }}", servers_html)
    html = html.replace("{{ last_update }}", last_update)

    return Response(content=html, media_type="text/html")


@app.get("/health", summary="Health check", tags=["system"])
async def health_check():
    """Health check endpoint. Returns 200 if the service is running."""
    return {"status": "ok"}


@app.get("/api/payment/stripe/callback")
async def stripe_callback(request: Request):
    """Handle Stripe checkout session callback."""
    from core.services.payment.stripe_pay import StripeService
    from core.database.engine import get_session
    from core.database.models import Order, OrderStatus, Payment, PaymentStatus

    session_id = request.query_params.get("session_id", "")
    order_id = request.query_params.get("order_id", "")
    cancelled = request.query_params.get("cancelled", "")

    if cancelled:
        return Response(
            content="<h1>Payment Cancelled</h1><p>You can return to the bot.</p>",
            media_type="text/html",
            status_code=200,
        )

    if not session_id or not order_id:
        return Response(content="Missing parameters", status_code=400)

    async with get_session() as session:
        order = await session.get(Order, int(order_id))
        if not order:
            return Response(content="Order not found", status_code=404)

        stripe_svc = StripeService()
        result = await stripe_svc.verify_payment(session_id, order.amount)

        if result.success:
            order.status = OrderStatus.PAID
            order.payment_id = result.ref_id

            payment = Payment(
                user_id=order.user_id,
                order_id=order.id,
                method="stripe",
                status=PaymentStatus.COMPLETED,
                amount=order.amount,
                gateway_transaction_id=session_id,
                gateway_ref_id=result.ref_id,
            )
            session.add(payment)

            logger.info(f"Stripe payment verified: order={order_id}, ref={result.ref_id}")

            # Notify user via bot
            await _notify_user_payment_success(order.user_id, order.amount, "stripe")

            return Response(
                content="<h1>Payment Successful</h1><p>Return to the bot.</p>",
                media_type="text/html",
                status_code=200,
            )
        else:
            order.status = OrderStatus.FAILED
            return Response(
                content=f"<h1>Payment Failed</h1><p>{result.error}</p>",
                media_type="text/html",
                status_code=200,
            )


@app.post("/api/payment/idpay/callback")
async def idpay_callback(request: Request):
    """Handle IDPay payment callback."""
    from core.services.payment.idpay import IDPayService
    from core.database.engine import get_session
    from core.database.models import Order, OrderStatus, Payment, PaymentStatus

    data = await request.json()

    status = data.get("status", 0)
    order_id = data.get("order_id", "")
    track_id = data.get("track_id", "")
    payment_id = data.get("id", "")

    # IDPay status codes: 100 = paid, 101 = already verified
    if status not in (100, 101):
        return Response(status_code=200)

    async with get_session() as session:
        order = await session.get(Order, int(order_id))
        if not order:
            return Response(status_code=404)

        idpay_svc = IDPayService()
        result = await idpay_svc.verify_payment(payment_id, order.amount)

        if result.success:
            order.status = OrderStatus.PAID
            order.payment_id = result.ref_id

            payment = Payment(
                user_id=order.user_id,
                order_id=order.id,
                method="idpay",
                status=PaymentStatus.COMPLETED,
                amount=order.amount,
                gateway_transaction_id=payment_id,
                gateway_ref_id=str(track_id),
            )
            session.add(payment)

            logger.info(f"IDPay payment verified: order={order_id}, track={track_id}")

            # Notify user via bot
            await _notify_user_payment_success(order.user_id, order.amount, "idpay")

    return Response(status_code=200)


# Include WebApp API routes
from api.routes.webapp import router as webapp_router
app.include_router(webapp_router)

# Include Public API routes
from api.routes.public_api import router as public_api_router
app.include_router(public_api_router)

# Include Admin API routes
from api.routes.admin_api import router as admin_api_router
app.include_router(admin_api_router)


async def run_webhook_server():
    """Run the webhook server."""
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=settings.WEBHOOK_PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()
