from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import database
import keyboards.sqlquery
from misc.logger import logging
import misc.env


router = Router()
r"""Router for settings button"""
router.message.filter(F.from_user.id == misc.env.DEVELOPER_CHAT_ID)


# конфигурация логгинга
logging = logging.getLogger(__name__)


class States(StatesGroup):
    r"""Stores which stage of the dialogue the client is at"""
    waiting_for_query = State()


@router.message(F.text == 'Выполнить SQL-запрос')
async def btn_sql_query_pressed(message: Message, state: FSMContext):
    await message.reply(text="Введите запрос:", reply_markup=keyboards.sqlquery.get_sqlquery_keyboard())
    await state.set_state(States.waiting_for_query)


# выполнение запроса
@router.message(States.waiting_for_query)
async def complete_the_query(message: Message, state: FSMContext):
    result = database.make_sql_query(message.text)

    await message.reply('Запрос выполнен. Результат: ' + str(result))

    await state.clear()


# нажата кнопка '❌ Отмена'
@router.callback_query(States.waiting_for_query, F.data == 'btn_cancel_query')
async def btn_decline_change_pressed(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await query.message.answer('Операция отменена')
    # выход из ожидания
    await state.clear()
