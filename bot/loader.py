"""Initialize bot, dispatcher, and core services."""

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.config import settings

# Redis
redis = Redis.from_url(settings.redis_url, decode_responses=True)

# Bot
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

# Storage for FSM
storage = RedisStorage(redis=redis)

# Dispatcher
dp = Dispatcher(storage=storage)
