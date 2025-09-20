import asyncio
import logging

from aiogram import Bot, Dispatcher
from app.handlers import router
from config import PARSER_TOKEN

bot = Bot(token=PARSER_TOKEN)
dp = Dispatcher()


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.critical("Парсер не смог стартовать")
