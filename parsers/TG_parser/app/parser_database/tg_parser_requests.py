import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from db_models.async_models import News_source
from db_models.async_models import async_session
from sqlalchemy import select

import logging

logger = logging.getLogger(__name__)
cash = {}


async def get_source_info(source_name):
    global cash
    if source_name in cash:
        return cash[source_name]

    if len(cash) >= 20:
        cash = {}

    async with async_session() as session:
        try:
            source = await session.scalar(
                select(News_source).where(News_source.notes == source_name)
            )
        except Exception as e:
            logger.error(f"Ошибка при запросе информации об источнике в бд: {e}")
            return

        cash[source_name] = source

        return source
