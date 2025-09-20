import logging
from openai import AsyncOpenAI
import re

import ai.ai_database.ia_requests as ia_rq

from config import AI

logger = logging.getLogger(__name__)


class AsyncAi:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=AI)

    async def make_ai_request(self, input_data):
        response = await self.client.chat.completions.create(
            model=input_data["model"],
            messages=[{"role": "user", "content": input_data["prompt"]}],
        )
        return {
            "response": response.choices[0].message.content,
            "is_mass_media": input_data["is_mass_media"],
            "source_name": input_data["source_name"],
            "time_interval": input_data["time_interval"],
            "date_interval": input_data["date_interval"],
        }

    async def main(self, task):
        try:
            ai_response = await self.make_ai_request(task)
        except Exception as e:
            logger.error(f"Ошибка при запросе в ИИ: {e}")
        # try:
        # ai_responses = await asyncio.gather(*tasks)
        # except Exception as e:
        #    print(f"Ошибка при запускке задач: {e}")
        #    return False
        if ai_response:
            self.find_tags(ai_response)
        else:
            logger.error("Нет ответов от ИИ")
            # print(ai_response)
            return False
        return ai_response

    def find_tags(self, text):
        # for text in list_of_texst:
        if text["response"] == "False":
            logger.info("ИИ вернул False, пропускаю")
            return
        tag_pattern = r'---\s*"([^"]+)"'
        encode_theme_tags = {
            "Спортивные": 1,
            "Политические": 2,
            "Образование": 3,
            "Научные": 4,
            "Экономические": 5,
            "Социальные": 6,
            "Культурные": 7,
            "Программирование": 8,
        }
        try:
            theme_tag_of_new_raw = re.search(tag_pattern, text["response"])
            theme_tag_of_new = theme_tag_of_new_raw.group(1)
            is_mass_media = text["is_mass_media"]
        except Exception as e:
            logger.exception(f"Тег не найден, пропускаю новость. Ошибка: {e}")
            return
        # print(f'Тип файла text{type(text)}')
        try:
            text_without_tags = text["response"].replace(
                theme_tag_of_new_raw.group(0), ""
            )
        except Exception as e:
            # print(f"{theme_tag_of_new_raw.group(0)} удалён из текста")
            logger.warning(f"Ошибка при удалении тега из текста: {e}")
            # print(f"Исходный текст: {text['response']}")
            return
        # print(f"Текст успешно очищен от тегов")
        configured_for_db = {
            "news_body": text_without_tags,
            "news_theme": encode_theme_tags[theme_tag_of_new],
            "news_time": text["time_interval"],
            "news_date": text["date_interval"],
            "mass_media": is_mass_media,
            "source_name": text["source_name"],
        }
        # print(f"Сформирован список для записи в базу")
        logger.info("Запускаю запись в базу")
        if len(configured_for_db) == 0:
            logger.warning("Новости отсутствуют, записывать не чего")
            return
        ia_rq.send_compressed_text(configured_for_db)
