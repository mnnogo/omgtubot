from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from logger import logging
import database

# рутер для подключения в основном файле
router = Router()
r"""Router for grades button"""


# конфигурация логгинга
logging = logging.getLogger(__name__)


# нажатие кнопки "Посмотреть зачетку"
@router.message(F.text == 'Посмотреть зачетку')
async def view_all_grades(message: Message, state: FSMContext):
    if not database.is_user_authorized(message.from_user.id):
        await message.reply('Вы еще не авторизованы. Для начала пройдите <b>Авторизацию</b>.')
        return
