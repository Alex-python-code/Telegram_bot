from app.async_models import async_session
from app.async_models import User_preferences
from sqlalchemy import select
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


async def get_users_for_mailing(iter_number, limit) -> list:
    async with async_session() as session:
        now_hour = datetime.now().hour
        try:
            users = (await session.scalars(
                select(User_preferences.tg_id).where(User_preferences.mailing == now_hour).offset(iter_number * limit).limit(limit)
            )).all()
        except Exception as e:
            logger.warning(f"Не удалось выбрать пользователей для рассылки: {e}")
            return []

        return users
