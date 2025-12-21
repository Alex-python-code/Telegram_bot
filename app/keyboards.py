from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


settings = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Настроить предпочтения", callback_data="preferences"
            )
        ],
        [InlineKeyboardButton(text="В главное меню", callback_data="main_menu")],
    ]
)

go_to_main_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="В главное меню", callback_data="main_menu")]
    ]
)

finish_select_of_news_preferences = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Завершить", callback_data="main_menu")],
        [InlineKeyboardButton(text="Заново", callback_data="preferences")],
    ]
)

first_start = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Настроить свои предпочтения", callback_data="preferences"
            )
        ],
        [
            InlineKeyboardButton(
                text="Перейти в главное меню", callback_data="main_menu"
            )
        ],
    ]
)


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Новости")],
        [KeyboardButton(text="Архив")],
        [KeyboardButton(text="Настройки"), KeyboardButton(text="Рассылка")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

news_source = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Официальные"),
            KeyboardButton(text="Не официальные"),
        ],  # Далее именуются 0 и 1 соответственно
        [KeyboardButton(text="Оба источника")],
    ],  # Далее именуется 2
    resize_keyboard=True,
    one_time_keyboard=True,
)

share_location = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Поделиться местоположением", request_location=True)],
        [KeyboardButton(text="Oтказываюсь предоставлять")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

news_dates = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Сегодня")],
        [KeyboardButton(text="Вчера")],
        [KeyboardButton(text="Позавчера")],
    ],
    resize_keyboard=True,
)

news_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Ещё новости")],
        [KeyboardButton(text="В главное меню")],
    ],
    resize_keyboard=True,
)

selecting_time_interval_for_news = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="За час")], [KeyboardButton(text="За день")]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

admin_panel = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Активная аудитория"),
            KeyboardButton(text="Найти пользователя"),
        ],
        [KeyboardButton(text="Приток аудитории")],
        [KeyboardButton(text="Разослать сообщение")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

period_of_statistic = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="7 дней")], [KeyboardButton(text="30 дней")]],
    resize_keyboard=True,
    one_time_keyboard=True,
)
