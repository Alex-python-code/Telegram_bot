from aiogram import Router
from aiogram.types import Message

router = Router()

@router.channel_post()
async def parsing_chanels_posts(message: Message):
    print(f'message.text: {message.text} message.date: {message.date}')