import asyncio
from openai import AsyncOpenAI
import re

import ai_database.ia_requests as ia_rq

from config import AI_TOKEN

class AsyncAi:
        
    def __init__(self):
        self.client = AsyncOpenAI(api_key = AI_TOKEN)

    async def make_ai_request(self, input_data):
        response = await self.client.chat.completions.create(
            model = input_data['model'],
            messages = [{"role": "user", "content": input_data['prompt']}]
        )
        return {'response': response.choices[0].message.content,
                'is_mass_media': input_data['is_mass_media'],
                'source_name': input_data['source_name'],
                'time_interval': input_data['time_interval']
                }
    
    async def main(self, list_of_tasks):
        tasks = [asyncio.create_task(self.make_ai_request(task)) for task in list_of_tasks]
        ai_responses = []
        try:
            ai_responses = await asyncio.gather(*tasks)
        except Exception as e:
            print(f'Ошибка при запускке задач: {e}')
            return False
        if ai_responses:
            self.find_tags(ai_responses)
        else:
            print('Нет ответов от ИИ')
            print(ai_responses)
            return False
        return ai_responses

    def find_tags(self, list_of_texst):
        list_configured_for_db = []
        for text in list_of_texst:
            tag_pattern = r'---\s*"([^"]+)"'
            encode_theme_tags = {
                'Спортивные': 1,
                'Политические': 2,
                'Военные': 3,
                'Научные': 4,
                'Экономические': 5,
                'Социальные': 6,
                'Культурные': 7,
            }
            try:
                theme_tag_of_new_raw = re.search(tag_pattern, text['response'])
                theme_tag_of_new = theme_tag_of_new_raw.group(1)
                is_mass_media = text['is_mass_media']
            except Exception as e:
                print(f'Тег не найден, пропускаю новость. Ошибка: {e}')
                continue
            #print(f'Тип файла text{type(text)}')
            try:
                text_without_tags = text['response'].replace(theme_tag_of_new_raw.group(0), '')
            except:
                print(f'{theme_tag_of_new_raw.group(0)} удалён из текста')
                print('Ошибка при удалении тега из текста')
                print(f'Исходный текст: {text['response']}')
                continue
            print(f'Текст успешно очищен от тегов')
            list_configured_for_db.append({'news_body': text_without_tags,
                                           'news_theme': encode_theme_tags[theme_tag_of_new],
                                           'news_time': text['time_interval'],
                                           'news_date': text['date_interval'],
                                           'mass_media': is_mass_media,
                                           'source_name': text['source_name']
                                           })
            print(f'Сформирован список для записи в базу')
        print('Запускаю запись в базу')
        ia_rq.send_compressed_text(list_configured_for_db)