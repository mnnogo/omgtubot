from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import misc.constants
import user_functions
from logger import logging
import database.get, database.update, database.delete, database.other


# рутер для подключения в основном файле
router = Router()
r"""Router for settings button"""


# конфигурация логгинга
logging = logging.getLogger(__name__)


class States(StatesGroup):
    r"""Stores which stage of the dialogue the client is at"""
    waiting_for_term = State()


# нажатие кнопки "Настройки"
@router.message(F.text == 'Настройки')
async def notifications_settings_command(message: Message):
    if not database.other.is_user_authorized(message.from_user.id):
        await message.reply('Вы еще не авторизованы. Для начала пройдите <b>Авторизацию</b>.')
        return

    is_user_subscribed = database.other.is_user_subscribed(message.from_user.id)

    # если пользователь уже подписан на уведомления
    if is_user_subscribed:
        btn_switch_notif = InlineKeyboardButton(text='❌ Выключить уведомления', callback_data='btn_cancel_notif')
    else:
        btn_switch_notif = InlineKeyboardButton(text='✅ Включить уведомления', callback_data='btn_return_notif')

    btn_change_term = InlineKeyboardButton(text='📝 Изменить семестр', callback_data='btn_change_term')
    btn_exit_notif_menu = InlineKeyboardButton(text='Выход', callback_data='btn_exit_notif_menu')

    builder = InlineKeyboardBuilder()
    builder.row(btn_switch_notif)
    builder.row(btn_change_term)
    builder.row(btn_exit_notif_menu)

    info_msg = '<b>Настройки:</b>\n'
    info_msg += f'Уведомления - <i>{'Включены' if is_user_subscribed else 'Выключены'}</i>\n'
    info_msg += f'Семестр - <i>{database.get.get_user_term(message.from_user.id)}</i>'

    await message.reply(text=info_msg, reply_markup=builder.as_markup(resize_keyboard=True))


# нажата кнопка '✅ Включить уведомления'
@router.callback_query(F.data == 'btn_return_notif')
async def btn_return_notif_pressed(query: CallbackQuery):
    # удалить сообщение с меню
    await query.message.delete()

    warning_message = await query.message.answer('Для избежания ошибок производится обновление списка Ваших работ. '
                                                 'Подождите несколько минут...')
    # logs
    logging.info(f'Выполняется обновление работ для "{query.from_user.id}"...')

    # обновить список работ перед включением подписки
    user_functions.update_all_user_works_list(database.get.get_user_login(query.from_user.id))

    # включить подписку
    user_functions.change_user_notification_subscribe(query.from_user.id, True)

    await warning_message.delete()
    await query.message.answer('Уведомления включены. Начиная с <b>данного</b> момента будут отслеживаться изменения')

    # logs
    logging.info('Обновление завершено.')


# нажата кнопка '❌ Выключить уведомления'
@router.callback_query(F.data == 'btn_cancel_notif')
async def btn_cancel_notif_pressed(query: CallbackQuery):
    # выключить подписку
    database.update.update_user_notification_subscribe(query.from_user.id, False)

    await query.message.delete()
    await query.message.answer('Уведомления больше не будут приходить.')


# нажата кнопка '📝 Изменить семестр'
@router.callback_query(F.data == 'btn_change_term')
async def btn_change_term_pressed(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await query.message.answer(text='Введите новое значение:\n'
                                    '<i>(значение семестра автоматически вырастает на единицу 31 января '
                                    'и 31 августа)</i>')
    await state.set_state(States.waiting_for_term)


# введено число нового семестра
@router.message(States.waiting_for_term)
async def new_term_sent(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 1 or int(message.text) > misc.constants.TERM_COUNT:
        await message.reply(text='Некорректное число. Попробуйте еще раз:')
        return

    input_term = int(message.text)

    database.update.update_user_term(user_id=message.from_user.id, term=input_term)

    await message.reply(text='Текущий семестр успешно обновлен.')
    await state.clear()


# нажата кнопка 'Выход'
@router.callback_query(F.data == 'btn_exit_notif_menu')
async def btn_exit_notif_menu_pressed(query: CallbackQuery):
    await query.message.delete()
    await query.message.answer('Вы вышли из меню.')
