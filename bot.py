import asyncio
import logging
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from app.handlers import router
from app.bot_database.async_models import async_main
from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def main():
    await async_main()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    handler = RotatingFileHandler("app.log", maxBytes=1_000_000, backupCount=6)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            handler,
            logging.FileHandler("app.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(__name__)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.critical("Бот не смог стартовать")
