import asyncio
import logging
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from app.handlers import router
from app.async_models import async_main

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scheduler.hourly_news_sender import hourly_news_mailing

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TEST_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()


async def main():
    scheduler.add_job(hourly_news_mailing, "cron", minute=0, jitter=20)
    scheduler.start()

    await async_main()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    handler = RotatingFileHandler("app.log", maxBytes=1_000_000, backupCount=6)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[handler],
    )
    logger = logging.getLogger(__name__)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.critical("Бот не смог стартовать")
