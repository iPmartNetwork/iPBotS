"""Bot configuration loaded from environment variables."""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App
    APP_ENV: str = "production"
    APP_DEBUG: bool = False
    APP_SECRET_KEY: str = "change-me"

    # Telegram
    BOT_TOKEN: str
    ADMIN_IDS: str = ""
    BOT_USERNAME: str = ""
    SUPPORT_CHAT_ID: int = 0

    @property
    def admin_ids_list(self) -> list:
        """Parse ADMIN_IDS string to list of ints."""
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip()]

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "v2ray_shop"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # Webhook
    WEBHOOK_ENABLED: bool = False
    WEBHOOK_HOST: str = ""
    WEBHOOK_PATH: str = "/api/telegram/webhook"
    WEBHOOK_PORT: int = 8443

    # ZarinPal
    ZARINPAL_MERCHANT_ID: str = ""
    ZARINPAL_SANDBOX: bool = False
    ZARINPAL_CALLBACK_URL: str = ""

    # NowPayments
    NOWPAYMENTS_API_KEY: str = ""
    NOWPAYMENTS_IPN_SECRET: str = ""
    NOWPAYMENTS_CALLBACK_URL: str = ""

    # Cryptomus
    CRYPTOMUS_MERCHANT_ID: str = ""
    CRYPTOMUS_API_KEY: str = ""
    CRYPTOMUS_CALLBACK_URL: str = ""

    # IDPay
    IDPAY_API_KEY: str = ""
    IDPAY_SANDBOX: bool = False
    IDPAY_CALLBACK_URL: str = ""

    # Card to Card
    CARD2CARD_ENABLED: bool = False
    CARD2CARD_NUMBER: str = ""
    CARD2CARD_HOLDER: str = ""

    # Referral
    REFERRAL_ENABLED: bool = True
    REFERRAL_BONUS_PERCENT: int = 10
    REFERRAL_MIN_WITHDRAW: int = 50000

    # Backup
    BACKUP_ENABLED: bool = True
    BACKUP_INTERVAL_HOURS: int = 24
    BACKUP_CHAT_ID: int = 0

    # Locale
    DEFAULT_LANGUAGE: str = "fa"

    # Payment Notification Group
    PAYMENT_GROUP_ID: int = 0  # Group/channel ID for payment notifications
    PAYMENT_TOPIC_CARD2CARD_WALLET: int = 0  # Topic ID for wallet card2card
    PAYMENT_TOPIC_CARD2CARD_PURCHASE: int = 0  # Topic ID for direct purchase card2card
    PAYMENT_TOPIC_ONLINE: int = 0  # Topic ID for online payment results

    # OpenAI (for AI support chatbot)
    OPENAI_API_KEY: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
