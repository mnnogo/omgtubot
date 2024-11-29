from aiogram import Router, F
from aiogram.types import Message

import database.delete
import database.get
import database.other
import database.update
import misc.utils
import strings
from misc.logger import logging

# рутер для подключения в основном файле
router = Router()
r"""Router for view all works button"""


# конфигурация логгинга
logging = logging.getLogger(__name__)


# нажатие кнопки "Посмотреть список работ"
@router.message(F.text == strings.VIEW_WORKS)
async def view_all_works_command(message: Message):
    if not database.other.is_user_authorized(message.from_user.id):
        await message.reply('Вы еще не авторизованы. Для просмотра списка работ пройдите <b>Авторизацию</b>.')
        return

    # получение логина из БД по телеграм айди
    login = database.get.get_user_login(message.from_user.id)

    # получение работ из БД по логину
    all_works = database.get.get_student_works(login=login)

    i = 1
    msg = '<b>Список Ваших работ:</b>\n'
    for work in all_works:
        if i % 20 == 0:
            await message.answer(msg)
            msg = ''

        msg += f'\n{misc.utils.format_work_message(work)}\n'
        i += 1

    await message.answer(msg)
