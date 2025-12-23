from sync_models import News, User, Users_statistics
from sync_models import Session
from sqlalchemy import delete, update, select, func

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from time import sleep


handler = RotatingFileHandler("db_updates.log", maxBytes=1_000_000, backupCount=6)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[handler],
)

logger = logging.getLogger(__name__)

def daily_db_update():
    with Session() as session:
        date_of_day = datetime.now().replace(microsecond=0)
        today_count_users = session.scalar(select(func.count(User.tg_id)))

        try:
            session.execute(delete(News).where(News.news_date > 2))
            logger.info("Старые строки в таблице удалены")
            session.execute(update(News).values(news_date=News.news_date - 1))
        except Exception as e:
            logger.error(f"Не удалось обновить значения News.news_date по причине: {e}")
            session.rollback()
            return
        session.commit()
        sleep(0.1)
        
        
        """Ежедневное добавление количества активных юзеров"""
        try:
            yesterday_date = date_of_day - timedelta(days=1)
            users_activity = session.scalar(
                select(func.count(User.tg_id)).where(
                    User.last_activity >= yesterday_date.replace(microsecond=0)
                )
            )
            session.add(
                Users_statistics(
                    day=date_of_day,
                    users_activity=users_activity,
                    all_users=today_count_users,
                )
            )
        except Exception as e:
            logger.error(
                f"Не удалось получить количество активных пользователей по причине: {e}"
            )
            session.rollback()
            return

        logger.info(
            "Данные в таблицах: news, number_of_users, number_of_users_activity обновленны успешно"
        )
        session.commit()

daily_db_update()