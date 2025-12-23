import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from db_models.sync_models import Session
from db_models.sync_models import News

import logging


logger = logging.getLogger(__name__)


def send_compressed_text(list_of_texts: list):
    with Session() as session:
        ready_to_send = []
        for item in list_of_texts:
            ready_to_send.append(
                News(
                    news_body=item["news_body"],
                    news_theme=item["news_theme"],
                    news_time=item["news_time"],
                    news_date=item["news_date"],
                    source_group=item["mass_media"],
                    source_name=int(item["source_name"]),
                )
            )
        try:
            session.add_all(ready_to_send)
            session.commit()
        except Exception as e:
            logger.error(f"Ошибка записи новости в бд: {e}")
            session.rollback()
            return
        logger.info("Данные записаны в базу успешно")
