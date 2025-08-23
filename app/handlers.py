from aiogram import F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from asyncio import sleep

import app.keyboards as kb
import source.text_source as tsrc
import source.def_source as dsrc
import app.bot_database.bot_requests as rq

router = Router()

class Set_preferences(StatesGroup):
    source = State()
    news_types = State()
    exclude_news_sources = State()
    news_region = State()
    
class Set_only_news_region(StatesGroup):
    only_news_region = State()

class Reg(StatesGroup):
    name = State()
    number = State()


@router.message(F.text == 'Хочу ссылочку на хранилище')
async def send_url(message: Message):
    await message.answer('Ой, да пожалуйста, вот Ваша ссылочка',
                         reply_markup=kb.settings)

@router.message(CommandStart())
async def cmd_start(message: Message):
    if await rq.is_user_first(message.from_user.id):
        await rq.reg_user(message.from_user.id, message.from_user.first_name)
        await message.answer(tsrc.greeting,
                            reply_markup = kb.first_start)
    else:
        await message.reply(f'Привет!\nТвой ТГ ID: {message.from_user.id}\nА вот твоё имя {message.from_user.first_name}\nНу а это твой ник @{message.from_user.username}',
                        reply_markup = kb.main_menu)
    
@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery, state: State):
    user_state = await state.get_state()
    print(user_state)
    if user_state:
        await state.clear()
    await callback.answer('Меню открыто')
    await callback.message.answer('Это главное меню\nЗдесь вы можете вабрать интересующие разделы',
                                  reply_markup = kb.main_menu)

@router.message(Command('help'))
async def get_help(message: Message):
    regions = await dsrc.all_regions('id')
    await message.answer(str(regions))

@router.message(F.text == 'Как дела?')
async def how_are_you_get(message: Message):
    await message.answer('Потихоньку, как сам?')
    
@router.message(F.photo)
async def message_is_photo(message: Message):
    await message.reply('Это фото, но я не умею обрабатывать фотографии')
    
@router.message(F.text == 'Профиль')
async def user_profile(message: Message):
    data = await dsrc.get_user_profile(message.from_user.id)
    
    await message.answer(f'Ваше имя: {data['user_name']}\n\
Подписка на рассылку новостей: {data['mailing']}\n\
Тип новостей: {data['news_type']}\n\
Источники новостей: {data['news_sources']}\n\
Исключённые источники: {data['exclude_news_sources']}\n\
Регион новостей: {data['news_region']}')
    
    
@router.message(F.text == 'Настройки')
#Добавить функционал просмотра записанной локации пользователя через запрос в бд
async def settings(message: Message):
    await message.answer('Настройки открыты', reply_markup=kb.settings)

@router.callback_query(F.data == 'catalog')
async def catalog(callback: CallbackQuery):
    await callback.answer('')
    await callback.message.answer('Нууу...\nКаталог пока пуст')


@router.callback_query(F.data == 'set_news_region')
#Обновление только региона новостей пользователя
async def set_news_region(callback: CallbackQuery, state: State):
    await state.set_state(Set_only_news_region.only_news_region)
    await callback.answer('')
    if not await rq.does_user_have_preferences(callback.message.from_user.id):
        await callback.message.answer("У Вас не настроены новостные предпочтения, поэтому вы не можете изменить регион своих новостей")
        await settings(callback.message)
        return
    await callback.message.answer(f'Для персонализации новостей выберите свой регион.\nЕсли ваш регион отстуствует, то можете выбрать 0 (Россия)\n\n\
{await dsrc.all_regions('id and name')}\nВведите одно число без разделительных знаков\nПример: 18')

@router.message(Set_only_news_region.only_news_region)
#Запись в бд только региона новостей пользователя
async def set_news_region(message: Message, state: State):
    if not message.text.isdigit() or not int(message.text) in await dsrc.all_regions('id'):
            await message.answer('Вы ввели не корректное значение, пожалуйста, выберите один из поддерживаемых регионов\nПример: 18')
            return
    await state.update_data(only_news_region = message.text)
    users_location = await state.get_data()
    print(users_location['only_news_region'])
    await rq.reset_users_region(users_location['only_news_region'])
    await state.clear()
    await message.answer('Ваш регион успешно обновлён')


