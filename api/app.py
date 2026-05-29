"""FastAPI application for webhooks and payment callbacks."""

import asyncio

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from loguru import logger
import uvicorn

from bot.config import settings

app = FastAPI(title="V2Ray Shop Bot API - iPmart Network", docs_url=None, redoc_url=None)

# Serve WebApp static files
app.mount("/webapp", StaticFiles(directory="webapp", html=True), name="webapp")


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

            # TODO: Create subscription (trigger from here)

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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


# Include WebApp API routes
from api.routes.webapp import router as webapp_router
app.include_router(webapp_router)


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
