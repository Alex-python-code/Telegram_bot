from aiogram.fsm.state import State, StatesGroup


class Set_news_mailing(StatesGroup):
    set_time = State()


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
    news_themes = State()
    exclude_news_sources = State()


class Admin_panel(StatesGroup):
    run_as_admin = State()
    enter_username = State()
    make_audience_chart = State()
    make_activity_chart = State()
    send_message = State()
