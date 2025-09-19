import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from app.handlers import router
from config import TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher()


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    log_dir = "/home/alexlinux/Рабочий стол/Progra/Python/Telegram_bot/TG_parser"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "newsbot.log")

    # Формат логов
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Настройка root-логгера
    logging.basicConfig(level=logging.INFO, handlers=[])

    root_logger = logging.getLogger()

    # Хэндлер для файла (с ротацией)
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')