@router.callback_query(F.data == 'preferences')
#Источники новостей
async def preferences_one(callback: CallbackQuery, state: State):
    await state.set_state(Set_preferences.source)
    await callback.answer('')
    await callback.message.answer('Выберите источники',
                                  reply_markup=kb.news_source)
    
@router.message(Set_preferences.source, F.text)
#Темы новостей
async def preferences_two(message: Message, state: State):
    if not message.text in tsrc.news_sources:
        await message.answer("Такого источника нет")
        return
    await state.update_data(source = message.text)
    await state.set_state(Set_preferences.news_types)
    await message.answer(f'Выберите новостные темы которые Вам интересны.\n{tsrc.number_select_format}{await dsrc.all_news_themes()}',
                        reply_markup=kb.go_to_main_menu)
    
@router.message(Set_preferences.news_types, F.text)
async def preferences_three(message: Message, state: State):
    '''Исключение источников новостей'''
    all_news_sources = await rq.get_count_of_news_sources()
    #print(all_news_sources)
    if not await dsrc.input_is_digit(message, all_news_sources):
        return
    await state.update_data(news_types = message.text)
    await state.set_state(Set_preferences.exclude_news_sources)
    user_news_preferences = await state.get_data()
    sources_encode = {'Официальные': 0, 'Не официальные': 1}
    if user_news_preferences['source'] == 'Официальные' or user_news_preferences["source"] == 'Не официальные':
        await message.answer(f'Выберите новостные источники которые Вам не нравятся\n{tsrc.number_select_format}{await dsrc.all_news_sources(sources_encode[user_news_preferences['source']])}',
                             reply_markup=kb.go_to_main_menu)
    else:
        await message.answer(f'''Выберите новостные источники которые Вам не нравятся
{tsrc.number_select_format}Официальные:
{await dsrc.all_news_sources(sources_encode['Официальные'])}\n
Не официальные:
{await dsrc.all_news_sources(sources_encode['Не официальные'])}''',
                             reply_markup=kb.go_to_main_menu)
    
@router.message(Set_preferences.exclude_news_sources, F.text)
#Регион новосетей пользователя
async def preferences_four(message: Message, state: State):
    user_news_preferences = await state.get_data()
    if user_news_preferences['source'] == 'Оба источника':
        exclude_news_sources_limit = 6
    else:
        exclude_news_sources_limit = 3
    if not await dsrc.input_is_digit(message, exclude_news_sources_limit):
        return
    await state.update_data(exclude_news_sources = message.text)
    await state.set_state(Set_preferences.news_region)
    await message.answer(f'Для персонализации новостей выберите свой регион.\nЕсли ваш регион отстуствует, то можете выбрать 0 (Россия)\n\n\
{await dsrc.all_regions('id and name')}\nВведите одно число без разделительных знаков\nПример: 18', reply_markup=kb.go_to_main_menu)
    
@router.message(Set_preferences.news_region)
#Запись новостных предпочтений в бд
async def preferences_five(message: Message, state: State):
    if not message.text.isdigit() or ' ' in message.text or not int(message.text) in await dsrc.all_regions('id'):
        await message.answer('Вы ввели не корректное значение, пожалуйста, выберите один из поддерживаемых регионов\nПример: 18')
        return
    await state.update_data(news_region = message.text)
    user_news_preferences = await state.get_data()
    tg_id = message.from_user.id
    await rq.set_users_preferences(tg_id, user_news_preferences['source'], user_news_preferences['news_types'], user_news_preferences['exclude_news_sources'], user_news_preferences['news_region'])
    await state.clear()
    await message.answer(f'Ваши предпочтения настроены!\nПосмотреть или изменить свои предпочтения вы можете в настройках\n{user_news_preferences}', 
                         reply_markup=kb.finish_select_of_news_preferences)
    

    