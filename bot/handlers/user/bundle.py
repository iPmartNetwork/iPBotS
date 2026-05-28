"""Bundle (package deal) handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.database.engine import get_session
from core.database.models import User
from core.database.models.bundle import Bundle, BundleItem

router = Router(name="bundle")


@router.callback_query(F.data == "shop:bundles")
async def show_bundles(callback: CallbackQuery):
    """Show available bundles."""
    async with get_session() as session:
        stmt = (
            select(Bundle)
            .where(Bundle.is_active == True)
            .where((Bundle.stock == -1) | (Bundle.stock > 0))
            .options(selectinload(Bundle.items).selectinload(BundleItem.plan))
            .order_by(Bundle.sort_order)
        )
        result = await session.execute(stmt)
        bundles = result.scalars().all()

    if not bundles:
        await callback.answer("⚠️ باندلی موجود نیست.", show_alert=True)
        return

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()

    text = "📦 <b>باندل‌ها (پکیج‌های ویژه)</b>\n\n"
    text += "💡 با خرید باندل، چند سرویس رو با تخفیف ویژه بگیرید!\n\n"

    for bundle in bundles:
        text += (
            f"{bundle.icon} <b>{bundle.name}</b>\n"
            f"   💰 <s>{bundle.original_price:,}</s> → <b>{bundle.bundle_price:,}</b> تومان\n"
            f"   🏷️ صرفه‌جویی: {bundle.savings:,} تومان ({bundle.savings_percent}%)\n"
        )

        # Show items
        for item in bundle.items:
            if item.plan:
                text += f"   • {item.plan.name} x{item.quantity}\n"
        text += "\n"

        builder.row(
            InlineKeyboardButton(
                text=f"{bundle.icon} خرید {bundle.name} ({bundle.bundle_price:,} ت)",
                callback_data=f"bundle:buy:{bundle.id}",
            )
        )

    builder.row(
        InlineKeyboardButton(text="🔙 بازگشت", callback_data="shop:categories")
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("bundle:buy:"))
async def buy_bundle(callback: CallbackQuery, db_user: User):
    """Show bundle purchase options."""
    bundle_id = int(callback.data.split(":")[2])

    async with get_session() as session:
        stmt = (
            select(Bundle)
            .where(Bundle.id == bundle_id)
            .options(selectinload(Bundle.items).selectinload(BundleItem.plan))
        )
        result = await session.execute(stmt)
        bundle = result.scalar_one_or_none()

    if not bundle:
        await callback.answer("⚠️ باندل یافت نشد.", show_alert=True)
        return

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    # Show quantity options if bulk is available
    if bundle.max_quantity > 1:
        text = (
            f"{bundle.icon} <b>{bundle.name}</b>\n\n"
            f"💰 قیمت واحد: {bundle.bundle_price:,} تومان\n"
        )

        if bundle.bulk_discount_per_unit > 0:
            text += f"🏷️ تخفیف هر واحد اضافه: {bundle.bulk_discount_per_unit:,} تومان\n"

        text += "\nتعداد مورد نظر را انتخاب کنید:\n\n"

        kb_rows = []
        for qty in range(1, min(bundle.max_quantity + 1, 6)):
            price = bundle.calculate_bulk_price(qty)
            kb_rows.append([
                InlineKeyboardButton(
                    text=f"{qty} عدد - {price:,} تومان",
                    callback_data=f"bundle:qty:{bundle_id}:{qty}",
                )
            ])

        kb_rows.append([
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="shop:bundles")
        ])

        await callback.message.edit_text(
            text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows)
        )
    else:
        # Direct purchase
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"💳 پرداخت آنلاین ({bundle.bundle_price:,} ت)",
                    callback_data=f"bundle:pay:zarinpal:{bundle_id}:1",
                )],
                [InlineKeyboardButton(
                    text=f"💰 پرداخت از کیف پول",
                    callback_data=f"bundle:pay:wallet:{bundle_id}:1",
                )],
                [InlineKeyboardButton(
                    text="🔙 بازگشت", callback_data="shop:bundles"
                )],
            ]
        )

        text = (
            f"{bundle.icon} <b>{bundle.name}</b>\n\n"
            f"شامل:\n"
        )
        for item in bundle.items:
            if item.plan:
                text += f"  • {item.plan.name} ({item.plan.display_data} / {item.plan.display_duration})\n"

        text += (
            f"\n💰 قیمت اصلی: <s>{bundle.original_price:,}</s> تومان\n"
            f"✅ قیمت باندل: <b>{bundle.bundle_price:,}</b> تومان\n"
            f"🏷️ صرفه‌جویی: {bundle.savings:,} تومان"
        )

        await callback.message.edit_text(text, reply_markup=kb)

    await callback.answer()


@router.callback_query(F.data.startswith("bundle:qty:"))
async def bundle_quantity_selected(callback: CallbackQuery, db_user: User):
    """Handle bundle quantity selection."""
    parts = callback.data.split(":")
    bundle_id = int(parts[2])
    quantity = int(parts[3])

    async with get_session() as session:
        bundle = await session.get(Bundle, bundle_id)

    if not bundle:
        await callback.answer("⚠️ خطا.", show_alert=True)
        return

    total_price = bundle.calculate_bulk_price(quantity)

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"💳 پرداخت آنلاین ({total_price:,} ت)",
                callback_data=f"bundle:pay:zarinpal:{bundle_id}:{quantity}",
            )],
            [InlineKeyboardButton(
                text=f"💰 پرداخت از کیف پول",
                callback_data=f"bundle:pay:wallet:{bundle_id}:{quantity}",
            )],
            [InlineKeyboardButton(
                text="🔙 بازگشت", callback_data=f"bundle:buy:{bundle_id}"
            )],
        ]
    )

    await callback.message.edit_text(
        f"🛒 <b>خلاصه سفارش</b>\n\n"
        f"📦 باندل: {bundle.name}\n"
        f"🔢 تعداد: {quantity}\n"
        f"💰 مبلغ کل: <b>{total_price:,}</b> تومان\n\n"
        f"روش پرداخت را انتخاب کنید:",
        reply_markup=kb,
    )
    await callback.answer()
