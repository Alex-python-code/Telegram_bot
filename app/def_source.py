import app.bot_database.bot_requests as rq
from async_lru import alru_cache
from datetime import date, timedelta


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


async def chart_of_all_users(period: int) -> bool:
    """График количества пользователей.

    Args:
        period (int): Период за который идёт анализ
    """
    today = date.today()
    first_day_of_period = today - timedelta(days=period)
    audience_for_period = await rq.count_users_in_period(first_day_of_period)

    if not audience_for_period:
        return False

    await make_chart(
        audience_for_period, period, "audience_for_period.png", "Пользователи", "Дата"
    )
    return True


async def user_activity_chart(period: int) -> bool:
    """График активности пользователей.

    Args:
        period (int): Период за который идёт анализ
    """
    today = date.today()
    first_day = today - timedelta(days=period)
    result = await rq.count_of_users_activity(first_day)

    if not result:
        return False

    dates = [day for day in result.get("days")]
    active_users = [users for users in result.get("active_users")]
    all_users = [users for users in result.get("all_users")]
    activity_coeff = []
    for active, all in zip(active_users, all_users):
        activity_coeff.append(active / all)

    print(dates)
    print(activity_coeff)
    await make_chart(
        {"days": dates, "users": activity_coeff},
        period,
        "active_audience.png",
        "Коэффициент активности",
        "Дата",
    )
    return True


async def make_chart(
    audience_for_period: dict, period: int, image_name: str, xlabel: str, ylabel: str
) -> None:
    """Создание графика с аналитикой пользователей

    Args:
        audience_for_period (dict): Словарь с двумя списками, 'days' - даты, 'users' - значения
        period (int): Период за который идёт анализ
        image_name (str): Имя с которым будет сохранён график
        xlabel (str): Имя вертикальной шкалы
        ylabel (str): Имя горизонтальной шкалы
    """
    import matplotlib.pyplot as plt

    title_of_chart = "Количесво пользователей по дням"
    days = audience_for_period.get("days", [0])
    days = list(map(str, days))
    number_of_users = audience_for_period.get("users", [0])

    if period == 30:
        days = days[::7]
        number_of_users = number_of_users[::7]
        title_of_chart = "Количество пользователей по неделям"

    days.sort()
    number_of_users.sort()

    plt.bar(days, number_of_users, color="steelblue")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title_of_chart)
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(image_name, dpi=300)
