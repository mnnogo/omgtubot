from aiogram import Router, F
from aiogram.types import Message

import database.get
import keyboards.main
from misc.logger import logging
import misc.env
from bot_init import bot

# рутер для подключения в основном файле
router = Router()
r"""Router for settings button"""
router.message.filter(F.from_user.id == misc.env.DEVELOPER_CHAT_ID)


# конфигурация логгинга
logging = logging.getLogger(__name__)


@router.message(F.text == 'Назад')
async def btn_goback_pressed(message: Message):
    await message.reply("Кнопки", reply_markup=keyboards.main.get_main_keyboard(misc.env.DEVELOPER_CHAT_ID))
