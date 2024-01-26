import time
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
import database.get, database.delete, database.update, database.other
import encryption
import html_parser.main, html_parser.works
from logger import logging


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


# нажатие кнопки "Авторизация"
@router.message(F.text == 'Авторизация')
async def authorization_command(message: Message, state: FSMContext):
    # если пользователь уже авторизован ###########################################
    if database.other.is_user_authorized(message.from_user.id):
        # создание клавиатуры под сообщением
        btn_yes = InlineKeyboardButton(text='✅ Да', callback_data='btn_change_account')
        btn_no = InlineKeyboardButton(text='❌ Нет', callback_data='btn_decline_change_account')

        builder = InlineKeyboardBuilder()
        builder.row(btn_yes, btn_no)

        await message.reply(f'Вы уже авторизованы под логином "{database.get.get_user_login(message.from_user.id)}". '
                            f'Хотите <b>изменить</b> аккаунт?', reply_markup=builder.as_markup())
        # переход в ожидание нажатия кнопки
        await state.set_state(States.waiting_for_change_acc_answer)
        return
    ################################################################################

    await message.reply('Введите логин от аккаунта:')
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


# запрос пароля после ввода логина
@router.message(States.waiting_for_login)
async def wait_for_password(message: Message, state: FSMContext):
    # сохранение логина для следующих состояний
    await state.update_data(login=message.text)

    await message.answer('Введите пароль от аккаунта:')
    # ожидание ввода пароля
    await state.set_state(States.waiting_for_password)


# обработка логина и пароля после их ввода
@router.message(States.waiting_for_password)
async def authorization_handler(message: Message, state: FSMContext):
    warning_data_message = await message.answer('Выполняется проверка на корректность данных. Процесс может занять '
                                                'около минуты...')
    _data = await state.get_data()

    login = _data.get('login')
    password = message.text

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

    # если пользователь уже был авторизован и меняет аккаунт, удаление старых работ из БД
    if database.other.is_user_authorized(message.from_user.id):
        login = database.get.get_user_login(message.from_user.id)
        database.delete.delete_all_student_works(login)

    # кодирование пароля перед занесением в БД
    encrypted_password = encryption.encrypt(password)

    # добавление/обновление пользователя в БД
    database.update.update_user(message.from_user.id, login, encrypted_password)

    warning_works_message = await message.answer('Успешно. Собираем информацию о работах с сайта. Процесс может '
                                                 'занять около 3 минут.......')

    # добавление/обновление работ в БД
    all_works = html_parser.works.get_student_works(session)
    database.update.update_student_works(all_works, login)

    await warning_works_message.delete()

    warning_grades_message = await message.answer('Успешно. Собираем информацию об оценках с сайта. Процесс может '
                                                  'занять около (?)')
    # TODO

    i = 1
    msg = 'Успешно. При изменении статуса работ Вам придет уведомление.\n' \
          '\n' \
          '<b>Список Ваших работ</b>:\n'
    for work in all_works:
        msg += f'\n{i}. {str(work)}\n'
        i += 1

    await message.answer(msg)

    # информация в логи
    end_time = time.time()
    logging.info(f'Авторизация закончилась. Затраченное время: {end_time - start_time}')

    await state.clear()
