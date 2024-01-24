from aiogram import Router, F
from aiogram.types import Message
from logger import logging
import database

# рутер для подключения в основном файле
router = Router()
r"""Router for view all works button"""


# конфигурация логгинга
logging = logging.getLogger(__name__)


# нажатие кнопки "Посмотреть список работ"
@router.message(F.text == 'Посмотреть список работ')
async def view_all_works_command(message: Message):
    if not database.is_user_authorized(message.from_user.id):
        await message.reply('Вы еще не авторизованы. Для просмотра списка работ пройдите <b>Авторизацию</b>.')
        return

    # получение логина из БД по телеграм айди
    login = database.get_user_login(message.from_user.id)

    # получение работ из БД по логину
    all_works = database.get_old_student_works(login)

    i = 1
    msg = '<b>Список Ваших работ:</b>\n'
    for work in all_works:
        msg += f'\n{i}. {str(work)}\n'
        i += 1

    await message.reply(msg)
