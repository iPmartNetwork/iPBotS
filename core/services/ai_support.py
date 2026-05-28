"""AI-powered support chatbot service."""

import json
from typing import Optional, List, Dict

import aiohttp
from loguru import logger

from bot.config import settings


# FAQ knowledge base
FAQ_KNOWLEDGE = {
    "اتصال": (
        "برای اتصال:\n"
        "1. لینک اشتراک را از بخش «سرویس‌های من» کپی کنید\n"
        "2. اپلیکیشن مناسب را نصب کنید:\n"
        "   - اندروید: v2rayNG یا Hiddify\n"
        "   - آیفون: Streisand یا Hiddify\n"
        "   - ویندوز: v2rayN یا Hiddify Next\n"
        "3. لینک را در اپلیکیشن وارد کنید\n"
        "4. Connect بزنید"
    ),
    "قطع": (
        "اگر سرویس قطع شده:\n"
        "1. ابتدا ترافیک و تاریخ انقضا را بررسی کنید\n"
        "2. اپلیکیشن را ببندید و دوباره باز کنید\n"
        "3. سرور دیگری را امتحان کنید\n"
        "4. اگر مشکل ادامه داشت، تیکت بزنید"
    ),
    "خرید": (
        "برای خرید سرویس:\n"
        "1. از منوی «خرید سرویس» پلن مورد نظر را انتخاب کنید\n"
        "2. روش پرداخت را انتخاب کنید\n"
        "3. پرداخت را انجام دهید\n"
        "4. سرویس خودکار فعال می‌شود"
    ),
    "تمدید": (
        "برای تمدید سرویس:\n"
        "1. به بخش «سرویس‌های من» بروید\n"
        "2. سرویس مورد نظر را انتخاب کنید\n"
        "3. دکمه «تمدید» را بزنید\n"
        "4. پرداخت را انجام دهید\n\n"
        "💡 می‌توانید تمدید خودکار را فعال کنید"
    ),
    "کیف پول": (
        "کیف پول شما:\n"
        "- از منوی «کیف پول» موجودی خود را ببینید\n"
        "- با «شارژ» موجودی اضافه کنید\n"
        "- خرید با کیف پول سریع‌تر و بدون نیاز به درگاه است\n"
        "- درآمد زیرمجموعه به کیف پول واریز می‌شود"
    ),
    "زیرمجموعه": (
        "سیستم زیرمجموعه‌گیری:\n"
        "- لینک دعوت خود را از بخش «زیرمجموعه» کپی کنید\n"
        "- با هر خرید زیرمجموعه، پورسانت دریافت کنید\n"
        "- درآمد قابل برداشت به کیف پول است"
    ),
    "استرداد": (
        "سیاست استرداد:\n"
        "- در صورت عدم استفاده از سرویس، امکان استرداد وجود دارد\n"
        "- برای درخواست استرداد، تیکت بزنید\n"
        "- بررسی و پاسخ ظرف 24 ساعت"
    ),
    "سرعت": (
        "اگر سرعت پایین است:\n"
        "1. سرور دیگری را امتحان کنید\n"
        "2. پروتکل را تغییر دهید\n"
        "3. از بخش «تغییر سرور» لوکیشن نزدیک‌تر انتخاب کنید\n"
        "4. اگر مشکل ادامه داشت، تیکت بزنید"
    ),
}

# Keywords mapping
KEYWORD_MAP = {
    "اتصال": ["وصل", "کانکت", "connect", "اتصال", "نصب", "آموزش", "چطور", "چگونه"],
    "قطع": ["قطع", "کار نمیکنه", "وصل نمیشه", "disconnect", "مشکل", "ارور", "error"],
    "خرید": ["خرید", "بخرم", "سفارش", "پلن", "قیمت", "هزینه"],
    "تمدید": ["تمدید", "renew", "تمام شده", "منقضی", "expire"],
    "کیف پول": ["کیف پول", "موجودی", "شارژ", "wallet", "پول"],
    "زیرمجموعه": ["زیرمجموعه", "دعوت", "referral", "لینک دعوت", "پورسانت"],
    "استرداد": ["استرداد", "برگشت", "refund", "پس بدید", "لغو"],
    "سرعت": ["سرعت", "کند", "slow", "speed", "پینگ", "ping"],
}


class AISupportService:
    """AI-powered support service with FAQ matching and optional GPT."""

    def __init__(self):
        self.openai_api_key = getattr(settings, "OPENAI_API_KEY", "")

    def find_faq_answer(self, question: str) -> Optional[str]:
        """Find answer from FAQ knowledge base using keyword matching."""
        question_lower = question.lower().strip()

        # Score each category
        scores: Dict[str, int] = {}
        for category, keywords in KEYWORD_MAP.items():
            score = 0
            for keyword in keywords:
                if keyword in question_lower:
                    score += 1
            if score > 0:
                scores[category] = score

        if not scores:
            return None

        # Get best match
        best_category = max(scores, key=scores.get)
        return FAQ_KNOWLEDGE.get(best_category)

    async def get_ai_response(self, question: str, context: str = "") -> Optional[str]:
        """Get AI response using OpenAI API (if configured)."""
        if not self.openai_api_key:
            return None

        system_prompt = (
            "تو یک دستیار پشتیبانی ربات فروش VPN هستی. "
            "به فارسی و مختصر پاسخ بده. "
            "اگر سوال خارج از حوزه کاری ربات بود، کاربر را به پشتیبانی انسانی ارجاع بده. "
            "هرگز اطلاعات فنی سرورها یا اطلاعات محرمانه را فاش نکن."
        )

        if context:
            system_prompt += f"\n\nاطلاعات اضافی: {context}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": question},
                        ],
                        "max_tokens": 500,
                        "temperature": 0.7,
                    },
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        logger.error(f"OpenAI API error: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"AI support error: {e}")
            return None

    async def answer_question(self, question: str) -> str:
        """Get the best answer for a user question."""
        # First try FAQ
        faq_answer = self.find_faq_answer(question)
        if faq_answer:
            return f"🤖 <b>پاسخ خودکار:</b>\n\n{faq_answer}"

        # Try AI if available
        ai_answer = await self.get_ai_response(question)
        if ai_answer:
            return f"🤖 <b>پاسخ هوشمند:</b>\n\n{ai_answer}"

        # Fallback
        return (
            "🤖 متوجه سوال شما نشدم.\n\n"
            "💡 می‌توانید:\n"
            "• از بخش «سوالات متداول» استفاده کنید\n"
            "• تیکت پشتیبانی ارسال کنید\n\n"
            "کلمات کلیدی: اتصال، خرید، تمدید، قطع، سرعت، کیف پول"
        )


# Singleton
ai_support = AISupportService()
