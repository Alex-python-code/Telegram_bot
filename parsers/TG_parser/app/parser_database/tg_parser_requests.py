from async_model import News_source
from async_model import async_session
from sqlalchemy import select


cash = {}

async def get_source_info(source_name):
    if source_name in cash:
        return cash[source_name]
    
    if len(cash) >= 20:
        cash = {}

    async with async_session() as session:
        try:
            source = session.scalar(select(News_source).where(News_source.notes == source_name))
        except Exception as e:
            print(f'Ошибка при запросе информации об источнике: {e}')

        cash[source_name] = source_name
        
        return source