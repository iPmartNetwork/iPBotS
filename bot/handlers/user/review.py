"""Post-purchase review/rating handler."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy import select

from core.database.engine import get_session
from core.database.models import User, Subscription
from core.database.models.review import Review

router = Router(name="review")


class ReviewStates(StatesGroup):
    waiting_comment = State()


@router.callback_query(F.data.startswith("review:rate:"))
async def rate_service(callback: CallbackQuery, state: FSMContext, db_user: User):
    """Rate a subscription (1-5 stars)."""
    parts = callback.data.split(":")
    sub_id = int(parts[2])
    rating = int(parts[3])

    await state.update_data(review_sub_id=sub_id, review_rating=rating)

    stars = "⭐" * rating + "☆" * (5 - rating)
    await callback.message.edit_text(
        f"⭐ <b>امتیاز شما: {stars}</b>\n\n"
        f"💬 نظر خود را بنویسید (اختیاری):\n"
        f"یا /skip برای رد شدن"
    )
    await state.set_state(ReviewStates.waiting_comment)
    await callback.answer()


@router.message(ReviewStates.waiting_comment)
async def process_review_comment(message: Message, state: FSMContext, db_user: User):
    """Process review comment."""
    data = await state.get_data()
    sub_id = data.get("review_sub_id")
    rating = data.get("review_rating", 5)

    comment = None
    if message.text and not message.text.startswith("/skip"):
        comment = message.text.strip()[:500]

    async with get_session() as session:
        # Get server name
        sub = await session.get(Subscription, sub_id)
        server_name = ""
        if sub and sub.server_id:
            from core.database.models import Server
            server = await session.get(Server, sub.server_id)
            server_name = server.name if server else ""

        review = Review(
            user_id=db_user.id,
            subscription_id=sub_id,
            rating=rating,
            comment=comment,
            server_name=server_name,
        )
        session.add(review)

    stars = "⭐" * rating
    await message.answer(
        f"✅ <b>ممنون از نظر شما!</b>\n\n"
        f"امتیاز: {stars}\n"
        f"{'💬 نظر: ' + comment if comment else ''}"
    )
    await state.clear()


@router.callback_query(F.data.startswith("review:ask:"))
async def ask_review(callback: CallbackQuery, db_user: User):
    """Ask user to rate their service."""
    sub_id = int(callback.data.split(":")[2])

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⭐", callback_data=f"review:rate:{sub_id}:1"),
        InlineKeyboardButton(text="⭐⭐", callback_data=f"review:rate:{sub_id}:2"),
        InlineKeyboardButton(text="⭐⭐⭐", callback_data=f"review:rate:{sub_id}:3"),
        InlineKeyboardButton(text="⭐⭐⭐⭐", callback_data=f"review:rate:{sub_id}:4"),
        InlineKeyboardButton(text="⭐⭐⭐⭐⭐", callback_data=f"review:rate:{sub_id}:5"),
    )
    builder.row(
        InlineKeyboardButton(text="❌ بعداً", callback_data="noop"),
    )

    await callback.message.edit_text(
        "⭐ <b>نظرسنجی</b>\n\n"
        "از سرویس خود راضی بودید؟\n"
        "لطفاً امتیاز دهید:",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()
