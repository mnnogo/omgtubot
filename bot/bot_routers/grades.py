from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from logger import logging
import database

# рутер для подключения в основном файле
router = Router()
r"""Router for grades button"""


# конфигурация логгинга
logging = logging.getLogger(__name__)


TERM_COUNT = 8


# нажатие кнопки "Посмотреть зачетку"
@router.message(F.text == 'Посмотреть зачетку')
async def view_all_grades(message: Message):
    if not database.is_user_authorized(message.from_user.id):
        await message.reply('Вы еще не авторизованы. Для начала пройдите <b>Авторизацию</b>.')
        return

    builder = InlineKeyboardBuilder()

    for i in range(1, (TERM_COUNT - 1) + 1, 2):
        btn_term_left = InlineKeyboardButton(text=f'Семестр {i}', callback_data=f'btn_term{i}')
        btn_term_right = InlineKeyboardButton(text=f'Семестр {i + 1}', callback_data=f'btn_term{i + 1}')
        builder.row(btn_term_left, btn_term_right)

    btn_exit = InlineKeyboardButton(text='Выход', callback_data='btn_exit')
    builder.row(btn_exit)

    # семестр, выбранный пользователем
    users_term = database.get_user_term(message.from_user.id)

    grades_info_list = database.get_user_grades(user_id=message.from_user.id, term=users_term)

    msg = (f'<b>Оценки в {users_term} семестре:</b>\n'
           f'\n')

    for grade_info in grades_info_list:
        msg += f'{grade_info.subject} - <b>{grade_info.grade}</b>\n\n'
    # убрать последние два переноса
    msg = msg[:-2]

    await message.reply(text=msg, reply_markup=builder.as_markup(resize_keyboard=True))

