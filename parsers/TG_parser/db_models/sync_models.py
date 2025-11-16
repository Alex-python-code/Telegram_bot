from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    sessionmaker,
    mapped_column,
)
from sqlalchemy import create_engine

from dotenv import load_dotenv
import os
import logging
from datetime import date

logger = logging.getLogger(__name__)

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

try:
    engine = create_engine(
        url=f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    Session = sessionmaker(engine)
except Exception as e:
    logger.critical(f"Не удалось подключиться к бд в sync_models.py: {e}")


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    tg_id = mapped_column(BigInteger, primary_key=True)
    user_name = mapped_column(Text, nullable=True)
    reg_date: Mapped[date] = mapped_column()
    mailing: Mapped[int] = mapped_column()


class User_preferences(Base):
    __tablename__ = "users_preferences"

    tg_id = mapped_column(BigInteger, primary_key=True)
    news_sources: Mapped[int] = mapped_column()
    news_types: Mapped[int] = mapped_column()
    exclude_news_sources: Mapped[int] = mapped_column(nullable=True)
    news_region: Mapped[str] = mapped_column(String(50), nullable=True)


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(primary_key=True)
    news_header = mapped_column(Text)
    news_body = mapped_column(Text)
    source_name: Mapped[int] = mapped_column()
    source_group: Mapped[int] = mapped_column()  # Телеграм или интернет
    news_theme: Mapped[int] = mapped_column()
    news_time: Mapped[int] = mapped_column()
    news_date: Mapped[int] = mapped_column()
    news_region_id: Mapped[int] = mapped_column()


class News_region(Base):
    __tablename__ = "news_regions"

    region_name: Mapped[str] = mapped_column(String(30))
    region_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)


class News_source(Base):
    __tablename__ = "news_sources"

    source_id: Mapped[int] = mapped_column(primary_key=True)
    source_url = mapped_column(Text)
    source_type: Mapped[int] = mapped_column()
    notes = mapped_column(Text)
    mass_media: Mapped[int] = mapped_column()


class News_theme(Base):
    __tablename__ = "news_themes"

    id: Mapped[int] = mapped_column(primary_key=True)
    theme_name: Mapped[str] = mapped_column(String(20))


def sync_main():
    Base.metadata.create_all(engine)
