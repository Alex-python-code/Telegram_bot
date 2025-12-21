from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.def_source as dsrc
import app.bot_database.bot_requests as rq

from .states import Set_preferences, Set_news_mailing

import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

preferences_router = Router()


@preferences_router.message(F.text == "Настройки")
# Добавить функционал просмотра записанной локации пользователя через запрос в бд
async def settings(message: Message):
    await message.answer("Настройки открыты", reply_markup=kb.settings)


@preferences_router.callback_query(F.data == "preferences")
async def preferences_one(callback: CallbackQuery, state: FSMContext):
    """Установка источников новостей"""
    await state.set_state(Set_preferences.source)
    await callback.answer("")
    await callback.message.answer("Выберите источники", reply_markup=kb.news_source)


@preferences_router.message(Set_preferences.source, F.text)
async def preferences_two(message: Message, state: FSMContext):
    """Установка новостных тем"""
    encode_sources = {"Официальные": 0, "Не официальные": 1, "Оба источника": 2}

    if message.text not in encode_sources.keys():
        await message.answer("Такого источника нет")
        return

    await state.update_data(source=encode_sources[message.text])
    await state.set_state(Set_preferences.news_themes)
    await message.answer(
        "Выберите темы которые Вам интересны.\n\nПример записи: 1 7 3\n\n1. Спортивные\n2. Политические\n3. Образование\n4. Научные\n5. Экономические\n6. Социальные\n7. Культурные\n8. Программирование",
        reply_markup=kb.go_to_main_menu,
    )


@preferences_router.message(Set_preferences.news_themes, F.text)
async def preferences_three(message: Message, state: FSMContext):
    """Исключение источников новостей"""
    all_news_sources = 8
    if not await dsrc.input_is_digit(message, all_news_sources):
        return

    await state.update_data(
        news_themes=await dsrc.del_repeated_values(((message.text).split()))
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


@preferences_router.message(Set_preferences.exclude_news_sources)
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
        user_news_preferences["news_themes"],
        user_news_preferences["exclude_news_sources"],
    )
    await state.clear()
    await message.answer(
        "Ваши предпочтения настроены!\nПосмотреть или изменить свои предпочтения вы можете в настройках.",
        reply_markup=kb.finish_select_of_news_preferences,
    )


@preferences_router.message(F.text == "Рассылка")
async def subscribe_to_mailing(message: Message, state: FSMContext):
    await message.answer(
        "Напишите восколько отправлять вам новости по МСК+1, с точностью до часа\nПример: 15\n\nЕсли хотите отказаться от рассылки напишите 25"
    )
    await state.set_state(Set_news_mailing.set_time)


@preferences_router.message(Set_news_mailing.set_time)
async def set_mailing_time(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) > 25:
        await message.answer("Не корректный ввод")
        return

    mailing_time = int(message.text)

    if int(message.text) == 25:
        mailing_time = None

    resp = await rq.set_time_of_mailing(message.from_user.id, mailing_time)

    if not resp:
        await message.answer(
            "Приносим свои извинения, на сервере произошла ошибка. Попробуйте позже"
        )
        await state.clear()
        await message.answer(
            "Это главное меню\nЗдесь вы можете вабрать интересующие разделы",
            reply_markup=kb.main_menu,
        )

        return

    await message.answer("Данные успешно обновлены", reply_markup=kb.main_menu)
    await state.clear()
