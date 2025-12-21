from app.async_models import async_session
from app.async_models import (
    User,
    User_preferences,
    News,
    News_region,
    News_source,
    News_theme,
    Users_statistics,
)
from sqlalchemy import select, func

import logging
from datetime import date, timedelta


logger = logging.getLogger(__name__)


async def reg_user(tg_id, user_name, reg_date):
    """Регистрация пользователя"""
    async with async_session() as session:
        session.add(User(tg_id=tg_id, user_name=user_name, reg_date=reg_date))
        await session.commit()


async def set_users_preferences(tg_id, news_source, news_themes, exclude_news_sources):
    """Установить предпочтения пользователя"""
    async with async_session() as session:
        user = await session.scalar(
            select(User_preferences).where(User_preferences.tg_id == tg_id)
        )
        if not user:
            session.add(
                User_preferences(
                    tg_id=tg_id,
                    news_sources=news_source,
                    news_themes=news_themes,
                    exclude_news_sources=exclude_news_sources,
                )
            )
        elif user:
            user.tg_id = tg_id
            user.news_sources = news_source
            user.news_themes = news_themes
            user.exclude_news_sources = exclude_news_sources
        await session.commit()


async def set_time_of_mailing(tg_id, time):
    """Установить время рассылки новостей"""
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


async def does_user_have_preferences(tg_id: str) -> bool:
    """Настроены ли у пользователя предпочтения"""
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
    """По id пользователя выдаёт его предпочтения"""
    async with async_session() as session:
        preferences = await session.scalar(
            select(User_preferences).where(User_preferences.tg_id == tg_id)
        )
        return preferences


async def get_news_for_user(
    mass_media, news_themes, exclude_sources, limit, page_number, day, time
):
    """Выбрать 5 последних новостей для пользователя"""
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
                        .order_by(News.news_time.desc())
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
                        .order_by(News.news_time.desc(), News.id.desc())
                        .limit(limit)
                        .offset(page_number * limit)
                    )
                ).all()
            except Exception as e:
                logger.error(f"Ошибка в sql запросе новостей для пользователя: {e}")
                return False
        page_number += 1
        return [news, page_number]


async def is_user_first(tg_id) -> bool:
    """Проверка на то, что пользователь пишет впервые"""
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            return False
        return True


async def user_profile(tg_id: int) -> list:
    """Получение профиля пользователя"""
    async with async_session() as session:
        user = (await session.scalars(select(User).where(User.tg_id == tg_id))).all()
        preferences = (
            await session.scalars(
                select(User_preferences).where(User_preferences.tg_id == tg_id)
            )
        ).all()
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
    """Получить количество новостных источников"""
    async with async_session() as session:
        return await session.scalar(select(func.count(News_theme.id)))


async def get_number_of_users():
    """Получить количество всех пользователей"""
    async with async_session() as session:
        return await session.scalar(select(func.count(User.tg_id)))


async def get_users_activity() -> list | int:
    """Получить количество активных пользователей"""
    async with async_session() as session:
        week_ago = date.today() - timedelta(days=7)
        today = await session.scalar(
            select(func.count()).where(User.last_activity == date.today())
        )
        last_week = await session.scalar(
            select(func.count()).where(User.last_activity >= week_ago)
        )

        return [today, last_week]


async def convert_username_to_tg_id(username) -> int:
    """Конвертирует имя пользователя в tg id"""
    async with async_session() as session:
        return await session.scalar(
            select(User.tg_id).where(User.user_name == username)
        )


async def count_users_in_period(first_day: date) -> dict[str, tuple]:
    """Запрос количества пользователей за каждый день периода.
    Args:
        first_day: - Первый день периода для выборки данных.

    Returns:
        dict: - Словарь имеет аргументы 'days', 'users'
    """
    async with async_session() as session:
        try:
            results = (
                await session.execute(
                    select(Users_statistics.day, Users_statistics.all_users)
                    .where(Users_statistics.day >= first_day)
                    .order_by(Users_statistics.day.desc())
                )
            ).all()

        except Exception as e:
            logger.error(
                f"Ошибка при получении количества пользователей в файле bot_requests по причине: {e}"
            )
            return False

        if not results:
            logger.error("Отсутствуют данные о количестве пользователей")
            return False

        days, users = map(list, zip(*results))

        return {"days": days, "users": users}


async def count_of_users_activity(first_day: date) -> dict[str, tuple] | bool:
    """Запрос количества активных пользователей за каждый день периода.
    Args:
        first_day: - Первый день периода для выборки данных.
    Returns:
        dict: - Словарь имеет аргументы 'days', 'active_users', 'all_users'
    """
    async with async_session() as session:
        try:
            results = (
                await session.execute(
                    select(
                        Users_statistics.day,
                        Users_statistics.users_activity,
                        Users_statistics.all_users,
                    )
                    .where(Users_statistics.day >= first_day)
                    .order_by(Users_statistics.day.desc())
                )
            ).all()
        except Exception as e:
            logger.error(
                f"Ошибка при получении активности пользователей в файле bot_requests по причине: {e}"
            )
            return False

        if not results:
            logger.error("Отсутствуют данные об активности пользователей")
            return False

        results = list(map(tuple, results))
        try:
            days, users_activity, all_users = zip(*results)
        except Exception as e:
            print(e)
        return {"days": days, "active_users": users_activity, "all_users": all_users}
    

async def get_all_tg_id(iter_number: int, limit: int) -> list:
    """Получить тг id пользователей порционно"""  
    async with async_session() as session:
        try:
            result = (await session.scalars(select(User.tg_id).offset(iter_number * limit).limit(limit))).all()
        except:
            logger.warning(f'Не удалось получить tg id во время итерации {iter_number}')

        return result

