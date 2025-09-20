from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import source.text_source as tsrc
import source.def_source as dsrc
import app.bot_database.bot_requests as rq

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
        await rq.reg_user(message.from_user.id, message.from_user.first_name)
        await message.answer(tsrc.greeting, reply_markup=kb.first_start)
    else:
        await state.clear()
        await message.reply(
            f"Привет!\nТвой ТГ ID: {message.from_user.id}\nА вот твоё имя {message.from_user.first_name}\nНу а это твой ник @{message.from_user.username}",
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


@router.message(F.text == "Новости")
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
        "Напишите час (или часы) за которые вы хотите посмотреть новости.\nПример: 1 18 19 17"
    )
    await state.set_state(Viewing_news.select_time)


@router.message(Viewing_news.select_time, F.text)
async def selecting_hour(message: Message, state: FSMContext):
    """Выбор часа новостей"""
    # print(await state.get_state())

    if await dsrc.input_is_digit(message, None):
        await state.update_data(select_time=message.text.split())
    else:
        await message.answer("это не время!")
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


@router.message(F.text, Viewing_news.user_news)
async def today_news(message: Message, state: FSMContext):
    """Показ новостей за выбранный день"""
    encode_news_days = {"Сегодня": 0, "Вчера": 1, "Позавчера": 2}

    if message.text == "В главное меню":
        await state.clear()
        await go_to_main_menu(message, state)
        return

    if message.text not in ["Сегодня", "Вчера", "Позавчера", "Ещё новости"]:
        await message.answer(
            "Не корректный запрос!\n Выберите один из пунктов на клавиатуре"
        )
        return

    if message.text != "Ещё новости":  # Если первый запрос
        preferences = await rq.get_users_news_preferences(message.from_user.id)
        if not preferences:
            await message.answer(
                "У Вас не настроены новостные предпочтения, поэтому Вы не можете просматривать новости.\nПожалуйста, настройте свои предпочтения в настройках"
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
    # print(f"user preferences: {preferences.news_sources, preferences.news_types, preferences.exclude_news_sources, 5, news_viewing_state['page_number'], news_viewing_state['select_day'], news_viewing_state["select_time"]}")
    if len(news_viewing_state["user_news"]) == 0:
        # print("get request")
        today_news = await rq.get_news_for_user(
            preferences.news_sources,
            preferences.news_types.split(),
            preferences.exclude_news_sources,
            5,
            news_viewing_state["page_number"],
            news_viewing_state["select_day"],
            news_viewing_state["select_time"],
        )
        await state.update_data(user_news=today_news[0], page_number=today_news[1])
        news_viewing_state = await state.get_data()
    # print(f'news_viewing_state["user_news"] = {news_viewing_state["user_news"]}')
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


# @router.callback_query(F.data == 'set_news_region')
# Обновление только региона новостей пользователя
async def set_news_region(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Set_only_news_region.only_news_region)
    await callback.answer("")
    if not await rq.does_user_have_preferences(callback.message.from_user.id):
        await callback.message.answer(
            "У Вас не настроены новостные предпочтения, поэтому вы не можете изменить регион своих новостей"
        )
        await settings(callback.message)
        return
    await callback.message.answer(
        f"Для персонализации новостей выберите свой регион.\nЕсли ваш регион отстуствует, то можете выбрать 0 (Россия)\n\n\
{await dsrc.all_regions('id and name')}\nВведите одно число без разделительных знаков\nПример: 18"
    )


# @router.message(Set_only_news_region.only_news_region)
# Запись в бд только региона новостей пользователя
async def set_news_region(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) not in await dsrc.all_regions(
        "id"
    ):
        await message.answer(
            "Вы ввели не корректное значение, пожалуйста, выберите один из поддерживаемых регионов\nПример: 18"
        )
        return
    await state.update_data(only_news_region=message.text)
    users_location = await state.get_data()
    # print(users_location["only_news_region"])
    await rq.reset_users_region(users_location["only_news_region"])
    await state.clear()
    await message.answer("Ваш регион успешно обновлён")


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

    if  message.text not in encode_sources.keys():
        await message.answer("Такого источника нет")
        return

    await state.update_data(source=encode_sources[message.text])
    await state.set_state(Set_preferences.news_types)
    await message.answer(
        "Выберите новостные темы которые Вам интересны.\n\nНапишите через пробел и без разделительных знаков.\nПример: 1 7 3\n\n1. Спортивные\n2. Политически\n3. Образование\n4. Научные\n5. Экономические\n6. Социальные\n7. Культурные\n8. Программирование",
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

    await message.answer(
        f"""Выберите новостные источники которые Вам НЕ нравятся\n                  
{tsrc.number_select_format}{await dsrc.all_news_sources(user_news_preferences["source"])}""",
        reply_markup=kb.go_to_main_menu,
    )


@router.message(Set_preferences.exclude_news_sources)
async def preferences_five(message: Message, state: FSMContext):
    """Запись новостных предпочтений в бд"""
    await state.update_data(exclude_news_sources=message.text)
    user_news_preferences = await state.get_data()

    if user_news_preferences["source"] == 2:
        exclude_news_sources_limit = 4
    else:
        exclude_news_sources_limit = 6

    if not await dsrc.input_is_digit(message, exclude_news_sources_limit):
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
        f"Ваши предпочтения настроены!\nПосмотреть или изменить свои предпочтения вы можете в настройках\n{user_news_preferences}",
        reply_markup=kb.finish_select_of_news_preferences,
    )
