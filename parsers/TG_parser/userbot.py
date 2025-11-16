import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from ai.async_ai_module import AsyncAi

import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import asyncio

from pyrogram import filters
from pyrogram.types import Message
from pyrogram.client import Client
from parser_rq.tg_parser_requests import get_source_info


load_dotenv()
PARSER_ID = os.getenv("PARSER_ID")
PARSER_HASH = os.getenv("PARSER_HASH")
PHONE_NUM = os.getenv("PHONE_NUM")


app = Client("parser", api_id=PARSER_ID, api_hash=PARSER_HASH, phone_number=PHONE_NUM)


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


@app.on_message(filters=filters.private)
async def private_answer(client: Client, message: Message):
    logger.info("Сообщение в лс")
    await message.reply("Бот запущен и успешно работает")


@app.on_message(filters=filters.channel)
async def parsing_chanels_posts(client: Client, message: Message):
    chat = message.chat
    text = message.caption or message.text

    logger.info(f"Новое сообщение в канале {chat.title}, id: {chat.id}")
    logger.info(f"message.text: {message.caption} message.date: {message.date}")
    if not text:
        logger.info("В посте отсутствует текст, пропускаю")
        return
    prompt = await AiUtils.create_prompt(
        text, chat.title, str(message.date.strftime("%H"))
    )
    if not prompt:
        logger.error("Не удалось создать промт для ии")
        return
    # print('Отправка новости в ИИ')
    logger.info("Отправка запроса в ИИ")
    await ai_module.main(prompt)


async def main():
    async with app:
        await asyncio.Future()
        logger.info("Юзер бот запущен и авторизован")


if __name__ == "__main__":
    handler = RotatingFileHandler("userbot.log", maxBytes=1_000_000, backupCount=6)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[handler],
    )
    logger = logging.getLogger(__name__)
    try:
        app.run()
        logger.info("Юзер бот запущен и авторизован")
    except KeyboardInterrupt:
        logger.critical("Парсер не смог стартовать")
