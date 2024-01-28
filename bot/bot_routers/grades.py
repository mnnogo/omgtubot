from re import Match

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

import database
import database.delete
import database.get
import database.other
import database.update
import keyboards.grades
import misc.utils
from logger import logging

# рутер для подключения в основном файле
router = Router()
r"""Router for grades button"""

# конфигурация логгинга
logging = logging.getLogger(__name__)


# нажатие кнопки "Посмотреть зачетку"
@router.message(F.text == 'Посмотреть зачетку')
async def view_all_grades(message: Message):
    if not database.other.is_user_authorized(message.from_user.id):
        await message.reply('Вы еще не авторизованы. Для начала пройдите <b>Авторизацию</b>.')
        return

    # семестр, выбранный пользователем при регистрации или настройке
    users_term = database.get.get_user_term(user_id=message.from_user.id)

    await show_term_grades(message.from_user.id, users_term, message_reply_to=message)


# при нажатии на кнопку с callback формата btn_term(число) передать число в виде Match[str] как btn_name
# (тот же тип, что и при вызове re.search())
@router.callback_query(F.data.regexp(r'btn_term(\d+)$').as_("btn_name"))
async def btn_term_pressed(query: CallbackQuery, btn_name: Match[str]):
    selected_term = int(btn_name.group(1))

    await show_term_grades(query.from_user.id, selected_term, message_to_edit=query.message)


@router.callback_query(F.data == 'btn_exit')
async def btn_exit_pressed(query: CallbackQuery):
    await query.message.delete()
    await query.message.answer(text='Вы вышли из просмотра оценок.')


# показать все оценки за семестр X
async def show_term_grades(user_id: int, term: int, *, message_reply_to: Message = None, message_to_edit: Message = None) \
        -> None:
    r"""If message with grades was sent to user once, give it as parameter, so it can be edited instead of sending
    new one. Otherwise, give message_reply_to. At least one of them should be given. If both are given, only
    message_to_edit is used."""
    if message_to_edit is None and message_reply_to is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ValueError(error_msg)

    grades_info_list = database.get.get_user_grades(user_id=user_id, term=term)

    msg = f'<b>Оценки в {term} семестре:</b>\n'

    for grade_info in grades_info_list:
        msg += f'\n{misc.utils.format_grade_message(grade_info)}\n'
    msg = msg[:-1]

    # количество семестров у пользователя
    user_max_term = database.get.get_user_max_term(user_id=user_id)
    if message_to_edit is None:
        await message_reply_to.reply(text=msg, reply_markup=keyboards.grades.get_grades_default_kb(user_max_term))
    else:
        await message_to_edit.edit_text(text=msg, reply_markup=keyboards.grades.get_grades_default_kb(user_max_term))
