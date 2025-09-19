import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from aiogram import Router
from aiogram.types import Message
from parser_database import tg_parser_requests

import datetime


router = Router()

class TimeUtils:
    @staticmethod
    def format_time(input_time):
        '''Функция для очистки строки от не нужных символов'''
        #ftime = re.search(r'(\d{2}):(\d{2})', input_time)
        #return ftime.group(1)
        print(datetime.date.today())
        date, time = input_time.split()
        time = time[:-12]
        if date == str(datetime.date.today()):
            date = 0
        if time[0] == '0':
            time = time.replace('0', '')
        print(date, time)
        return [date, time]


class AiUtils:
    @staticmethod
    async def create_prompt(news_text, source_name, time):
        ai_model = 'gpt-5-nano'
        assistant_text = 'Тег текста выведи в самом начале и в формате ---"тег" '
        ai_system_text = 'Сожми текст, до 30-40 слов, на выходе должен быть красивый лаконочный текст. Если текст является рекламой, а не новостью, в ответ верни False вместо сжатого текста. Присвой тексту один из тегов Спортивные Политические Образование Научные Экономические Социальные Культурные. не используй вводных конструкций, просто выведи сжатый текст.'
        source_info = await tg_parser_requests.get_source_info(source_name)

        datetime_of_news = TimeUtils.format_time(time)
        data_for_ai_request = {
                'model': ai_model,
                'prompt': ai_system_text + assistant_text + news_text,
                'is_mass_media': source_info['mass_media'],
                'source_name': source_name,
                'time_interval': datetime_of_news[1],
                'date_interval': datetime_of_news[0]
            }
        return data_for_ai_request
    

class Handlers:
    @router.channel_post()
    async def parsing_chanels_posts(message: Message):
        print(f'Новое сообщение в канале {message.chat.title}, id: {message.chat.id}')
        print(f'message.text: {message.text} message.date: {message.date} message.new_chat_title: {message.new_chat_title}')
        #AiUtils.create_prompt(message.text, message.new_chat_title)
        
#TimeUtils.format_time('2025-09-18 09:30:55+00:00')