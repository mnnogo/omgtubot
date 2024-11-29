from aiogram import Router, F
from aiogram.types import Message

import misc.env
import keyboards.panel_admin
import strings
from misc.logger import logging
from bot_init import dp

from handlers.adminpanel import fixkeyboard, mailing, sqlquery, goback

# рутер для подключения в основном файле
router = Router()
r"""Router for admin panel button"""
router.message.filter(F.from_user.id == misc.env.DEVELOPER_CHAT_ID)


# конфигурация логгинга
logging = logging.getLogger(__name__)

# подключение рутеров из файлов
dp.include_routers(
    fixkeyboard.router, mailing.router, sqlquery.router, goback.router
)


@router.message(F.text == strings.OPEN_ADMIN_PANEL)
async def btn_admin_panel_pressed(message: Message):
    await message.reply(text='Кнопки', reply_markup=keyboards.panel_admin.get_admin_panel_keyboard())
