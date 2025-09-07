from app.bot_database.async_models import async_session
from app.bot_database.async_models import User, User_preferences, News, News_region, News_source, News_theme
from sqlalchemy import select, func


async def is_user_first(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            return False
        return True

async def user_profile(tg_id: int):
    async with async_session() as session:
        user = (await session.execute(select(User).where(User.tg_id == tg_id))).scalars().all()
        preferences = (await session.execute(select(User_preferences).where(User_preferences.tg_id == tg_id))).scalars().all()
        print(f'user {user}, {type(user)}')
        print(f'preferences {preferences}, {type(preferences)}')
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
        if source_type == "all":
            return (await session.scalars(select(News_source))).all()
        return (await session.scalars(select(News_source).where(News_source.source_type == source_type))).all()
    
async def get_count_of_news_sources():
    async with async_session() as session:
        return await session.scalar(select(func.count(News_theme.id)))


async def reg_user(tg_id, user_name):
    async with async_session() as session:
        session.add(User(tg_id = tg_id,
                         user_name = user_name))
        await session.commit()
        
async def set_users_preferences(tg_id, news_source, news_types, exclude_news_sources):
    async with async_session() as session:
        user = await session.scalar(select(User_preferences).where(User_preferences.tg_id == tg_id))
        if not user:
            session.add(User_preferences(tg_id = tg_id,
                                        news_sources = news_source,
                                        news_types = news_types,
                                        exclude_news_sources = exclude_news_sources))
                                        #news_region = news_region))
        elif user:
            user.tg_id = tg_id
            user.news_sources = news_source
            user.news_types = news_types
            user.exclude_news_sources = exclude_news_sources
            #user.news_region = news_region
        await session.commit()
        
async def reset_users_region(location, tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User_preferences).where(User_preferences.tg_id == tg_id))
        user.news_region = location
        await session.commit()
        
async def does_user_have_preferences(tg_id: str):
    async with async_session() as session:
        user = await session.scalar(select(User_preferences).where(User_preferences.tg_id == tg_id))
        if user:
            return True
        return False


async def get_source_info(source_id):
    '''Принимает на вход id источника и возвращает информацию о нём'''
    async with async_session() as session:
        try:
            source = await session.scalar(select(News_source).where(News_source.source_id == source_id))
        except Exception as e:
            print(f'Error getting source info: {e}')
            return []
        return source

async def get_users_news_preferences(tg_id):
    async with async_session() as session:
        preferences = await session.scalar(select(User_preferences).where(User_preferences.tg_id == tg_id))
        return preferences
    
async def get_news_for_user(mass_media, news_themes, exclude_sources, limit, page_number, day):
    async with async_session() as session:
        if mass_media == 2:
            news = (await session.scalars(select(News)
                                         .where(News.news_date == day,
                                                News.source_name != exclude_sources,
                                                News.news_theme == news_themes)
                                         .limit(limit)
                                         .offset(page_number * limit))).all()
        else:
            news = (await session.scalars(select(News)
                                         .where(News.news_date == day,
                                                News.source_group == mass_media,
                                                News.source_name != exclude_sources,
                                                News.news_theme == news_themes)
                                         .limit(limit)
                                         .offset(page_number * limit))).all()
        page_number += 1
        return [news, page_number]