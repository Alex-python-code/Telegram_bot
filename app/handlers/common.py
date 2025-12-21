from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.def_source as dsrc
import app.bot_database.bot_requests as rq

import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

common_router = Router()


@common_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if await rq.is_user_first(message.from_user.id):
        await rq.reg_user(
            message.from_user.id, message.from_user.username, datetime.now()
        )
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


@common_router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: FSMContext):
    user_state = await state.get_state()
    if user_state:
        await state.clear()
    await callback.answer("Меню открыто")
    await callback.message.answer(
        "Это главное меню\nЗдесь вы можете вабрать интересующие разделы",
        reply_markup=kb.main_menu,
    )


@common_router.message(F.text == "Как дела?")
async def how_are_you_get(message: Message):
    await message.answer("Нормально")


@common_router.message(F.photo)
async def message_is_photo(message: Message):
    await message.reply("Это фото, но я не умею обрабатывать фотографии")


@common_router.message(F.text == "Профиль")
async def user_profile(message: Message):
    data = await dsrc.get_user_profile(message.from_user.id)
    await message.answer(
        f"Ваше имя: {data['user_name']}\n\
Темы новостей: {data['news_type']}\n\
Виды источников новостей: {data['news_sources']}\n\
Исключённые источники: {data['exclude_news_sources']}"
    )
