import logging
from openai import AsyncOpenAI

from .ai_database.ia_requests import send_compressed_text

from dotenv import load_dotenv
import os

logger = logging.getLogger(__name__)


load_dotenv()
AI = os.getenv("AI")


class AsyncAi:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=AI)
        self.news_storage = []

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

    async def main(self, task) -> bool:
        ai_response = {}
        try:
            ai_response = await self.make_ai_request(task)
        except Exception as e:
            logger.error(f"Ошибка при запросе в ИИ: {e}")
        if ai_response:
            logger.info(ai_response)
            result = self.find_tags(ai_response)
        else:
            logger.error("Нет ответов от ИИ")
            return False

        if not result:
            return False

        theme_tag_of_new, text_without_tags, is_mass_media = zip(result)

        configured_for_db = {
            "news_body": text_without_tags,
            "news_theme": theme_tag_of_new,
            "news_time": ai_response["time_interval"],
            "news_date": ai_response["date_interval"],
            "mass_media": is_mass_media,
            "source_name": ai_response["source_name"],
        }

        self.news_storage.append(configured_for_db)

        if len(self.news_storage) >= 10:
            logger.info("Запускаю запись в базу")
            if len(configured_for_db) == 0:
                logger.warning("Новости отсутствуют, записывать не чего")
                return False
            send_compressed_text(self.news_storage)
        return True

    def find_tags(self, text: dict) -> list[str] | None:
        if text["response"] == "SKIP":
            logger.info("ИИ вернул SKIP, пропускаю")
            return

        try:
            theme_tag_of_new = text["response"].split("\n")[0]
            text_without_tags = text["response"].split("\n")[1]
            is_mass_media = text["is_mass_media"]
        except Exception as e:
            logger.exception(f"Тег не найден, пропускаю новость. Ошибка: {e}")
            return

        return [theme_tag_of_new, text_without_tags, int(is_mass_media)]
