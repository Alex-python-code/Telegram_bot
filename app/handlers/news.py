from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.def_source as dsrc
import app.bot_database.bot_requests as rq
from .states import Viewing_news

from datetime import datetime
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

news_router = Router()

# Константы
NEWS_DAY_MAPPING = {
    "Сегодня": [0],
    "Вчера": [1],
    "Позавчера": [2],
    "Новости": [0, 1, 2],
    "Ещё новости": [3],
}


@news_router.message(F.text == "В главное меню", Viewing_news.select_day)
async def go_to_main_menu(message: Message, state: FSMContext):
    """Возврат в главное меню из просмотра новостей"""
    await state.clear()
    await dsrc.send_main_menu(message)


@news_router.message(F.text == "Архив")
async def news_time_interval(message: Message, state: FSMContext):
    """Выбор временного интервала для просмотра архива новостей"""
    await message.answer(
        "Вы хотите посмотреть новости за определённый час или все новости за определённый день?",
        reply_markup=kb.selecting_time_interval_for_news,
    )
    await state.set_state(Viewing_news.select_time_interval)
    await state.update_data(select_time=[])


@news_router.message(Viewing_news.select_time_interval, F.text == "За час")
async def selecting_type_intervals(message: Message, state: FSMContext):
    """Переход к выбору конкретных часов"""
    await message.answer(
        "Напишите час (или часы) за которые вы хотите посмотреть новости. Пишите время по МСК+1\nПример: 1 12 8"
    )
    await state.set_state(Viewing_news.select_time)


@news_router.message(Viewing_news.select_time, F.text)
async def selecting_hour(message: Message, state: FSMContext):
    """Валидация и сохранение выбранных часов"""

    if not await dsrc.input_is_digit(message, None):
        return

    try:
        hours = [int(h) for h in message.text.split()]

        # Валидация диапазона часов
        if not all(0 <= h <= 23 for h in hours):
            await message.answer("Часы должны быть в диапазоне от 0 до 23")
            return

        await state.update_data(select_time=hours)

    except ValueError:
        logger.warning(f"Invalid hour input: {message.text}")
        await message.answer("Некорректный формат. Введите числа от 0 до 23")
        return

    await state.set_state(Viewing_news.news_for_user)
    await message.answer(
        "Выберите за какой день вы хотите посмотреть новости",
        reply_markup=kb.news_dates,
    )


@news_router.message(F.text == "За день", Viewing_news.select_time_interval)
async def selecting_day(message: Message, state: FSMContext):
    """Выбор просмотра новостей за весь день"""
    await state.update_data(select_time=[])
    await message.answer(
        "Выберите за какой день вы хотите посмотреть новости",
        reply_markup=kb.news_dates,
    )
    await state.set_state(Viewing_news.news_for_user)


@news_router.message(F.text == "Новости")
@news_router.message(F.text, Viewing_news.news_for_user)
async def today_news(message: Message, state: FSMContext):
    """Показ новостей за выбранный день"""

    # Обработка возврата в главное меню
    if message.text == "В главное меню":
        await state.clear()
        await dsrc.send_main_menu(message)
        return

    # Валидация команды
    if message.text not in NEWS_DAY_MAPPING:
        await message.answer(
            "Некорректный запрос!\nВыберите один из пунктов на клавиатуре"
        )
        return

    # Сброс select_time для кнопки "Новости"
    if message.text == "Новости":
        await state.update_data(select_time=[], quick_start=True)

    # Инициализация состояния при первом запросе
    if message.text != "Ещё новости":
        try:
            preferences = await rq.get_users_news_preferences(message.from_user.id)
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}", exc_info=True)
            await message.answer(
                "Произошла ошибка при получении настроек. Попробуйте позже"
            )
            return

        await state.set_state(Viewing_news.news_for_user)

        if not preferences:
            await message.answer(
                "У вас не настроены предпочтения, поэтому вы не можете просматривать новости."
            )
            await state.clear()
            await settings(message)
            return
        
        news_days = [NEWS_DAY_MAPPING[message.text]]
        
        if (await state.get_data()).get('quick_start'):
            news_days = [0, 1, 2]
        
        await state.update_data(
            select_day=news_days,
            num_of_news=0,
            page_number=0,
            user_preferences=preferences,
            news_for_user=[],
        )
    else:
        # Увеличиваем счетчик просмотренных новостей
        viewing_data = await state.get_data()
        await state.update_data(num_of_news=viewing_data.get("num_of_news", 0) + 1)

    # Получаем текущее состояние
    news_viewing_state = await state.get_data()

    # Загружаем новости если кэш пуст
    if not await dsrc.load_news_if_needed(state, news_viewing_state, message):
        return

    # Обновляем состояние после возможной загрузки
    news_viewing_state = await state.get_data()
    news_list = news_viewing_state.get("news_for_user", [])

    # Проверяем наличие новостей
    if not news_list:
        await message.answer("К сожалению, новости закончились или не были найдены :(")
        await state.clear()
        await dsrc.send_main_menu(message)
        return

    # Отправляем первую новость из списка
    current_news = news_list[0]
    await state.update_data(last_activity=datetime.today().timestamp())
    await message.answer(current_news.news_body, reply_markup=kb.news_kb)

    # Удаляем отправленную новость из кэша
    await state.update_data(news_for_user=news_list[1:])


@news_router.message(F.text == "Настройки")
async def settings(message: Message):
    """Открытие меню настроек"""
    await message.answer("Настройки открыты", reply_markup=kb.settings)