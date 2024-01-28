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


# конфигурация логгинга
logging = logging.getLogger(__name__)


@router.message(F.from_user.id == misc.env.DEVELOPER_CHAT_ID, F.text == 'Обновить клавиатуру у всех')
async def btn_fixkeyboard_pressed(message: Message):
    all_users_id = database.get.get_users_list()

    for user_id in all_users_id:
        await bot.send_message(user_id, 'Клавиатура обновлена.', reply_markup=keyboards.main.get_main_keyboard(user_id))

