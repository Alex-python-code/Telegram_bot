from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.def_source as dsrc
import app.bot_database.bot_requests as rq

import logging
from datetime import date


logger = logging.getLogger(__name__)

router = Router()


class Viewing_news(StatesGroup):
    select_time_interval = State()
    select_time = State()
    select_day = State()
    page_number = State()
    num_of_news = State()
    user_preferences = State()
    user_news = State()


class Set_preferences(StatesGroup):
    source = State()
    news_types = State()
    exclude_news_sources = State()
    # news_region = State()


class Set_only_news_region(StatesGroup):
    only_news_region = State()


class Reg(StatesGroup):
    name = State()
    number = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if await rq.is_user_first(message.from_user.id):
        await rq.reg_user(message.from_user.id, message.from_user.first_name, date.today().strftime("%d/%m/%Y"))
        await message.answer(
            """Здравствуйте!
Рад приветствовать тебя в этом новостном боте.
Сейчас Вы можете настроить свои новостные предпочтения или сразу перейти в основное меню
""",
            reply_markup=kb.first_start,
        )
    else:
        await state.clear()
        await message.reply(
            f"Привет!\nЯ новостной бот. Я могу кратко рассказать что происходит в мире\nВаш ID в системе: {message.from_user.id}",
            reply_markup=kb.main_menu,
        )


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    user_state = await state.get_state()
    # print(user_state)
    if user_state:
        await state.clear()
    await callback.answer("Меню открыто")
    await callback.message.answer(
        "Это главное меню\nЗдесь вы можете вабрать интересующие разделы",
        reply_markup=kb.main_menu,
    )


@router.message(Command("help"))
async def get_help(message: Message):
    regions = await dsrc.all_regions("id")
    await message.answer(str(regions))


@router.message(F.text == "Как дела?")
async def how_are_you_get(message: Message):
    await message.answer("Потихоньку, как сам?")


@router.message(F.photo)
async def message_is_photo(message: Message):
    await message.reply("Это фото, но я не умею обрабатывать фотографии")


@router.message(F.text == "Профиль")
async def user_profile(message: Message):
    data = await dsrc.get_user_profile(message.from_user.id)
    await message.answer(
        f"Ваше имя: {data['user_name']}\n\
Тип новостей: {data['news_type']}\n\
Источники новостей: {data['news_sources']}\n\
Исключённые источники: {data['exclude_news_sources']}"
    )


@router.message(F.text == "В главное меню", Viewing_news.select_day)
async def go_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Это главное меню\nЗдесь вы можете вабрать интересующие разделы",
        reply_markup=kb.main_menu,
    )


@router.message(F.text == "Архив")
async def news_time_interval(message: Message, state: FSMContext):
    await message.answer(
        "Вы хотите посмотреть новости за определённый час или все новости за определённый день?",
        reply_markup=kb.selecting_time_interval_for_news,
    )
    await state.set_state(Viewing_news.select_time_interval)
    await state.update_data(select_time=[])


@router.message(Viewing_news.select_time_interval, F.text == "За час")
async def selecting_type_intervals(message: Message, state: FSMContext):
    await message.answer(
        "Напишите час (или часы) за которые вы хотите посмотреть новости. Пишите время по МСК\nПример: 1 18 19 17"
    )
    await state.set_state(Viewing_news.select_time)


@router.message(Viewing_news.select_time, F.text)
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


@router.message(F.text == "За день", Viewing_news.select_time_interval)
async def selecting_day(message: Message, state: FSMContext):
    await message.answer(
        "Выберите за какой день Вы хотите посмотреть новости",
        reply_markup=kb.news_dates,
    )
    await state.set_state(Viewing_news.user_news)


@router.message(F.text == "Новости")
@router.message(F.text, Viewing_news.user_news)
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
            preferences.news_types.split(),
            preferences.exclude_news_sources.split(),
            5,
            news_viewing_state["page_number"],
            news_viewing_state["select_day"],
            news_viewing_state["select_time"],
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


@router.message(F.text == "Настройки")
# Добавить функционал просмотра записанной локации пользователя через запрос в бд
async def settings(message: Message):
    await message.answer("Настройки открыты", reply_markup=kb.settings)


@router.callback_query(F.data == "preferences")
async def preferences_one(callback: CallbackQuery, state: FSMContext):
    """Установка источников новостей"""
    await state.set_state(Set_preferences.source)
    await callback.answer("")
    await callback.message.answer("Выберите источники", reply_markup=kb.news_source)


@router.message(Set_preferences.source, F.text)
async def preferences_two(message: Message, state: FSMContext):
    """Установка новостных тем"""
    encode_sources = {"Официальные": 0, "Не официальные": 1, "Оба источника": 2}

    if message.text not in encode_sources.keys():
        await message.answer("Такого источника нет")
        return

    await state.update_data(source=encode_sources[message.text])
    await state.set_state(Set_preferences.news_types)
    await message.answer(
        "Выберите темы которые Вам интересны.\n\nПример записи: 1 7 3\n\n1. Спортивные\n2. Политические\n3. Образование\n4. Научные\n5. Экономические\n6. Социальные\n7. Культурные\n8. Программирование",
        reply_markup=kb.go_to_main_menu,
    )


@router.message(Set_preferences.news_types, F.text)
async def preferences_three(message: Message, state: FSMContext):
    """Исключение источников новостей"""
    all_news_sources = 8
    # print(all_news_sources)
    if not await dsrc.input_is_digit(message, all_news_sources):
        return

    await state.update_data(
        news_types=await dsrc.del_repeated_values(((message.text).split()))
    )
    await state.set_state(Set_preferences.exclude_news_sources)

    user_news_preferences = await state.get_data()
    all_sources = await dsrc.all_news_sources(user_news_preferences["source"])
    all_sources_in_str = "0. Ничего не отключать\n"

    for key, value in all_sources.items():
        all_sources_in_str += f"{key}. {value}\n"

    await message.answer(
        f"Отключить новости из:\n\nПример записи: 1 7 3\n\n{all_sources_in_str}",
        reply_markup=kb.go_to_main_menu,
    )


@router.message(Set_preferences.exclude_news_sources)
async def preferences_five(message: Message, state: FSMContext):
    """Запись новостных предпочтений в бд"""

    if message.text == "0":
        await state.update_data(exclude_news_sources="0")
    else:
        await state.update_data(exclude_news_sources=message.text)

    user_news_preferences = await state.get_data()

    exclude_news_sources_limit = await dsrc.all_news_sources(
        user_news_preferences["source"]
    )

    if not await dsrc.input_is_digit(message, len(exclude_news_sources_limit)):
        return

    tg_id = message.from_user.id
    await rq.set_users_preferences(
        tg_id,
        user_news_preferences["source"],
        user_news_preferences["news_types"],
        user_news_preferences["exclude_news_sources"],
    )
    await state.clear()
    await message.answer(
        "Ваши предпочтения настроены!\nПосмотреть или изменить свои предпочтения вы можете в настройках.",
        reply_markup=kb.finish_select_of_news_preferences,
    )
