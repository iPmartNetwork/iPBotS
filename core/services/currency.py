"""Multi-currency support service."""
from typing import Dict
import aiohttp
from loguru import logger


# Static fallback rates (Toman per unit)
FALLBACK_RATES: Dict[str, int] = {
    "IRR": 1,       # Rial (base)
    "IRT": 10,      # Toman = 10 Rial
    "USD": 620000,  # ~62,000 Toman
    "EUR": 680000,  # ~68,000 Toman
    "TRY": 18000,   # ~1,800 Toman
    "RUB": 6500,    # ~650 Toman
    "AED": 170000,  # ~17,000 Toman
}

CURRENCY_SYMBOLS = {
    "IRT": "تومان",
    "USD": "$",
    "EUR": "€",
    "TRY": "₺",
    "RUB": "₽",
    "AED": "د.إ",
}


class CurrencyService:
    """Convert between currencies."""

    def __init__(self):
        self._rates = FALLBACK_RATES.copy()

    def convert(self, amount: int, from_currency: str, to_currency: str) -> int:
        """Convert amount between currencies.
        
        Args:
            amount: Amount in source currency (smallest unit)
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Amount in target currency
        """
        if from_currency == to_currency:
            return amount

        # Convert to Toman first
        from_rate = self._rates.get(from_currency, 1)
        toman_amount = amount * from_rate // 10  # to Toman

        # Convert from Toman to target
        to_rate = self._rates.get(to_currency, 1)
        if to_rate == 0:
            return 0

        return toman_amount * 10 // to_rate

    def format_price(self, amount: int, currency: str = "IRT") -> str:
        """Format price with currency symbol."""
        symbol = CURRENCY_SYMBOLS.get(currency, currency)
        if currency == "IRT":
            return f"{amount:,} {symbol}"
        elif currency in ("USD", "EUR"):
            return f"{symbol}{amount:,.2f}"
        else:
            return f"{amount:,} {symbol}"

    def get_price_in_currency(self, toman_price: int, currency: str) -> float:
        """Get price in target currency from Toman."""
        rate = self._rates.get(currency, 620000)
        if currency == "IRT":
            return toman_price
        return round(toman_price / (rate / 10), 2)

    async def update_rates(self):
        """Update exchange rates from API (optional)."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.exchangerate-api.com/v4/latest/USD",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        rates = data.get("rates", {})
                        if "TRY" in rates:
                            self._rates["TRY"] = int(self._rates["USD"] / rates["TRY"])
                        if "RUB" in rates:
                            self._rates["RUB"] = int(self._rates["USD"] / rates["RUB"])
                        if "EUR" in rates:
                            self._rates["EUR"] = int(self._rates["USD"] / rates["EUR"])
                        logger.info("Exchange rates updated")
        except Exception as e:
            logger.warning(f"Rate update failed, using fallback: {e}")


currency_service = CurrencyService()
