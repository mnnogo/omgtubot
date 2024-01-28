from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database.get
import database.other
import misc.env
from logger import logging
from misc.bot_init import bot

# рутер для подключения в основном файле
router = Router()
r"""Router for mailing button"""


# конфигурация логгинга
logging = logging.getLogger(__name__)


class States(StatesGroup):
    r"""Stores which stage of the dialogue the client is at"""
    waiting_for_message = State()
    waiting_for_confirmation = State()


@router.message(F.from_user.id == misc.env.DEVELOPER_CHAT_ID, F.text == 'Сделать рассылку')
async def btn_send_mailing_pressed(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='❌ Отмена', callback_data='btn_cancel_mailing'))

    await message.reply(f'Введите сообщение:', reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(States.waiting_for_message)


# нажата '❌ Отмена' в подтверждении
@router.callback_query(F.data == 'btn_cancel_mailing', States.waiting_for_message)
async def btn_cancel_mailing_pressed(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await query.message.answer('Операция отменена.')
    await state.clear()


# сообщение для рассылки отправлено
@router.message(States.waiting_for_message)
async def mailing_message_sent(message: Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='✅ Да', callback_data='btn_confirm_yes'),
                InlineKeyboardButton(text='❌ Нет', callback_data='btn_confirm_no'))

    await state.update_data(message_to_mail=message.text)

    await message.copy_to(chat_id=message.chat.id, parse_mode=ParseMode.MARKDOWN_V2)
    await message.answer('Разослать сообщение?', reply_markup=builder.as_markup(resize_keyboard=True))
    await state.set_state(States.waiting_for_confirmation)


# нажата '✅ Да' в подтверждении
@router.callback_query(F.data == 'btn_confirm_yes', States.waiting_for_confirmation)
async def btn_confirm_yes_pressed(query: CallbackQuery, state: FSMContext):
    _data = await state.get_data()
    message_to_mail = _data.get('message_to_mail')

    mailing_subscribers_list = database.get.get_mailing_subscribers_id()

    for user_id in mailing_subscribers_list:
        await bot.send_message(user_id, message_to_mail)

    logging.info(f'Сообщение было отправлено: {mailing_subscribers_list}. Текст сообщения: "{message_to_mail}"')

    await query.message.delete()
    await query.message.answer(f'Сообщение отправлено: {mailing_subscribers_list}')

    await state.clear()


# нажата '❌ Нет' в подтверждении
@router.callback_query(F.data == 'btn_confirm_no', States.waiting_for_confirmation)
async def btn_confirm_no_pressed(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await query.message.answer('Операция отменена.')
    await state.clear()
