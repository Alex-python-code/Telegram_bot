from aiogram import BaseMiddleware
from aiogram.types import Message

from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import asyncio

from .middleware_rq import set_users_activity


logger = logging.getLogger(__name__)
handler = RotatingFileHandler("maiddleware.log", maxBytes=1_000_000, backupCount=6)
format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
handler.setFormatter(format)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


class MonitorUserActivity(BaseMiddleware):
    def __init__(self):
        self.last_users_activity = {}
        self.minutely_save_task = None

    async def __call__(self, handler, event: Message, data: dict):
        if not self.minutely_save_task:
            self.minutely_save_task = asyncio.create_task(self.minutely_save_data())

        if event.from_user:
            user_id = event.from_user.id
            self.last_users_activity[user_id] = datetime.today().replace(microsecond=0)

        return await handler(event, data)

    async def minutely_save_data(self):
        while True:
            await asyncio.sleep(60)
            if not self.last_users_activity:
                continue
            response = await set_users_activity(self.last_users_activity)
            if response:
                logger.error(
                    f"Ошибка при записи в бд активности пользователей: {response}"
                )
            self.last_users_activity = {}
