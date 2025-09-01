from parsers.parser_database.sync_parser_models import News_source
from parsers.parser_database.sync_parser_models import Session
from sqlalchemy import select

def get_source_info(source_id):
    '''Принимает на вход id источника и возвращает информацию о нём'''
    with Session() as s:
        try:
            source = s.scalars(select(News_source).where(News_source.source_id == source_id)).first()
        except Exception as e:
            print(f'Error getting source info: {e}')
            return []
        return source