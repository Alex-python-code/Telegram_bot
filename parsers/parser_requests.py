from app.database.models import User, User_preferences, News, News_region, News_source, News_theme
from sqlalchemy import select

def get_source_info(source_id):
    '''Принимает на вход id источника и возвращает информацию о нём'''
    with session() as session:
        try:
            source = session(select(News_source).where(News_source.source_id == source_id)).scalars()
        except Exception as e:
            print(f'Error getting source info: {e}')
            return []
        return source