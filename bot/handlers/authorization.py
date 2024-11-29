import time
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from requests import Session

import database.delete
import database.get
import database.other
import database.update
import encryption
import html_parser.grades
import html_parser.main
import html_parser.works
import html_parser.tasks
import misc.utils
import strings
from misc.logger import logging

# рутер для подключения в основном файле
router = Router()
r"""Router for authorization button"""

# конфигурация логгинга
logging = logging.getLogger(__name__)


class States(StatesGroup):
    r"""Stores which stage of the dialogue the client is at"""
    waiting_for_login = State()
    waiting_for_password = State()
    waiting_for_change_acc_answer = State()
    waiting_for_term = State()


# нажатие кнопки "Авторизация"
@router.message(F.text == strings.START_AUTH)
async def authorization_command(message: Message, state: FSMContext):
    # если пользователь уже авторизован ###########################################
    if database.other.is_user_authorized(message.from_user.id):
        # создание клавиатуры под сообщением
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(text='✅ Да', callback_data='btn_change_account'),
                    InlineKeyboardButton(text='❌ Нет', callback_data='btn_decline_change_account'))
        builder.row(InlineKeyboardButton(text='Выход из аккаунта', callback_data='btn_logout_account'))

        await message.reply(f'Вы уже авторизованы под логином "{database.get.get_user_login(message.from_user.id)}". '
                            f'Хотите <b>изменить</b> аккаунт?', reply_markup=builder.as_markup())
        # переход в ожидание нажатия кнопки
        await state.set_state(States.waiting_for_change_acc_answer)
        return
    ################################################################################

    await message.reply('Введите логин от аккаунта ОмГТУ:')
    # ожидание ввода логина
    await state.set_state(States.waiting_for_login)


# нажата кнопка '✅ Да' при смене аккаунта
@router.callback_query(States.waiting_for_change_acc_answer, F.data == 'btn_change_account')
async def btn_change_account_pressed(query: CallbackQuery, state: FSMContext):
    await query.message.reply('Введите новый логин:')
    # ожидание ввода логина
    await state.set_state(States.waiting_for_login)


# нажата кнопка '❌ Нет' при смене аккаунта
@router.callback_query(States.waiting_for_change_acc_answer, F.data == 'btn_decline_change_account')
async def btn_decline_change_pressed(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await query.message.answer('Операция отменена')
    # выход из ожидания
    await state.clear()


# нажата кнопка 'Выход из аккаунта' при смене аккаунта
@router.callback_query(States.waiting_for_change_acc_answer, F.data == 'btn_logout_account')
async def btn_logout_account_pressed(query: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='✅ Да', callback_data='btn_logout_yes'),
                InlineKeyboardButton(text='❌ Нет', callback_data='btn_logout_no'))

    await query.message.delete()
    await query.message.answer('Вы уверены?', reply_markup=builder.as_markup())


# нажата кнопка '✅ Да' при подтверждении выхода
@router.callback_query(States.waiting_for_change_acc_answer, F.data == 'btn_logout_yes')
async def btn_logout_account_pressed(query: CallbackQuery, state: FSMContext):
    database.delete.delete_all_student_works(user_id=query.from_user.id)
    database.delete.delete_all_student_grades(user_id=query.from_user.id)
    database.delete.delete_user_account(user_id=query.from_user.id)

    await query.message.delete()
    await query.message.answer('Вы вышли из аккаунта.')

    # выход из ожидания
    await state.clear()


