from .scheduler_rq import get_users_for_mailing
from app.bot_database.bot_requests import get_news_for_user, get_users_news_preferences
from datetime import datetime

import logging


logger = logging.getLogger(__name__)


async def get_news(mass_media, news_themes, exclude_sources, time):
    try:
        news = await get_news_for_user(
            mass_media=mass_media,
            news_themes=news_themes,
            exclude_sources=exclude_sources,
            limit=1,
            page_number=0,
            day=0,
            time=time,
        )
    except Exception as e:
        logger.warning(f"Не удалось получить новости для рассылки: {e}")
        return ""
    return news[0]


async def hourly_news_mailing():
    from bot import bot

    users = await get_users_for_mailing()
    if not users:
        return

    now_time = datetime.now().hour
    time = [now_time, now_time - 1]

    for user in users:
        try:
            news = ""
            preferences = await get_users_news_preferences(user.tg_id)

            news = await get_news(
                preferences.news_sources,
                preferences.news_types.split(),
                preferences.exclude_news_sources.split(),
                time,
            )
        except Exception as e:
            logger.warning(
                f"Не удалось запросить данные о пользователе или новости для рассылки: {e}"
            )
            continue
        if not news:
            await bot.send_message(
                user.tg_id, "Я не смог найти подходящие для Вас новости, простите :("
            )
            return
        await bot.get
        await bot.send_message(user.tg_id, news[0].news_body)
