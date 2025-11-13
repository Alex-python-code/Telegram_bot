from db_models.sync_models import News
from db_models.sync_models import Session
from sqlalchemy import delete, update

import logging
from logging.handlers import RotatingFileHandler


handler = RotatingFileHandler("db_updates.log", maxBytes=1_000_000, backupCount=6)

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s",
    handlers=[handler, logging.FileHandler("db_updates.log", encoding = 'utf-8')],
)

logger = logging.getLogger(__name__)

with Session() as session:
    try:
        session.execute(delete(News).where(News.news_date >= 3))
        logger.info("Старые строки в таблице удалены")
        session.execute(update(News).values(news_date = News.news_date + 1))
        logger.info("Данные в колонке news_date данные обновлены")
        session.commit()
    except Exception as e:
        logger.error(f'Не удалось обновить значения News.news_date по причине: {e}')