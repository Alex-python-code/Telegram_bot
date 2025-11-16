from app.async_models import async_session
from app.async_models import (
    User,
    User_preferences,
    News,
    News_region,
    News_source,
    News_theme,
)
from sqlalchemy import select, func

import logging


logger = logging.getLogger(__name__)


async def reg_user(tg_id, user_name, reg_date):
    async with async_session() as session:
        session.add(User(tg_id=tg_id, user_name=user_name, reg_date=reg_date))
        await session.commit()


async def set_users_preferences(tg_id, news_source, news_types, exclude_news_sources):
    async with async_session() as session:
        user = await session.scalar(
            select(User_preferences).where(User_preferences.tg_id == tg_id)
        )
        if not user:
            session.add(
                User_preferences(
                    tg_id=tg_id,
                    news_sources=news_source,
                    news_types=news_types,
                    exclude_news_sources=exclude_news_sources,
                )
            )
        # news_region = news_region))
        elif user:
            user.tg_id = tg_id
            user.news_sources = news_source
            user.news_types = news_types
            user.exclude_news_sources = exclude_news_sources
            # user.news_region = news_region
        await session.commit()


async def set_time_of_mailing(tg_id, time: int):
    async with async_session() as session:
        try:
            user = await session.scalar(
                select(User_preferences).where(User_preferences.tg_id == tg_id)
            )
            user.mailing = time
            await session.commit()
        except Exception as e:
            logger.warning(f"Не удалось записать время рассылки пользователя: {e}")
            return False
        return True


# get requests


async def does_user_have_preferences(tg_id: str):
    async with async_session() as session:
        user = await session.scalar(
            select(User_preferences).where(User_preferences.tg_id == tg_id)
        )
        if user:
            return True
        return False


async def get_source_info(source_id):
    """Принимает на вход id источника и возвращает информацию о нём"""
    async with async_session() as session:
        try:
            source = await session.scalar(
                select(News_source).where(News_source.source_id == source_id)
            )
        except Exception as e:
            logger.error(f"Error getting source info: {e}")
            return []
        return source


async def get_users_news_preferences(tg_id):
    async with async_session() as session:
        preferences = await session.scalar(
            select(User_preferences).where(User_preferences.tg_id == tg_id)
        )
        return preferences


async def get_news_for_user(
    mass_media, news_themes, exclude_sources, limit, page_number, day, time
):
    try:
        exclude_sources = list(map(int, exclude_sources))
        news_themes = list(map(int, news_themes))
        time = list(map(int, time))
    except Exception as e:
        logger.warning(f"Ошибка при изменении типа данных {e}")
        return
    if len(time) == 0:
        time = [i for i in range(25)]
    async with async_session() as session:
        if mass_media == 2:
            try:
                news = (
                    await session.scalars(
                        select(News)
                        .where(
                            News.news_date == day,
                            News.news_time.in_(time),
                            News.source_name.notin_(exclude_sources),
                            News.news_theme.in_(news_themes),
                        )
                        .order_by(News.id.desc())
                        .limit(limit)
                        .offset(page_number * limit)
                    )
                ).all()
            except Exception as e:
                logger.error(f"Ошибка в sql запросе новостей для пользователя: {e}")
                return False
        else:
            try:
                news = (
                    await session.scalars(
                        select(News)
                        .where(
                            News.news_date == day,
                            News.news_time.in_(time),
                            News.source_group == mass_media,
                            News.source_name.notin_(exclude_sources),
                            News.news_theme.in_(news_themes),
                        )
                        .order_by(News.id.desc())
                        .limit(limit)
                        .offset(page_number * limit)
                    )
                ).all()
            except Exception as e:
                logger.error(f"Ошибка в sql запросе новостей для пользователя: {e}")
                return False
        page_number += 1
        return [news, page_number]


async def is_user_first(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            return False
        return True


async def user_profile(tg_id: int):
    async with async_session() as session:
        user = (
            (await session.execute(select(User).where(User.tg_id == tg_id)))
            .scalars()
            .all()
        )
        preferences = (
            (
                await session.execute(
                    select(User_preferences).where(User_preferences.tg_id == tg_id)
                )
            )
            .scalars()
            .all()
        )
        # print(f'user {user}, {type(user)}')
        # print(f'preferences {preferences}, {type(preferences)}')
        data = user + preferences
        return data


async def get_all_regions():
    async with async_session() as session:
        return (await session.execute(select(News_region))).scalars().all()


async def get_all_news_themes():
    async with async_session() as session:
        return (await session.scalars(select(News_theme))).all()


async def get_all_news_sources(source_type):
    async with async_session() as session:
        if source_type == 2:
            return (await session.scalars(select(News_source))).all()
        return (
            await session.scalars(
                select(News_source).where(News_source.source_type == source_type)
            )
        ).all()


async def get_count_of_news_sources():
    async with async_session() as session:
        return await session.scalar(select(func.count(News_theme.id)))
