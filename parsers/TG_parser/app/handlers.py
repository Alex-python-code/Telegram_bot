import sys

sys.path.append("/home/alexlinux/Рабочий стол/Progra/Python/Telegram_bot")

from ai.async_ai_module import AsyncAi

import logging

from aiogram import Router
from aiogram.types import Message
from .parser_database.tg_parser_requests import get_source_info

import datetime


router = Router()
logger = logging.getLogger(__name__)


class TimeUtils:
    @staticmethod
    async def format_time(input_time):
        """Функция для очистки строки от не нужных символов"""
        date, time = input_time.split()
        time = time[:-12]
        if date == str(datetime.date.today()):
            date = 0
        if time[0] == "0":
            time = time.replace("0", "")
        return [date, int(time) + 3]


class AiUtils:
    @staticmethod
    async def create_prompt(news_text, source_name, time):
        ai_model = "gpt-5-nano"
        assistant_text = 'Тег текста выведи в самом начале и в формате ---"тег" '
        ai_system_text = "Сожми текст, до 30-50 слов, на выходе должен быть красивый лаконочный текст. Если текст является рекламой, а не новостью или просто не имеет смысла, в ответ верни False вместо сжатого текста. Присвой тексту один из тегов Спортивные Политические Образование Научные Экономические Социальные Культурные. не используй вводных конструкций, просто выведи сжатый текст."
        source_info = await get_source_info(source_name)

        datetime_of_news = await TimeUtils.format_time(time)
        data_for_ai_request = {
            "model": ai_model,
            "prompt": ai_system_text + assistant_text + news_text,
            "is_mass_media": source_info.mass_media,
            "source_name": source_info.source_id,
            "time_interval": datetime_of_news[1],
            "date_interval": datetime_of_news[0],
        }
        return data_for_ai_request


ai_module = AsyncAi()
# json_array = []


class Handlers:
    @router.channel_post()
    async def parsing_chanels_posts(message: Message):
        logger.info(
            f"Новое сообщение в канале {message.chat.title}, id: {message.chat.id}"
        )
        logger.info(f"message.text: {message.caption} message.date: {message.date}")
        chanel_post = message.caption
        if not chanel_post:
            chanel_post = message.text
            if not chanel_post:
                logger.info("В посте отсутствует текст, пропускаю")
                return
        prompt = await AiUtils.create_prompt(
            chanel_post, message.chat.title, str(message.date)
        )
        # print('Отправка новости в ИИ')
        await ai_module.main(prompt)


# TimeUtils.format_time('2025-09-18 09:30:55+00:00')
