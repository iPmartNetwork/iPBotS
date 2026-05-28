"""Admin FSM states."""

from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    """Admin interaction states."""

    # Server management
    server_name = State()
    server_type = State()
    server_host = State()
    server_port = State()
    server_username = State()
    server_password = State()
    server_api_key = State()
    server_location = State()

    # Plan management
    plan_name = State()
    plan_category = State()
    plan_data = State()
    plan_duration = State()
    plan_price = State()
    plan_ip_limit = State()
    plan_server = State()
    plan_inbound = State()

    # User management
    user_search = State()
    user_credit_amount = State()
    user_ban_reason = State()
    user_message = State()

    # Broadcast
    broadcast_message = State()
    broadcast_confirm = State()

    # Discount
    discount_code = State()
    discount_type = State()
    discount_value = State()
    discount_max_uses = State()
    discount_expire = State()

    # Ticket reply
    ticket_reply = State()

    # Settings
    setting_value = State()
