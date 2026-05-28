"""Admin server management handlers."""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.filters.admin import AdminFilter
from bot.keyboards.admin_kb import AdminKeyboards
from bot.states import AdminStates
from core.database.engine import get_session
from core.database.models import Server
from core.database.models.server import PanelType

router = Router(name="admin_servers")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(F.text == "🖥️ سرورها")
async def servers_menu(message: Message):
    """Show servers list."""
    async with get_session() as session:
        stmt = select(Server).order_by(Server.id)
        result = await session.execute(stmt)
        servers = result.scalars().all()

    await message.answer(
        "🖥️ <b>مدیریت سرورها</b>",
        reply_markup=AdminKeyboards.server_list(servers),
    )


@router.callback_query(F.data == "admin:server:add")
async def add_server_start(callback: CallbackQuery, state: FSMContext):
    """Start adding a new server."""
    await callback.message.edit_text(
        "🖥️ <b>افزودن سرور جدید</b>\n\n"
        "نام سرور را وارد کنید:"
    )
    await state.set_state(AdminStates.server_name)
    await callback.answer()


@router.message(AdminStates.server_name)
async def server_name_input(message: Message, state: FSMContext):
    """Process server name."""
    await state.update_data(server_name=message.text.strip())

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="3x-ui (Sanaei)", callback_data="stype:xui"),
                InlineKeyboardButton(text="Hiddify", callback_data="stype:hiddify"),
            ]
        ]
    )
    await message.answer("نوع پنل را انتخاب کنید:", reply_markup=kb)
    await state.set_state(AdminStates.server_type)


@router.callback_query(AdminStates.server_type, F.data.startswith("stype:"))
async def server_type_input(callback: CallbackQuery, state: FSMContext):
    """Process server type."""
    panel_type = callback.data.split(":")[1]
    await state.update_data(server_type=panel_type)
    await callback.message.edit_text(
        "آدرس پنل را وارد کنید:\n"
        "(مثال: https://panel.example.com)"
    )
    await state.set_state(AdminStates.server_host)
    await callback.answer()


@router.message(AdminStates.server_host)
async def server_host_input(message: Message, state: FSMContext):
    """Process server host."""
    host = message.text.strip().rstrip("/")
    await state.update_data(server_host=host)
    await message.answer("پورت پنل را وارد کنید (پیش‌فرض: 443):")
    await state.set_state(AdminStates.server_port)


@router.message(AdminStates.server_port)
async def server_port_input(message: Message, state: FSMContext):
    """Process server port."""
    try:
        port = int(message.text.strip()) if message.text.strip() else 443
    except ValueError:
        port = 443
    await state.update_data(server_port=port)
    await message.answer("یوزرنیم پنل را وارد کنید:")
    await state.set_state(AdminStates.server_username)


@router.message(AdminStates.server_username)
async def server_username_input(message: Message, state: FSMContext):
    """Process server username."""
    await state.update_data(server_username=message.text.strip())
    await message.answer("پسورد پنل را وارد کنید:")
    await state.set_state(AdminStates.server_password)


@router.message(AdminStates.server_password)
async def server_password_input(message: Message, state: FSMContext):
    """Process server password and create server."""
    await state.update_data(server_password=message.text.strip())
    data = await state.get_data()

    # Check if Hiddify needs API key
    if data.get("server_type") == "hiddify":
        await message.answer("API Key هیدیفای را وارد کنید:")
        await state.set_state(AdminStates.server_api_key)
        return

    # Create server for 3x-ui
    await _create_server(message, state, data)


@router.message(AdminStates.server_api_key)
async def server_api_key_input(message: Message, state: FSMContext):
    """Process Hiddify API key."""
    await state.update_data(server_api_key=message.text.strip())
    data = await state.get_data()
    await _create_server(message, state, data)


async def _create_server(message: Message, state: FSMContext, data: dict):
    """Create server in database."""
    panel_type = PanelType.XUI if data["server_type"] == "xui" else PanelType.HIDDIFY

    async with get_session() as session:
        server = Server(
            name=data["server_name"],
            panel_type=panel_type,
            host=data["server_host"],
            port=data.get("server_port", 443),
            username=data["server_username"],
            password=data["server_password"],
            hiddify_api_key=data.get("server_api_key"),
        )
        session.add(server)

    await message.answer(
        f"✅ سرور «{data['server_name']}» با موفقیت اضافه شد.\n\n"
        f"🔄 برای تست اتصال از منوی سرورها اقدام کنید."
    )
    await state.clear()


@router.callback_query(F.data.startswith("admin:server:test:"))
async def test_server(callback: CallbackQuery):
    """Test server connection."""
    server_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        server = await session.get(Server, server_id)

    if not server:
        await callback.answer("⚠️ سرور یافت نشد.", show_alert=True)
        return

    await callback.answer("🔄 در حال تست اتصال...")

    # Test connection
    from core.services.panel.xui import XUIService
    from core.services.panel.hiddify import HiddifyService

    if server.panel_type == PanelType.XUI:
        panel = XUIService(
            host=server.host,
            port=server.port,
            username=server.username,
            password=server.password,
            api_path=server.api_path,
        )
    else:
        panel = HiddifyService(
            host=server.host,
            port=server.port,
            username=server.username,
            password=server.password,
            hiddify_api_key=server.hiddify_api_key,
        )

    success = await panel.login()

    if success:
        await callback.message.answer(f"✅ اتصال به سرور «{server.name}» موفق بود!")
    else:
        await callback.message.answer(f"❌ اتصال به سرور «{server.name}» ناموفق بود.")


@router.callback_query(F.data.startswith("admin:server:detail:"))
async def server_detail(callback: CallbackQuery):
    """Show server details."""
    server_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        server = await session.get(Server, server_id)

    if not server:
        await callback.answer("⚠️ سرور یافت نشد.", show_alert=True)
        return

    text = (
        f"🖥️ <b>{server.name}</b>\n\n"
        f"📋 نوع: {server.panel_type.value}\n"
        f"🌐 آدرس: {server.host}:{server.port}\n"
        f"📍 لوکیشن: {server.flag} {server.location}\n"
        f"👥 کاربران: {server.current_users}/{server.max_users or '♾️'}\n"
        f"✅ وضعیت: {'فعال' if server.is_active else 'غیرفعال'}\n"
        f"⭐ پیش‌فرض: {'بله' if server.is_default else 'خیر'}"
    )

    await callback.message.edit_text(
        text, reply_markup=AdminKeyboards.server_detail(server_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:server:delete:"))
async def delete_server(callback: CallbackQuery):
    """Delete a server."""
    server_id = int(callback.data.split(":")[3])

    await callback.message.edit_text(
        "⚠️ آیا از حذف این سرور مطمئن هستید؟",
        reply_markup=AdminKeyboards.confirm_action("server_delete", server_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:confirm:server_delete:"))
async def confirm_delete_server(callback: CallbackQuery):
    """Confirm server deletion."""
    server_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        server = await session.get(Server, server_id)
        if server:
            await session.delete(server)

    await callback.message.edit_text("✅ سرور حذف شد.")
    await callback.answer()
