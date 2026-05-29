"""Admin server management handlers - complete rewrite."""

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

ADMIN_MENU_BUTTONS = [
    "📊 داشبورد", "👥 کاربران", "🖥️ سرورها", "📋 پلن‌ها",
    "💳 پرداخت‌ها", "🎁 تخفیف‌ها", "📢 ارسال پیام", "🎫 تیکت‌ها",
    "⚙️ تنظیمات", "🗄️ پشتیبان‌گیری", "🔙 منوی کاربری",
]


@router.message(F.text == "🖥️ سرورها")
async def servers_menu(message: Message, state: FSMContext):
    """Show servers list."""
    await state.clear()

    async with get_session() as session:
        stmt = select(Server).order_by(Server.id)
        result = await session.execute(stmt)
        servers = result.scalars().all()

    if not servers:
        from aiogram.types import InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text="➕ افزودن سرور", callback_data="admin:server:add"))

        await message.answer(
            "🖥️ <b>سرورها</b>\n\nهیچ سروری اضافه نشده.\nبرای شروع یک سرور اضافه کنید.",
            reply_markup=builder.as_markup(),
        )
        return

    await message.answer(
        "🖥️ <b>مدیریت سرورها</b>",
        reply_markup=AdminKeyboards.server_list(servers),
    )


@router.callback_query(F.data == "admin:server:add")
async def add_server_start(callback: CallbackQuery, state: FSMContext):
    """Start adding a new server."""
    await state.clear()
    await callback.message.edit_text(
        "🖥️ <b>افزودن سرور جدید</b>\n\n"
        "نام سرور را وارد کنید:\n"
        "(مثال: سرور آلمان 1)"
    )
    await state.set_state(AdminStates.server_name)
    await callback.answer()


@router.message(AdminStates.server_name)
async def server_name_input(message: Message, state: FSMContext):
    """Process server name."""
    if message.text and (message.text.startswith("/cancel") or message.text in ADMIN_MENU_BUTTONS):
        await state.clear()
        await message.answer("❌ عملیات لغو شد.")
        return
    await state.update_data(server_name=message.text.strip())

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="3x-ui (Sanaei)", callback_data="stype:xui"),
            ],
            [
                InlineKeyboardButton(text="Marzban", callback_data="stype:marzban"),
            ],
            [
                InlineKeyboardButton(text="Hiddify", callback_data="stype:hiddify"),
            ],
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
        "🌐 آدرس پنل را وارد کنید:\n"
        "(مثال: https://panel.example.com)\n\n"
        "⚠️ حتماً با https:// یا http:// شروع شود"
    )
    await state.set_state(AdminStates.server_host)
    await callback.answer()


@router.message(AdminStates.server_host)
async def server_host_input(message: Message, state: FSMContext):
    """Process server host."""
    if message.text and (message.text.startswith("/cancel") or message.text in ADMIN_MENU_BUTTONS):
        await state.clear()
        await message.answer("❌ عملیات لغو شد.")
        return
    host = message.text.strip().rstrip("/")
    if not host.startswith("http"):
        host = f"https://{host}"
    await state.update_data(server_host=host)
    await message.answer("🔌 پورت پنل را وارد کنید:\n(پیش‌فرض: 443، فقط عدد)")
    await state.set_state(AdminStates.server_port)


@router.message(AdminStates.server_port)
async def server_port_input(message: Message, state: FSMContext):
    """Process server port."""
    if message.text and (message.text.startswith("/cancel") or message.text in ADMIN_MENU_BUTTONS):
        await state.clear()
        await message.answer("❌ عملیات لغو شد.")
        return
    try:
        port = int(message.text.strip()) if message.text.strip() else 443
    except ValueError:
        port = 443
    await state.update_data(server_port=port)
    await message.answer("👤 یوزرنیم پنل:")
    await state.set_state(AdminStates.server_username)


@router.message(AdminStates.server_username)
async def server_username_input(message: Message, state: FSMContext):
    """Process server username."""
    if message.text and (message.text.startswith("/cancel") or message.text in ADMIN_MENU_BUTTONS):
        await state.clear()
        await message.answer("❌ عملیات لغو شد.")
        return
    await state.update_data(server_username=message.text.strip())
    await message.answer("🔑 پسورد پنل:")
    await state.set_state(AdminStates.server_password)


