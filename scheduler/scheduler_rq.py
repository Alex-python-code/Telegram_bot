from app.async_models import async_session
from app.async_models import User_preferences
from sqlalchemy import select
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


async def get_users_for_mailing():
    async with async_session() as session:
        now_hour = datetime.now().hour
        try:
            users = await session.scalars(
                select(User_preferences).where(User_preferences.mailing == now_hour)
            )
        except Exception as e:
            logger.warning(f"Не удалось выбрать пользователей для рассылки: {e}")
            return []

        return users.all()
