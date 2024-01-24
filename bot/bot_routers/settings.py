from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

import user_functions
from logger import logging
import database

# рутер для подключения в основном файле
router = Router()
r"""Router for settings button"""


# конфигурация логгинга
logging = logging.getLogger(__name__)


class States(StatesGroup):
    r"""Stores which stage of the dialogue the client is at"""
    waiting_for_choice = State()


# нажатие кнопки "Настройки"
@router.message(F.text == 'Настройки')
async def notifications_settings_command(message: Message, state: FSMContext):
    if not database.is_user_authorized(message.from_user.id):
        await message.reply('Вы еще не авторизованы. Для начала пройдите <b>Авторизацию</b>.')
        return

    # если пользователь уже подписан на уведомления
    if database.is_user_subscribed(message.from_user.id):
        btn_switch_notif = InlineKeyboardButton(text='❌ Выключить уведомления', callback_data='btn_cancel_notif')
    else:
        btn_switch_notif = InlineKeyboardButton(text='✅ Включить уведомления', callback_data='btn_return_notif')

    btn_exit_notif_menu = InlineKeyboardButton(text='Выход', callback_data='btn_exit_notif_menu')

    builder = InlineKeyboardBuilder()
    builder.row(btn_switch_notif)
    builder.row(btn_exit_notif_menu)

    await message.reply('Выберите действие:', reply_markup=builder.as_markup(resize_keyboard=True))

    await state.set_state(States.waiting_for_choice)


# нажата кнопка '✅ Включить уведомления' в меню уведомлений
@router.callback_query(States.waiting_for_choice, F.data == 'btn_return_notif')
async def btn_return_notif_pressed(query: CallbackQuery, state: FSMContext):
    # удалить сообщение с меню
    await query.message.delete()

    warning_message = await query.message.answer('Для избежания ошибок производится обновление списка Ваших работ. '
                                                 'Подождите несколько минут...')
    # logs
    logging.info(f'Выполняется обновление работ для "{query.from_user.id}"...')

    # обновить список работ перед включением подписки
    user_functions.update_all_user_works_list(database.get_user_login(query.from_user.id))

    # включить подписку
    user_functions.change_user_notification_subscribe(query.from_user.id, True)

    await warning_message.delete()
    await query.message.answer('Уведомления включены. Начиная с <b>данного</b> момента будут отслеживаться изменения')

    # logs
    logging.info('Обновление завершено.')

    await state.clear()


# нажата кнопка '❌ Выключить уведомления' в меню уведомлений
@router.callback_query(States.waiting_for_choice, F.data == 'btn_cancel_notif')
async def btn_cancel_notif_pressed(query: CallbackQuery, state: FSMContext):
    # выключить подписку
    database.change_user_notification_subscribe(query.from_user.id, False)

    await query.message.delete()
    await query.message.answer('Уведомления больше не будут приходить.')
    # выход из ожидания
    await state.clear()


# нажата кнопка 'Выход' в меню уведомлений
@router.callback_query(States.waiting_for_choice, F.data == 'btn_exit_notif_menu')
async def btn_exit_notif_menu_pressed(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await query.message.answer('Вы вышли из меню.')
    # выход из ожидания
    await state.clear()