@router.message(AdminStates.server_password)
async def server_password_input(message: Message, state: FSMContext):
    """Process server password."""
    if message.text and (message.text.startswith("/cancel") or message.text in ADMIN_MENU_BUTTONS):
        await state.clear()
        await message.answer("❌ عملیات لغو شد.")
        return
    await state.update_data(server_password=message.text.strip())
    data = await state.get_data()

    if data.get("server_type") == "hiddify":
        await message.answer("🔑 API Key هیدیفای:")
        await state.set_state(AdminStates.server_api_key)
        return

    # Create server
    await _create_server(message, state, data)


@router.message(AdminStates.server_api_key)
async def server_api_key_input(message: Message, state: FSMContext):
    """Process Hiddify API key."""
    await state.update_data(server_api_key=message.text.strip())
    data = await state.get_data()
    await _create_server(message, state, data)


async def _create_server(message: Message, state: FSMContext, data: dict):
    """Create server in database and test connection."""
    from core.services.encryption import encryption

    type_map = {"xui": PanelType.XUI, "hiddify": PanelType.HIDDIFY, "marzban": PanelType.MARZBAN}
    panel_type = type_map.get(data["server_type"], PanelType.XUI)

    encrypted_password = encryption.encrypt(data["server_password"])

    async with get_session() as session:
        server = Server(
            name=data["server_name"],
            panel_type=panel_type,
            host=data["server_host"],
            port=data.get("server_port", 443),
            username=data["server_username"],
            password=encrypted_password,
            hiddify_api_key=data.get("server_api_key"),
            is_default=True,
        )
        session.add(server)
        await session.flush()
        server_id = server.id

    # Test connection
    await message.answer("🔄 در حال تست اتصال...")

    from core.services.panel.xui import XUIService
    from core.services.panel.hiddify import HiddifyService
    from core.services.panel.marzban import MarzbanService

    if panel_type == PanelType.XUI:
        panel = XUIService(host=data["server_host"], port=data.get("server_port", 443),
                          username=data["server_username"], password=data["server_password"])
    elif panel_type == PanelType.MARZBAN:
        panel = MarzbanService(host=data["server_host"], port=data.get("server_port", 443),
                              username=data["server_username"], password=data["server_password"])
    else:
        panel = HiddifyService(host=data["server_host"], port=data.get("server_port", 443),
                              username=data["server_username"], password=data["server_password"],
                              hiddify_api_key=data.get("server_api_key"))

    success = await panel.login()

    if success:
        await message.answer(
            f"✅ <b>سرور اضافه شد!</b>\n\n"
            f"🖥️ نام: {data['server_name']}\n"
            f"📋 نوع: {panel_type.value}\n"
            f"🌐 آدرس: {data['server_host']}:{data.get('server_port', 443)}\n"
            f"🟢 اتصال: موفق"
        )
    else:
        await message.answer(
            f"⚠️ <b>سرور اضافه شد ولی اتصال ناموفق بود!</b>\n\n"
            f"🖥️ نام: {data['server_name']}\n"
            f"🔴 اتصال: ناموفق\n\n"
            f"لطفاً آدرس، پورت و اطلاعات ورود را بررسی کنید."
        )

    await state.clear()


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

    await callback.message.edit_text(text, reply_markup=AdminKeyboards.server_detail(server_id))
    await callback.answer()


