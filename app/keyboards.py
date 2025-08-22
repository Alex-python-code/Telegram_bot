from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

main = InlineKeyboardMarkup(inline_keyboard = [
    [InlineKeyboardButton(text = 'Каталог', callback_data='catalog')],
    [InlineKeyboardButton(text = 'Корзина', callback_data='basket'), InlineKeyboardButton(text = 'Контакты', callback_data='contacts')]
])

settings = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text = 'Настроить предпочтения', callback_data='preferences'),
     InlineKeyboardButton(text = "Обновить местоположение", callback_data="set_news_region")],
    [InlineKeyboardButton(text="В главное меню", callback_data="main_menu")]
])

go_to_main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text = "В главное меню", callback_data='main_menu')]
])

finish_select_of_news_preferences = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text = 'Завершить', callback_data='main_menu')],
    [InlineKeyboardButton(text = 'Заново', callback_data='preferences')]
])

first_start = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text = "Настроить свои предпочтения", callback_data='preferences')],
    [InlineKeyboardButton(text = "Перейти в главное меню", callback_data='main_menu')]
])


main_menu = ReplyKeyboardMarkup(keyboard = [
    [KeyboardButton(text = "Последнние новости"), KeyboardButton(text = "Подписаться на рассылку")],
    [KeyboardButton(text = "Live режим"), KeyboardButton(text = "Профиль")],
    [KeyboardButton(text = 'Настройки')]],
    resize_keyboard=True,
    one_time_keyboard=True
)

news_source = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text= "Официальные"), KeyboardButton(text='Не официальные')], #Далее именуются 0 и 1 соответственно
    [KeyboardButton(text= "Оба источника")]],#Далее именуется 2
    resize_keyboard=True,
    one_time_keyboard=True
)

share_location = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text = 'Поделиться местоположением', request_location=True)],
    [KeyboardButton(text = "Oтказываюсь предоставлять")]],
    resize_keyboard=True,
    one_time_keyboard=True
)
