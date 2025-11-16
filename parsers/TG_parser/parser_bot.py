import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from ai.async_ai_module import AsyncAi
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
import asyncio

from parser_rq.tg_parser_requests import get_source_info

load_dotenv()
PARSER_TOKEN = os.getenv("PARSER_TOKEN")

bot = Bot(token=PARSER_TOKEN)
dp = Dispatcher()

class AiUtils:
    @staticmethod
    async def create_prompt(news_text, source_name, time):
        ai_model = "gpt-5-nano"
        assistant_text = 'Тег текста выведи в самом начале и в формате ---"тег" '
        ai_system_text = "Сожми текст, до 30-50 слов, на выходе должен быть красивый лаконочный текст. Если текст является рекламой, а не новостью или просто не имеет смысла, в ответ верни False вместо сжатого текста. Присвой тексту один из тегов Спортивные Политические Образование Научные Экономические Социальные Культурные. не используй вводных конструкций, просто выведи сжатый текст."
        source_info = await get_source_info(source_name)
        if not source_info:
            return False
        data_for_ai_request = {
            "model": ai_model,
            "prompt": ai_system_text + assistant_text + news_text,
            "is_mass_media": source_info.mass_media,
            "source_name": source_info.source_id,
            "time_interval": time,
            "date_interval": 0,
        }
        return data_for_ai_request

ai_module = AsyncAi()


@dp.channel_post()
async def parsing_chanels_posts(message: Message):
    chat = message.chat
    text = message.caption or message.text
    logger.info(f"Новое сообщение в канале {chat.title}, id: {chat.id}")
    logger.info(f"message.text: {text} message.date: {message.date}")
    if not text:
        logger.info("В посте отсутствует текст, пропускаю")
        return
    prompt = await AiUtils.create_prompt(
        text, chat.title, str(message.date.strftime("%H"))
    )
    if not prompt:
        logger.error("Не удалось создать промт для ии")
        return
    logger.info("Отправка запроса в ИИ")
    await ai_module.main(prompt)

async def main():
    logger.info("Бот запущен и авторизован")
    await dp.start_polling(bot)

if __name__ == "__main__":
    handler = RotatingFileHandler("parser_bot.log", maxBytes=1_000_000, backupCount=6)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[handler],
    )
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.critical("Бот остановлен")