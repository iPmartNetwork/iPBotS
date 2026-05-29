"""User FSM states."""

from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """User interaction states."""

    # Wallet
    wallet_charge_amount = State()
    wallet_charge_method = State()
    wallet_withdraw_amount = State()

    # Card2Card
    card2card_receipt = State()

    # Discount code
    enter_discount_code = State()

    # Ticket
    ticket_subject = State()
    ticket_message = State()
    ticket_reply = State()

    # Profile
    enter_phone = State()

    # Transfer
    transfer_target = State()
