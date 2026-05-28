"""AI-powered support chat handler."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from core.database.models import User
from core.services.ai_support import ai_support

router = Router(name="ai_chat")


@router.callback_query(F.data == "support:ai")
async def start_ai_chat(callback: CallbackQuery):
    """Start AI support chat."""
    await callback.message.edit_text(
        "🤖 <b>پشتیبانی هوشمند</b>\n\n"
        "سوال خود را بنویسید و من سعی می‌کنم پاسخ بدم.\n\n"
        "💡 مثال‌ها:\n"
        "• چطور وصل بشم؟\n"
        "• سرویسم قطع شده\n"
        "• چطور تمدید کنم؟\n"
        "• سرعت پایینه\n\n"
        "📝 سوال خود را تایپ کنید:"
    )
    await callback.answer()


@router.message(F.text.startswith("🤖"))
async def handle_ai_question(message: Message, db_user: User):
    """Handle AI support question (triggered by prefix)."""
    question = message.text.replace("🤖", "").strip()
    if not question:
        return

    await message.answer("🤖 در حال پردازش...")

    answer = await ai_support.answer_question(question)
    await message.answer(answer)


# Also handle direct questions when in support context
@router.callback_query(F.data == "support:ask_ai")
async def ask_ai_prompt(callback: CallbackQuery):
    """Prompt user to ask AI."""
    await callback.message.edit_text(
        "🤖 سوال خود را بنویسید:\n\n"
        "(هر پیامی که ارسال کنید، توسط هوش مصنوعی پاسخ داده می‌شود)"
    )
    await callback.answer()
