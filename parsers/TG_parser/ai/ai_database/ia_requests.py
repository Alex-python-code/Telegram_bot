from db_models.sync_models import Session
from db_models.sync_models import News

import logging


logger = logging.getLogger(__name__)


def send_compressed_text(list_of_texts):
    with Session() as session:
        ready_to_send = []
        ready_to_send.append(
            News(
                news_body=list_of_texts["news_body"],
                news_theme=list_of_texts["news_theme"],
                news_time=list_of_texts["news_time"],
                news_date=list_of_texts["news_date"],
                source_group=list_of_texts["mass_media"],
                source_name=int(list_of_texts["source_name"]),
            )
        )
        try:
            session.add_all(ready_to_send)
            session.commit()
        except Exception as e:
            logger.error(f"Ошибка записи новости в бд: {e}")
            return
        logger.info("Данные записаны в базу успешно")
