import asyncio
from openai import AsyncOpenAI
import re

import ai_database.ia_requests as ia_rq

from config import AI_TOKEN

class AsyncAi:
        
    def __init__(self, now_time_interval):
        self.client = AsyncOpenAI(api_key = AI_TOKEN)
        self.now_time_interval = now_time_interval

    async def make_ai_request(self, input_data):
        response = await self.client.chat.completions.create(
            model = input_data['model'],
            messages = [{"role": "user", "content": input_data['prompt']}]
        )
        return response.choices[0].message.content
    
    async def main(self, list_of_tasks):
        tasks = [asyncio.create_task(self.make_ai_request(task)) for task in list_of_tasks]
        try:
            ia_responses = await asyncio.gather(*tasks)
        except Exception as e:
            print(f'Ошибка при запускке задач: {e}')
        #if not ia_responses:
            #print('Нет ответов от ИИ')
            #return False
        self.find_tags(ia_responses)
        return ia_responses

    def find_tags(self, list_of_texst):
        list_configured_for_db = []
        for text in list_of_texst:
            tag_pattern = r'---\s*"([^"]+)"'
            try:
                theme_tag_of_new_raw = re.search(tag_pattern, text)
                theme_tag_of_new = theme_tag_of_new_raw.group(1)
            except:
                print('Тег не найден, присваиваю "Без темы"')
                theme_tag_of_new = 'Без темы'
                #continue
            #print(f'Тип файла text{type(text)}')
            try:
                text_without_tag = text.replace(theme_tag_of_new_raw.group(0), '')
            except:
                print(f'{theme_tag_of_new_raw.group(0)} удалён из текста')
                print('Ошибка при удалении тега из текста')
                print(f'Исходный текст: {text}')
                return
            print(f'Текст успешно очищен от тегов')
            list_configured_for_db.append({'news_body': text_without_tag, 'news_theme': theme_tag_of_new, 'news_datetime': self.now_time_interval})
            print(f'Сформирован список для записи в базу')
        print('Запускаю запись в базу')
        ia_rq.send_compressed_text(list_configured_for_db)