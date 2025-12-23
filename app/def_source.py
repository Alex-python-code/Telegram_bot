import app.bot_database.bot_requests as rq
import app.keyboards as kb

from datetime import date, timedelta, datetime
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import BaseStorage
from create_bot import bot

from logging import getLogger
from async_lru import alru_cache
import asyncio


logger = getLogger(__name__)


async def send_main_menu(message: Message):
    """Отправляет сообщение с главным меню"""
    await message.answer(
        "Это главное меню\nЗдесь вы можете выбрать интересующие разделы",
        reply_markup=kb.main_menu,
    )


async def load_news_if_needed(
    state: FSMContext, news_viewing_state: dict, message: Message
) -> bool:
    """
    Загружает новости из БД, если кэш пуст.

    Returns:
        True если новости успешно загружены или уже есть в кэше, False при ошибке
    """
    if news_viewing_state["news_for_user"]:
        return True

    preferences = news_viewing_state["user_preferences"]

    try:
        news_data = await rq.get_news_for_user(
            preferences.news_sources,
            preferences.news_themes.split(),
            preferences.exclude_news_sources.split(),
            5,
            news_viewing_state["page_number"],
            news_viewing_state["select_day"],
            news_viewing_state["select_time"],
        )

        if not news_data:
            logger.error("get_news_for_user returned empty result")
            await message.answer(
                "Приносим свои извинения, на сервере произошла ошибка. Попробуйте позже"
            )
            await state.clear()
            await send_main_menu(message)
            return False

        await state.update_data(news_for_user=news_data[0], page_number=news_data[1])
        return True

    except Exception as e:
        logger.error(f"Failed to load news: {e}", exc_info=True)
        await message.answer(
            "Приносим свои извинения, на сервере произошла ошибка. Попробуйте позже"
        )
        await state.clear()
        await send_main_menu(message)
        return False


async def input_digit_limit_check(digits, limit):
    digits = digits.split(" ")
    for digit in digits:
        if int(digit) > limit:
            return False
    return True


async def input_is_digit(message, limit):
    user_message = " ".join((message.text).split())
    if user_message.replace(" ", "").isdigit():
        if not limit:
            return True
        elif await input_digit_limit_check(user_message, limit):
            return True
    await message.answer(
        "Введите пожалуйста значения в корректном формате\nПример: 1 7 3"
    )
    return False


async def all_regions(type_output):
    data = await rq.get_all_regions()
    data.reverse()
    if type_output == "id and name":
        regions = ""
        for region in data:
            regions += f"{region.region_id}. {region.region_name}\n"
        return regions
    if type_output == "id":
        regions_id = []
        for region in data:
            regions_id.append(region.region_id)
        return regions_id
    if type_output == "name":
        regions_name = []
        for region in data:
            regions_name.append(region.region_name)
        return regions_name


async def all_news_themes():
    data = await rq.get_all_news_themes()
    themes = ""
    for theme in data:
        themes += f"{theme.id}. {theme.theme_name}\n"
    return themes


async def get_user_profile(tg_id):
    data = await rq.user_profile(tg_id)
    user = data[0]
    preferences = data[1]
    return {
        "user_name": user.user_name,
        "mailing": user.subscrible_for_mailing,
        "news_type": preferences.news_types,
        "news_sources": preferences.news_sources,
        "exclude_news_sources": preferences.exclude_news_sources,
        "news_region": preferences.news_region,
    }


@alru_cache()
async def all_news_sources(source_type):
    data = await rq.get_all_news_sources(source_type)
    all_sources = {}
    for source in data:
        all_sources[source.source_id] = source.notes
    return all_sources


async def del_repeated_values(message):
    # data = [i for i in message]
    data = sorted(set(message))
    return (" ".join(map(str, data))).strip()


async def news_users_chart(period: int) -> bool:
    """График количества новых пользователей.

    Args:
        period (int): Период за который идёт анализ
    """
    today = date.today()
    first_day_of_period = today - timedelta(days=period + 2)
    audience_for_period = await rq.count_users_in_period(first_day_of_period)

    if not audience_for_period:
        return False

    days = audience_for_period.get("days", [])
    days = days[1::]
    input_users = audience_for_period.get("users", [])
    output_users = [
        input_users[i + 1] - input_users[i] for i in range(len(input_users) - 1)
    ]
    audience_for_period = {"days": days, "users": output_users}

    await make_chart(
        audience_for_period,
        period,
        "new_users_for_period.png",
        "Новые пользователи",
        "Дата",
        "Приток пользователей",
    )
    return True


async def chart_of_all_users(period: int) -> bool:
    """График количества пользователей.

    Args:
        period (int): Период за который идёт анализ
    """
    today = date.today()
    first_day_of_period = today - timedelta(days=period + 1)
    audience_for_period = await rq.count_users_in_period(first_day_of_period)

    if not audience_for_period:
        return False

    await make_chart(
        audience_for_period,
        period,
        "audience_for_period.png",
        "Пользователи",
        "Дата",
        "Количество пользователей",
    )
    return True


async def user_activity_chart(period: int) -> bool:
    """График активности пользователей.

    Args:
        period (int): Период за который идёт анализ
    """
    today = date.today()
    first_day = today - timedelta(days=period + 1)
    result = await rq.count_of_users_activity(first_day)

    if not result:
        return False

    dates = [day for day in result.get("days")]
    active_users = [users for users in result.get("active_users")]
    all_users = [users for users in result.get("all_users")]
    activity_coeff = []
    for active, all in zip(active_users, all_users):
        activity_coeff.append(active / all)

    await make_chart(
        {"days": dates, "users": activity_coeff},
        period,
        "active_audience.png",
        "Коэффициент активности",
        "Дата",
        "Коэффициент активности пользователей",
    )
    return True


async def make_chart(
    audience_for_period: dict,
    period: int,
    file_name: str,
    ylabel: str,
    xlabel: str,
    chart_name: str,
) -> None:
    """Создание графика с аналитикой пользователей

    Args:
        audience_for_period (dict): Словарь с двумя списками, 'days' - даты, 'users' - значения
        period (int): Период за который идёт анализ
        image_name (str): Название с которым будет сохранён график
        xlabel (str): Название горизонтальной шкалы
        ylabel (str): Название вертикальной шкалы
        chart_name (str): Название графика
    """
    import matplotlib.pyplot as plt

    title_of_chart = chart_name
    days = audience_for_period.get("days", [0])
    days = list(map(str, days))
    number_of_users = audience_for_period.get("users", [0])

    days = days[::-1]
    number_of_users = number_of_users[::-1]

    plt.bar(days, number_of_users, color="steelblue")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title_of_chart)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(file_name, dpi=300)
    plt.close()


async def cleanup_expired_states(storage: BaseStorage, timeout_seconds: int):
    while True:
        await asyncio.sleep(60)

        for key, state_data in list(storage.storage.items()):
            data = state_data.data
            last_activity = data.get("last_activity")

            if not last_activity:
                continue

            elapsed = datetime.today().timestamp() - last_activity
            if elapsed > timeout_seconds:
                chat_id = key.chat_id
                user_id = key.user_id

                await storage.set_state(key=key, state=None)
                await storage.set_data(key=key, data={})

                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text="Это главное меню\nЗдесь вы можете выбрать интересующие разделы",
                        reply_markup=kb.main_menu,
                    )
                except Exception as e:
                    logger.warning(f"Не удалось отправить сообщение {user_id}: {e}")
