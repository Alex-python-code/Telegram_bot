import app.bot_database.bot_requests as rq
from async_lru import alru_cache


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
