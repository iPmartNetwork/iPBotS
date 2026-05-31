"""Localization package."""

from locales.fa import MESSAGES as FA_MESSAGES
from locales.en import MESSAGES as EN_MESSAGES
from locales.ar import MESSAGES as AR_MESSAGES
from locales.tr import MESSAGES as TR_MESSAGES
from locales.ru import MESSAGES as RU_MESSAGES

_LOCALES = {
    "fa": FA_MESSAGES,
    "en": EN_MESSAGES,
    "ar": AR_MESSAGES,
    "tr": TR_MESSAGES,
    "ru": RU_MESSAGES,
}


def get_text(key: str, locale: str = "fa", **kwargs) -> str:
    """Get localized text by key.

    Args:
        key: Message key.
        locale: Language code (fa, en, ar, tr, ru).
        **kwargs: Format arguments.

    Returns:
        Formatted localized string.
    """
    messages = _LOCALES.get(locale, FA_MESSAGES)
    text = messages.get(key, FA_MESSAGES.get(key, key))

    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text

    return text