@router.callback_query(F.data.startswith("admin:server:edit:"))
async def edit_server(callback: CallbackQuery, state: FSMContext):
    """Start editing server."""
    server_id = int(callback.data.split(":")[3])
    await state.update_data(edit_server_id=server_id)

    from aiogram.types import InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    async with get_session() as session:
        server = await session.get(Server, server_id)

    if not server:
        await callback.answer("⚠️ سرور یافت نشد.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📍 تغییر لوکیشن", callback_data=f"admin:server:setloc:{server_id}"))
    builder.row(InlineKeyboardButton(text="🏳️ تغییر پرچم", callback_data=f"admin:server:setflag:{server_id}"))
    builder.row(InlineKeyboardButton(text="👥 حداکثر کاربر", callback_data=f"admin:server:setmax:{server_id}"))
    builder.row(InlineKeyboardButton(text="⭐ پیش‌فرض/غیرپیش‌فرض", callback_data=f"admin:server:toggledefault:{server_id}"))
    builder.row(InlineKeyboardButton(text="🔙 بازگشت", callback_data=f"admin:server:detail:{server_id}"))

    await callback.message.edit_text(
        f"✏️ <b>ویرایش سرور: {server.name}</b>",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:server:toggledefault:"))
async def toggle_default_server(callback: CallbackQuery):
    """Toggle server default status."""
    server_id = int(callback.data.split(":")[3])

    async with get_session() as session:
        server = await session.get(Server, server_id)
        if server:
            server.is_default = not server.is_default
            status = "پیش‌فرض ⭐" if server.is_default else "عادی"

    await callback.answer(f"سرور {status} شد", show_alert=True)


@router.callback_query(F.data.startswith("admin:server:setloc:"))
async def set_server_location(callback: CallbackQuery, state: FSMContext):
    """Set server location."""
    server_id = int(callback.data.split(":")[3])
    await state.update_data(edit_server_id=server_id, edit_field="location")
    await state.set_state(AdminStates.setting_value)
    await callback.message.edit_text("📍 لوکیشن جدید را وارد کنید:\n(مثال: آلمان، فرانکفورت)")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:server:setflag:"))
async def set_server_flag(callback: CallbackQuery, state: FSMContext):
    """Set server flag emoji."""
    server_id = int(callback.data.split(":")[3])
    await state.update_data(edit_server_id=server_id, edit_field="flag")
    await state.set_state(AdminStates.setting_value)
    await callback.message.edit_text("🏳️ ایموجی پرچم را ارسال کنید:\n(مثال: 🇩🇪)")
    await callback.answer()


@router.callback_query(F.data.startswith("admin:server:setmax:"))
async def set_server_max_users(callback: CallbackQuery, state: FSMContext):
    """Set server max users."""
    server_id = int(callback.data.split(":")[3])
    await state.update_data(edit_server_id=server_id, edit_field="max_users")
    await state.set_state(AdminStates.setting_value)
    await callback.message.edit_text("👥 حداکثر تعداد کاربر:\n(0 = نامحدود)")
    await callback.answer()


@router.message(AdminStates.setting_value)
async def process_setting_value(message: Message, state: FSMContext):
    """Process server edit value."""
    if message.text and (message.text.startswith("/cancel") or message.text in ADMIN_MENU_BUTTONS):
        await state.clear()
        await message.answer("❌ عملیات لغو شد.")
        return

    data = await state.get_data()
    server_id = data.get("edit_server_id")
    field = data.get("edit_field")
    value = message.text.strip()

    async with get_session() as session:
        server = await session.get(Server, server_id)
        if server:
            if field == "location":
                server.location = value
            elif field == "flag":
                server.flag = value
            elif field == "max_users":
                try:
                    server.max_users = int(value)
                except ValueError:
                    await message.answer("❌ عدد وارد کنید.")
                    return

    await message.answer(f"✅ {field} بروزرسانی شد.")
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

    await callback.answer("🔄 در حال تست...")

    from core.services.panel.xui import XUIService
    from core.services.panel.hiddify import HiddifyService
    from core.services.panel.marzban import MarzbanService

    if server.panel_type == PanelType.XUI:
        panel = XUIService(host=server.host, port=server.port,
                          username=server.username, password=server.password, api_path=server.api_path)
    elif server.panel_type == PanelType.MARZBAN:
        panel = MarzbanService(host=server.host, port=server.port,
                              username=server.username, password=server.password)
    else:
        panel = HiddifyService(host=server.host, port=server.port,
                              username=server.username, password=server.password,
                              hiddify_api_key=server.hiddify_api_key)

    success = await panel.login()

    if success:
        await callback.message.answer(f"🟢 اتصال به «{server.name}» موفق!")
    else:
        await callback.message.answer(f"🔴 اتصال به «{server.name}» ناموفق!")


@router.callback_query(F.data.startswith("admin:server:delete:"))
async def delete_server(callback: CallbackQuery):
    """Delete a server."""
    server_id = int(callback.data.split(":")[3])

    await callback.message.edit_text(
        "⚠️ آیا از حذف این سرور مطمئن هستید?",
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


@router.callback_query(F.data == "admin:servers:list")
async def servers_list_callback(callback: CallbackQuery):
    """Back to servers list."""
    async with get_session() as session:
        stmt = select(Server).order_by(Server.id)
        result = await session.execute(stmt)
        servers = result.scalars().all()

    await callback.message.edit_text(
        "🖥️ <b>مدیریت سرورها</b>",
        reply_markup=AdminKeyboards.server_list(servers),
    )
    await callback.answer()
