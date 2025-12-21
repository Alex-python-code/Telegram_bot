from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.def_source as dsrc
import app.bot_database.bot_requests as rq

from .states import Viewing_news

import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

news_router = Router()


@news_router.message(F.text == "В главное меню", Viewing_news.select_day)
async def go_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Это главное меню\nЗдесь вы можете вабрать интересующие разделы",
        reply_markup=kb.main_menu,
    )


@news_router.message(F.text == "Архив")
async def news_time_interval(message: Message, state: FSMContext):
    await message.answer(
        "Вы хотите посмотреть новости за определённый час или все новости за определённый день?",
        reply_markup=kb.selecting_time_interval_for_news,
    )
    await state.set_state(Viewing_news.select_time_interval)
    await state.update_data(select_time=[])


@news_router.message(Viewing_news.select_time_interval, F.text == "За час")
async def selecting_type_intervals(message: Message, state: FSMContext):
    await message.answer(
        "Напишите час (или часы) за которые вы хотите посмотреть новости. Пишите время по МСК+1\nПример: 1 12 8"
    )
    await state.set_state(Viewing_news.select_time)


@news_router.message(Viewing_news.select_time, F.text)
async def selecting_hour(message: Message, state: FSMContext):
    """Выбор часа новостей"""

    if await dsrc.input_is_digit(message, None):
        await state.update_data(select_time=message.text.split())
    else:
        return
    await state.set_state(Viewing_news.user_news)
    await message.answer(
        "Выберите за какой день Вы хотите посмотреть новости",
        reply_markup=kb.news_dates,
    )


@news_router.message(F.text == "За день", Viewing_news.select_time_interval)
async def selecting_day(message: Message, state: FSMContext):
    await message.answer(
        "Выберите за какой день Вы хотите посмотреть новости",
        reply_markup=kb.news_dates,
    )
    await state.set_state(Viewing_news.user_news)


@news_router.message(F.text == "Новости")
@news_router.message(F.text, Viewing_news.user_news)
async def today_news(message: Message, state: FSMContext):
    """Показ новостей за выбранный день"""
    encode_news_days = {
        "Сегодня": 0,
        "Вчера": 1,
        "Позавчера": 2,
        "Новости": 0,
    }

    if message.text == "В главное меню":
        await state.clear()
        await go_to_main_menu(message, state)
        return

    if message.text not in [
        "Сегодня",
        "Вчера",
        "Позавчера",
        "Ещё новости",
        "Новости",
    ]:
        await message.answer(
            "Не корректный запрос!\n Выберите один из пунктов на клавиатуре"
        )
        return

    if message.text == "Новости":
        await state.update_data(select_time=[])

    if message.text != "Ещё новости":  # Если первый запрос
        preferences = await rq.get_users_news_preferences(message.from_user.id)
        await state.set_state(Viewing_news.user_news)
        if not preferences:
            await message.answer(
                "У Вас не настроены предпочтения, поэтому Вы не можете просматривать новости."
            )
            await state.clear()
            await settings(message)
            return
        await state.update_data(
            select_day=encode_news_days[message.text],
            num_of_news=0,
            page_number=0,
            user_preferences=preferences,
            user_news="",
        )
    else:
        _viewing_data = await state.get_data()
        await state.update_data(num_of_news=_viewing_data["num_of_news"] + 1)

    news_viewing_state = await state.get_data()
    preferences = news_viewing_state["user_preferences"]
    if len(news_viewing_state["user_news"]) == 0:
        today_news = await rq.get_news_for_user(
            preferences.news_sources,
            preferences.news_themes.split(),
            preferences.exclude_news_sources.split(),
            5,
            news_viewing_state["page_number"],
            news_viewing_state["select_day"],
            news_viewing_state["select_time"],
        )
        if not today_news:
            await message.answer(
                "Приносим свои извинения, на сервере произошла ошибка. Попробуйте позже"
            )
            await state.clear()
            await message.answer(
                "Это главное меню\nЗдесь вы можете вабрать интересующие разделы",
                reply_markup=kb.main_menu,
            )
        await state.update_data(user_news=today_news[0], page_number=today_news[1])
        news_viewing_state = await state.get_data()
    if not news_viewing_state["user_news"]:
        await message.answer("К сожалению, новости закончились или не были найдены :(")
        await go_to_main_menu(message, state)
        return
    new = news_viewing_state["user_news"]
    await message.answer(new[0].news_body, reply_markup=kb.news_kb)
    del new[0]
    await state.update_data(user_news=new)


@news_router.message(F.text == "Настройки")
async def settings(message: Message):
    await message.answer("Настройки открыты", reply_markup=kb.settings)