# нажата кнопка '❌ Нет' при подтверждении выхода
@router.callback_query(States.waiting_for_change_acc_answer, F.data == 'btn_logout_no')
async def btn_logout_account_pressed(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await query.message.answer('Операция отменена.')

    # выход из ожидания
    await state.clear()


# запрос пароля после ввода логина
@router.message(States.waiting_for_login)
async def wait_for_password(message: Message, state: FSMContext):
    await state.update_data(login=message.text)

    await message.answer('Введите пароль от аккаунта:')
    await state.set_state(States.waiting_for_password)


# запрос текущего семестра после ввода пароля
@router.message(States.waiting_for_password)
async def wait_for_term(message: Message, state: FSMContext):
    await state.update_data(password=message.text)

    await message.answer('Введите ваш текущий семестр:')
    await state.set_state(States.waiting_for_term)


# обработка логина и пароля после их ввода
@router.message(States.waiting_for_term)
async def authorization_handler(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 1:
        await message.reply('Число некорректно. Попробуйте еще раз:')
        return

    warning_data_message = await message.answer('Выполняется проверка на корректность данных. Процесс может занять '
                                                'около минуты...')
    _data = await state.get_data()

    login = _data.get('login')
    password = _data.get('password')
    selected_term = int(message.text)

    # информация в логи
    logging.info(f'Началась авторизация пользователя "{message.from_user.id}", логин - "{login}"...')
    start_time = time.time()

    # попытка зайти в аккаунт
    session = html_parser.main.authorize(login, password)

    await warning_data_message.delete()

    if session == 1:
        await message.answer('Ошибка при подключении к сайту. Попробуйте позже')
        await state.clear()
        return

    if session == 2:
        await message.answer('Данные введены некорректно. Нажмите "Авторизация" еще раз и попробуйте снова.')
        await state.clear()
        return

    # информация в логи
    end_time = time.time()
    logging.info(f'Авторизация закончилась. Затраченное время: {end_time - start_time}')

    is_user_subscribed_notifications = True
    is_user_subscribed_mailing = True
    # если пользователь уже был авторизован и меняет аккаунт, удаление старых работ и оценок из БД
    if database.other.is_user_authorized(message.from_user.id):
        database.delete.delete_all_user_information(message.from_user.id)

        # взять из БД статус подписки и не изменять его
        is_user_subscribed_notifications = database.other.is_user_subscribed_notifications(message.from_user.id)
        is_user_subscribed_mailing = database.other.is_user_subscribed_mailing(message.from_user.id)

    # кодирование пароля перед занесением в БД
    encrypted_password = encryption.encrypt(password)

    # добавление/обновление пользователя в БД
    database.update.update_user(
        user_id=message.from_user.id,
        login=login,
        password=encrypted_password,
        notification_subscribe=is_user_subscribed_notifications,
        mailing_subscribe=is_user_subscribed_mailing,
        term=selected_term,
        last_update=misc.utils.round_down_the_date(datetime.now().date())
    )

    warning_works_message = await message.answer('Успешно. Собираем информацию о работах с сайта. Процесс может '
                                                 'занять до 3 минут...')

    # добавление/обновление работ в БД
    handle_student_works(session, login)

    await warning_works_message.delete()

    warning_grades_message = await message.answer('Успешно. Собираем информацию об оценках с сайта. Процесс может '
                                                  'занять до 2 минут...')

    # добавление/обновление оценок в БД
    max_term = handle_student_grades(session, login, message.from_user.id)

    await warning_grades_message.delete()

    warning_tasks_message = await message.answer('Успешно. Собираем информацию о заданиях с сайта. Процесс может '
                                                 'занять до 2 минут...')

    # добавление/обновление заданий в БД
    handle_student_tasks(session, login)

    await warning_tasks_message.delete()

    msg = 'Успешно. При изменении статуса работ или оценок Вам придет уведомление.\n' \
        if is_user_subscribed_notifications \
        else 'Успешно. У вас выключены уведомления, поэтому уведомления не будут приходить. ' \
             'Это можно изменить в <b>настройках</b>\n'

    await message.answer(msg +
                         '\n'
                         'Можете сверить информацию, нажав на <b>"Посмотреть список работ"</b> и '
                         '<b>"Посмотреть зачетку"</b>.\n')

    session.close()

    if selected_term > max_term:
        await message.answer(f'Введенный семестр не существует (их всего {max_term}). '
                             f'Вы можете поменять это в настройках.')

    await state.clear()


def handle_student_works(session: Session, login: str) -> None:
    all_works = html_parser.works.get_student_works(session)
    database.update.update_student_works(all_works, login)


def handle_student_grades(session: Session, login: str, user_id: int) -> int:
    all_grades = html_parser.grades.get_student_grades(session)
    database.update.add_student_grades(all_grades, login)

    # из БД взять максимальное значение семестра и занести ее в user_info
    max_term = database.get.get_user_max_term(login=login, based_on_works=True)
    database.update.update_user_max_term(user_id, max_term)

    return max_term


def handle_student_tasks(session: Session, login: str) -> None:
    all_tasks = html_parser.tasks.get_student_tasks(session)
    database.update.add_student_tasks(all_tasks, login)
