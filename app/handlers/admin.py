from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
import app.def_source as dsrc
import app.bot_database.bot_requests as rq

from .states import Admin_panel

import logging
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()
logger = logging.getLogger(__name__)

admin_router = Router()


@admin_router.message(Command("admin"))
async def start_as_admin(message: Message, state: FSMContext):
    if message.from_user.id in list(map(int, os.getenv("ADMINS").split())):
        await state.set_state(Admin_panel.run_as_admin)
        await message.answer("Админ панель открыта", reply_markup=kb.admin_panel)
    else:
        logger.info("Пользователь не является админом")


@admin_router.message(F.text == "Активная аудитория", Admin_panel.run_as_admin)
async def get_active_audience_period(message: Message, state: FSMContext):
    await message.answer(
        "За какой период показать статистику?", reply_markup=kb.period_of_statistic
    )
    await state.set_state(Admin_panel.make_activity_chart)


@admin_router.message(F.text, Admin_panel.make_activity_chart)
async def send_user_activity_chart(message: Message, state: FSMContext):
    periods = {"7 дней": 7, "30 дней": 30}
    if message.text not in periods.keys():
        await message.answer("Такой период отсутствует")
        await state.set_state(Admin_panel.run_as_admin)
        return
    try:
        response = await dsrc.user_activity_chart(periods.get(message.text))
        if not response:
            raise ValueError("response пуст")

    except Exception as e:
        logger.error(f"Не удалось создать диаграмму: {e}")
        await message.answer("Не удалось создать диаграмму")
        await state.set_state(Admin_panel.run_as_admin)
        return

    chart = FSInputFile("active_audience.png")
    await message.answer_photo(
        photo=chart,
        caption=f"Количество пользователей за {periods.get(message.text)} дней",
        reply_markup=kb.admin_panel,
    )
    await state.set_state(Admin_panel.run_as_admin)
    return


@admin_router.message(F.text == "Найти пользователя", Admin_panel.run_as_admin)
async def find_user(message: Message, state: FSMContext):
    await message.answer("Введи имя пользователя")
    await state.set_state(Admin_panel.enter_username)


@admin_router.message(F.text, Admin_panel.enter_username)
async def enter_username(message: Message, state: FSMContext):
    """Вывод данных о пользователе"""
    try:
        if not message.text.isdigit():
            username = message.text.replace("@", "")
            tg_id = await rq.convert_username_to_tg_id(username)
        else:
            tg_id = message.text
        about_user = await rq.user_profile(tg_id)
    except Exception as e:
        logger.error(f"Ошибка при запросе профиля пользователя: {e}")
        return
    await message.answer(
        f"Тг id: {about_user[0].tg_id}\n\
Имя пользователя: @{about_user[0].user_name}\n\
Дата регистрации: {about_user[0].reg_date}\n\
Последняя активность: {about_user[0].last_activity}\n\
Темы новостей: {about_user[1].news_themes}\n\
Виды источников новостей: {about_user[1].news_sources}\n\
Исключённые источники: {about_user[1].exclude_news_sources}"
    )
    await state.set_state(Admin_panel.run_as_admin)


@admin_router.message(F.text == "Приток аудитории", Admin_panel.run_as_admin)
async def get_all_audience_period(message: Message, state: FSMContext):
    await message.answer(
        "За какой период показать статистику?",
        reply_markup=kb.period_of_statistic,
    )
    await state.set_state(Admin_panel.make_audience_chart)


@admin_router.message(F.text, Admin_panel.make_audience_chart)
async def send_audience_chart(message: Message, state: FSMContext):
    """Создание и отправка диаграммы с количеством пользователей"""
    periods = {"7 дней": 7, "30 дней": 30}
    if message.text not in periods.keys():
        await message.answer("Такой период отсутствует")
        await state.set_state(Admin_panel.run_as_admin)
        return
    try:
        response = await dsrc.chart_of_all_users(periods.get(message.text))
        if not response:
            raise ValueError("response пуст")

    except Exception as e:
        logger.error(f"Не удалось создать диаграмму: {e}")
        await message.answer("Не удалось создать диаграмму")
        await state.set_state(Admin_panel.run_as_admin)
        return

    chart = FSInputFile("audience_for_period.png")
    await message.answer_photo(
        photo=chart,
        caption=f"Количество пользователей за {periods.get(message.text)} дней",
        reply_markup=kb.admin_panel,
    )
    await state.set_state(Admin_panel.run_as_admin)
    return


@admin_router.message(F.text == 'Разослать сообщение', Admin_panel.run_as_admin)
async def get_message_for_send(message: Message, state: FSMContext):
    await message.answer('Напишите сообщение которое будет отослано каждому пользователю')
    await state.set_state(Admin_panel.send_message)


@admin_router.message(F.text, Admin_panel.send_message)
async def send_message(message: Message, state: FSMContext):
    from bot import bot
    iter_number = 0

    while True:
        tg_ids = await rq.get_all_tg_id(iter_number, 100)
        if not tg_ids:
            return
        
        for tg_id in tg_ids:
            try:
                await bot.send_message(tg_id, message.text)
            except Exception as e:
                logger.warning(f'Не удалось отправить сообщение пользователю {tg_id} по причине {e}')
    
            await asyncio.sleep(0.05)

        iter_number += 1
        await asyncio.sleep(0.1)

    
@admin_router.message(F.text == 'Sticky Factor', Admin_panel.run_as_admin)
async def get