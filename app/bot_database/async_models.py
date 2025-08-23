from sqlalchemy import BigInteger, String, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, sessionmaker, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

engine = create_async_engine(url = 'sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    
    tg_id = mapped_column(BigInteger, primary_key=True)
    user_name = mapped_column(Text)
    subscrible_for_mailing: Mapped[bool] = mapped_column(nullable=True)
    
class User_preferences(Base):
    __tablename__ = 'users_preferences'
    
    tg_id = mapped_column(BigInteger, ForeignKey('users.tg_id'), primary_key=True)
    news_sources: Mapped[int] = mapped_column(ForeignKey("news_sources.source_id"))
    news_types: Mapped[int] = mapped_column(ForeignKey("news_sources.source_id"))
    exclude_news_sources: Mapped[int] = mapped_column(nullable=True)
    news_region: Mapped[str] = mapped_column(String(50), nullable=True)
    
class News(Base):
    __tablename__ = 'news'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    news_header = mapped_column(Text)
    news_body = mapped_column(Text)
    source_url = mapped_column(Text)
    source_group: Mapped[int] = mapped_column() #Телеграм или интернет
    news_type: Mapped[int] = mapped_column(ForeignKey('news_sources.source_id')) #Спортивные, политические и тд
    news_theme: Mapped[int] = mapped_column()
    news_region_id: Mapped[int] = mapped_column(ForeignKey('news_regions.region_id'))
    news_datetime: Mapped[int] = mapped_column()
    
class News_region(Base):
    __tablename__ = 'news_regions'
    
    region_name: Mapped[str] = mapped_column(String(30))
    region_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)

class News_source(Base):
    __tablename__ = 'news_sources'

    source_id: Mapped[int] = mapped_column(primary_key=True)
    source_url = mapped_column(Text)
    source_type: Mapped[int] = mapped_column()
    parent_html_news_element = mapped_column(Text)
    parent_html_news_class = mapped_column(Text)
    html_news_element = mapped_column(Text)
    html_news_class = mapped_column(Text)
    sublink_element = mapped_column(Text)
    sublink_class = mapped_column(Text)
    next_page_link_element = mapped_column(Text)
    next_page_link_class = mapped_column(Text)
    class_of_news_blocks = mapped_column(Text)
    date_format = mapped_column(Text)
    time_html_class = mapped_column(Text)
    time_html_element = mapped_column(Text)
    notes = mapped_column(Text)
    
class News_theme(Base):
    __tablename__ = 'news_themes'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    theme_name: Mapped[str] = mapped_column(String(20))
    
    
async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
