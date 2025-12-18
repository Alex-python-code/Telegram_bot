import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from ai.async_ai_module import AsyncAi
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.client import Client
from pyrogram.enums import ChatType
from parser_rq.tg_parser_requests import get_source_info

load_dotenv()

PARSER_ID = os.getenv("PARSER_ID")
PARSER_HASH = os.getenv("PARSER_HASH")
PHONE_NUM = os.getenv("PHONE_NUM")

app = Client(
    "parser", 
    api_id=PARSER_ID,
    api_hash=PARSER_HASH,
    phone_number=PHONE_NUM
)

class AiUtils:
    @staticmethod
    async def create_prompt(news_text, source_name, time):
        ai_model = "gpt-5-nano"
        assistant_text = 'Тег текста выведи в самом начале и в формате ---"тег" '
        ai_system_text = "Сожми текст, до 30-50 слов, на выходе должен быть красивый лаконочный текст. Если текст является рекламой, а не новостью или просто не имеет смысла, в ответ верни False вместо сжатого текста. Присвой тексту один из тегов Спортивные Политические Образование Научные Экономические Социальные Культурные. не используй вводных конструкций, просто выведи сжатый текст."
        source_info = await get_source_info(source_name)
        data_for_ai_request = {
            "model": ai_model,
            "prompt": ai_system_text + assistant_text + news_text,
            "is_mass_media": source_info.mass_media,
            "source_name": source_info.source_id,
            "time_interval": time,
            "date_interval": 0,
        }
        return data_for_ai_request

# Словарь для отслеживания последних обработанных сообщений
last_message_ids = {}

ai_module = AsyncAi()

@app.on_message(filters.private)
async def private_answer(client: Client, message: Message):
    logger.info("Сообщение в лс")
    await message.reply("Запущен и успешно работает")

async def process_message(message: Message, chat_title: str):
    """Обработка одного сообщения"""
    text = message.caption or message.text
    
    if not text:
        logger.debug(f"Сообщение {message.id} в {chat_title} без текста, пропускаю")
        return
    
    logger.info(f"Обработка сообщения из {chat_title}, ID: {message.id}")
    logger.info(f"Текст (первые 50 символов): {text[:50]}")
    logger.info(f"Дата: {message.date}")
    
    try:
        prompt = await AiUtils.create_prompt(
            text, chat_title, str(message.date.strftime("%H"))
        )
        
        logger.info("Отправка запроса в ИИ")
        await ai_module.main(prompt)
        logger.info(f"Сообщение {message.id} успешно обработано")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения {message.id}: {e}")

async def get_messages_from_channel(chat_id: int, limit: int = 5):
    """Получить список сообщений из канала"""
    messages = []
    try:
        count = 0
        async for message in app.get_chat_history(chat_id, limit=limit):
            messages.append(message)
            count += 1
            if count >= limit:
                break
    except Exception as e:
        logger.error(f"Ошибка получения сообщений из канала {chat_id}: {e}")
    return messages

async def get_all_dialogs():
    """Получить список всех диалогов"""
    dialogs = []
    try:
        async for dialog in app.get_dialogs():
            dialogs.append(dialog)
    except Exception as e:
        logger.error(f"Ошибка получения диалогов: {e}")
    return dialogs

async def poll_channels():
    """Активный опрос каналов на наличие новых сообщений"""
    logger.info("Запуск активного парсинга каналов")
    
    # Интервал проверки в секундах
    CHECK_INTERVAL = 60
    
    while True:
        try:
            dialogs = await get_all_dialogs()
            channels = [d for d in dialogs if d.chat.type == ChatType.CHANNEL]
            
            logger.info(f"Проверка {len(channels)} каналов...")
            
            for dialog in channels:
                chat_id = dialog.chat.id
                chat_title = dialog.chat.title
                
                try:
                    # Получаем последние 5 сообщений из канала
                    messages = await get_messages_from_channel(chat_id, limit=5)
                    
                    if not messages:
                        logger.debug(f"Канал {chat_title} пуст или недоступен")
                        continue
                    
                    # Если это первый запуск для этого канала
                    if chat_id not in last_message_ids:
                        last_message_ids[chat_id] = messages[0].id
                        logger.info(f"Инициализация для канала {chat_title}: последнее сообщение {messages[0].id}")
                        # При первом запуске обрабатываем только самое свежее
                        await process_message(messages[0], chat_title)
                        continue
                    
                    # Проверяем новые сообщения (от новых к старым)
                    for message in messages:
                        message_id = message.id
                        
                        # Если сообщение новее последнего обработанного
                        if message_id > last_message_ids[chat_id]:
                            logger.info(f"Новое сообщение в {chat_title}: {message_id}")
                            
                            # Проверяем, что сообщение не старше 10 минут
                            message_date = message.date
                            if message_date.tzinfo is not None:
                                message_date = message_date.replace(tzinfo=None)
                            
                            time_diff = datetime.now() - message_date
                            if time_diff < timedelta(minutes=10):
                                await process_message(message, chat_title)
                                # Задержка между обработкой сообщений
                                await asyncio.sleep(30)
                            else:
                                logger.info(f"Сообщение {message_id} слишком старое ({time_diff}), пропускаю")
                        else:
                            # Дошли до уже обработанных сообщений
                            break
                    
                    # Обновляем ID последнего сообщения
                    if messages:
                        last_message_ids[chat_id] = messages[0].id
                        
                except Exception as e:
                    logger.error(f"Ошибка при обработке канала {chat_title}: {e}", exc_info=True)
                
                # Небольшая задержка между проверкой каналов
                await asyncio.sleep(2)
            
            logger.info(f"Цикл проверки завершен. Следующая проверка через {CHECK_INTERVAL} секунд")
            await asyncio.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f"Критическая ошибка в poll_channels: {e}", exc_info=True)
            await asyncio.sleep(30)

async def main():
    await app.start()
    logger.info("Userbot запущен")
    
    # Получаем список всех диалогов для проверки
    dialogs = await get_all_dialogs()
    channels = [d for d in dialogs if d.chat.type == ChatType.CHANNEL]
    
    logger.info(f"Подписан на {len(dialogs)} диалогов")
    logger.info(f"Из них каналов: {len(channels)}")
    
    # Выводим список каналов
    for dialog in channels:
        logger.info(f"Канал: {dialog.chat.title} (ID: {dialog.chat.id})")
    
    # Запускаем активный парсинг в фоне
    asyncio.create_task(poll_channels())
    
    await asyncio.Event().wait()

if __name__ == "__main__":
    handler = RotatingFileHandler("userbot.log", maxBytes=1_000_000, backupCount=6)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[handler],
    )
    logger = logging.getLogger(__name__)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Парсер остановлен пользователем")
        app.stop()
    except Exception as e:
        logger.critical(f"Парсер не смог стартовать: {e}", exc_info=True)
        app.stop()