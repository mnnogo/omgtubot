import WorkInfo
import database
import user_functions
import html_parser
import encryption
import background
from logger import logging
import os
import asyncio
import time
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import Message, KeyboardButton, InlineKeyboardButton, CallbackQuery, ErrorEvent
from aiogram.filters import CommandStart

# конфигурация логгинга
logging = logging.getLogger(__name__)

# создание бота
TOKEN = os.getenv('TELEGRAM_API_TOKEN')
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# разделение диспатчера на рутеры
auth_router = Router()      # аутентификация
view_router = Router()      # просмотр работ
grades_router = Router()    # зачетка с оценками
settings_router = Router()  # настройки

dp.include_routers(auth_router, view_router, grades_router, settings_router)

# id разработчика для уведомлений
DEVELOPER_CHAT_ID = os.getenv('TELEGRAM_ID')


class States(StatesGroup):
    r"""Stores which stage of the dialogue the client is at"""

    class auth(StatesGroup):
        waiting_for_login = State()
        waiting_for_password = State()
        waiting_for_change_acc_answer = State()

    class settings_menu(StatesGroup):
        waiting_for_choice = State()


# команда /start
@dp.message(CommandStart())
async def start_command(message: Message):
    msg = 'Привет! Этот бот позволяет отслеживать обновления статуса работ в загрузке отчетных работ на сайте ОмГТУ.\n' \
          '\n' \
          'Для начала работы нажмите кнопку <b>"Авторизация"</b>.\n' \
          'При авторизации все введенные пароли хранятся в закодированном виде.\n' \
          'Для настройки уведомлений нажмите <b>"Настройка уведомлений"</b>\n' \
          '\n' \
          'При изменении статуса работы бот пришлет Вам уведомление. Проверка происходит раз в 2 часа. ' \
          'Если вами была выложена новая работа, то о её появлении не придет уведомление ' \
          '(в будущем будет настраиваемо)\n' \
          '\n' \
          'При исчезновении кнопок напишите /start еще раз.\n' \
          '\n' \
          'В будущем возможности бота вероятно будут расширяться.\n' \
          'При возникновении ошибки пишите в ТГ.\n' \
          '\n' \
          'Исходный код: https://github.com/Mnogchik/omgtubot/tree/master\n' \
          'Telegram: t.me/Mnogo1234'

    # шаблоны кнопок на главном экране
    btn_auth = KeyboardButton(text='Авторизация')
    btn_works_list = KeyboardButton(text='Посмотреть список работ')
    btn_grades_list = KeyboardButton(text='Посмотреть зачетку')
    btn_notif_settings = KeyboardButton(text='Настройки')

    # добавление кнопок на клавиатуру
    builder = ReplyKeyboardBuilder()
    builder.row(btn_auth)
    builder.row(btn_works_list)
    builder.row(btn_grades_list)
    builder.row(btn_notif_settings)

    # отправка приветствия + добавление клавиатуры
    await message.reply(msg, reply_markup=builder.as_markup(resize_keyboard=True))


# нажатие кнопки "Авторизация"
@auth_router.message(F.text == 'Авторизация')
async def authorization_command(message: Message, state: FSMContext):
    # если пользователь уже авторизован ###########################################
    if database.is_user_authorized(message.from_user.id):
        # создание клавиатуры под сообщением
        btn_yes = InlineKeyboardButton(text='✅ Да', callback_data='btn_change_account')
        btn_no = InlineKeyboardButton(text='❌ Нет', callback_data='btn_decline_change_account')

        builder = InlineKeyboardBuilder()
        builder.row(btn_yes, btn_no)

        await message.reply(f'Вы уже авторизованы под логином "{database.get_user_login(message.from_user.id)}". '
                            f'Хотите <b>изменить</b> аккаунт?', reply_markup=builder.as_markup())
        # переход в ожидание нажатия кнопки
        await state.set_state(States.auth.waiting_for_change_acc_answer)
        return
    ################################################################################

    await message.reply('Введите логин от аккаунта:')
    # ожидание ввода логина
    await state.set_state(States.auth.waiting_for_login)


# нажата кнопка '✅ Да' при смене аккаунта
@auth_router.callback_query(States.auth.waiting_for_change_acc_answer, F.data == 'btn_change_account')
async def btn_change_account_pressed(query: CallbackQuery, state: FSMContext):
    await query.message.reply('Введите новый логин:')
    # ожидание ввода логина
    await state.set_state(States.auth.waiting_for_login)


# нажата кнопка '❌ Нет' при смене аккаунта
@auth_router.callback_query(States.auth.waiting_for_change_acc_answer, F.data == 'btn_decline_change_account')
async def btn_decline_change_pressed(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await query.message.answer('Операция отменена')
    # выход из ожидания
    await state.clear()


# запрос пароля после ввода логина
@auth_router.message(States.auth.waiting_for_login)
async def wait_for_password(message: Message, state: FSMContext):
    # сохранение логина для следующих состояний
    await state.update_data(login=message.text)

    await message.answer('Введите пароль от аккаунта:')
    # ожидание ввода пароля
    await state.set_state(States.auth.waiting_for_password)


# обработка логина и пароля после их ввода
@auth_router.message(States.auth.waiting_for_password)
async def authorization_handler(message: Message, state: FSMContext):
    warning_message = await message.answer('Выполняется проверка на корректность данных. Процесс может занять около '
                                           'минуты...')
    _data = await state.get_data()

    login = _data.get('login')
    password = message.text

    # информация в логи
    logging.info(f'Началась авторизация пользователя "{message.from_user.id}", логин - "{login}"...')
    start_time = time.time()

    # попытка зайти в аккаунт
    session = html_parser.authorize(login, password)

    await warning_message.delete()

    if session == 1:
        await message.answer('Ошибка при подключении к сайту. Попробуйте позже')
        await state.clear()
        return

    if session == 2:
        await message.answer('Данные введены некорректно. Нажмите "Авторизация" еще раз и попробуйте снова.')
        await state.clear()
        return

    await message.answer('Успешно. Анализируем информацию с сайта. Процесс может занять около 3 минут.......')

    # если пользователь уже был авторизован и меняет аккаунт, удаление старых работ из БД
    if database.is_user_authorized(message.from_user.id):
        login = database.get_user_login(message.from_user.id)
        database.delete_all_student_works(login)

    # кодирование пароля перед занесением в БД
    encrypted_password = encryption.encrypt(password)

    # добавление/обновление пользователя в БД
    database.update_user_in_db(message.from_user.id, login, encrypted_password)
    # добавление/обновление работ в БД
    all_works = html_parser.get_new_student_works(session)
    database.update_student_works_db(all_works, login)

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


# нажатие кнопки "Посмотреть список работ"
@view_router.message(F.text == 'Посмотреть список работ')
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


# нажатие кнопки "Посмотреть зачетку"
@grades_router.message(F.text == 'Посмотреть зачетку')
async def view_all_grades(message: Message, state: FSMContext):
    if not database.is_user_authorized(message.from_user.id):
        await message.reply('Вы еще не авторизованы. Для начала пройдите <b>Авторизацию</b>.')
        return


# нажатие кнопки "Настройки"
@settings_router.message(F.text == 'Настройки')
async def notifications_settings_command(message: Message, state: FSMContext):
    if not database.is_user_authorized(message.from_user.id):
        await message.reply('Вы еще не авторизованы. Для начала пройдите <b>Авторизацию</b>.')
        return

    # если пользователь уже подписан на уведомления или нет
    if database.is_user_subscribed(message.from_user.id):
        btn_switch_notif = InlineKeyboardButton(text='❌ Выключить уведомления', callback_data='btn_cancel_notif')
    else:
        btn_switch_notif = InlineKeyboardButton(text='✅ Включить уведомления', callback_data='btn_return_notif')

    btn_exit_notif_menu = InlineKeyboardButton(text='Выход', callback_data='btn_exit_notif_menu')

    builder = InlineKeyboardBuilder()
    builder.row(btn_switch_notif)
    builder.row(btn_exit_notif_menu)

    await message.reply('Выберите действие:', reply_markup=builder.as_markup(resize_keyboard=True))

    await state.set_state(States.settings_menu.waiting_for_choice)


# нажата кнопка '✅ Включить уведомления' в меню уведомлений
@settings_router.callback_query(States.settings_menu.waiting_for_choice, F.data == 'btn_return_notif')
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
@settings_router.callback_query(States.settings_menu.waiting_for_choice, F.data == 'btn_cancel_notif')
async def btn_cancel_notif_pressed(query: CallbackQuery, state: FSMContext):
    # выключить подписку
    database.change_user_notification_subscribe(query.from_user.id, False)

    await query.message.delete()
    await query.message.answer('Уведомления больше не будут приходить.')

    await state.clear()


# нажата кнопка 'Выход' в меню уведомлений
@settings_router.callback_query(States.settings_menu.waiting_for_choice, F.data == 'btn_exit_notif_menu')
async def btn_exit_notif_menu_pressed(query: CallbackQuery, state: FSMContext):
    await query.message.delete()
    await query.message.answer('Вы вышли из меню.')
    # выход из ожидания
    await state.clear()


# функция, отвечающая за проверку и отправку уведомлений (неоптимизирована по нагрузке, изменить при лагах)
async def send_notifications_periodically():
    while True:
        try:
            logging.info('Началась рассылка уведомлений...')

            # запоминаем затраченное время и список юзеров, которым отправили уведомление
            user_notif_info = []
            start_time = time.time()

            # список ID людей, подписанных на уведомления
            senders_id_list = user_functions.get_notification_senders_list()

            logging.debug(f'Подписаны на уведомления: {senders_id_list}')

            # для каждого человека из списка проверить изменения
            for user_id in senders_id_list:
                # получить логин и пароль пользователя
                login = database.get_user_login(user_id)
                password = database.get_user_password(user_id)

                # получить сессию с авторизованным пользователем
                session = html_parser.authorize(login, password)

                # получить список работ, которые изменились
                updated_works = user_functions.get_updated_student_works(login, password, session)

                # после получения работ, обновить базу со всеми работами пользователя
                database.update_student_works_db(updated_works, login)

                # список работ у которых ТОЛЬКО обновился статус (не их появление)
                updated_status_works = user_functions.get_updated_status_works(updated_works=updated_works)

                # если хоть одна работа изменила статус
                if len(updated_status_works) > 0:
                    await send_notification(user_id, updated_status_works)
                    user_notif_info.append(user_id)

            # конец таймера
            end_time = time.time()

            logging.info(f'Уведомление отправлено след. пользователям: {user_notif_info}. '
                         f'Затраченное время: {end_time - start_time}')
        except Exception as e:
            logging.exception(e)
            # отправка сообщения мне в ТГ, т.к. наличие ошибки будет незаметно
            await notify_developer(str(e))

        # проверка каждые 2 часа
        await asyncio.sleep(7200)


# функция для отправки уведомления
async def send_notification(user_id: int, works: list[WorkInfo]):
    if len(works) == 0:
        await bot.send_message(user_id, 'Ошибочное уведомление.')
        return

    if len(works) == 1:
        await bot.send_message(user_id,
                               f'Работа <b>"{works[0].work_name}"</b> <i>({works[0].subject})</i> '
                               f'теперь имеет статус <b>"{works[0].status}"</b>')
        return

    msg = 'Следующие работы изменили статус:\n'
    i = 1
    for work in works:
        msg += f'\n{i}. Работа <b>"{work.work_name}"</b> <i>({work.subject})</i> ' \
               f'теперь имеет статус <b>"{work.status}"</b>\n'
        i += 1

    await bot.send_message(user_id, msg)


@dp.error()
async def errors_handler(event: ErrorEvent):
    exception_text = event.format_exc()
    logging.exception(exception_text)
    await notify_developer(exception_text)
    return True


# функция для уведомления разработчика о возникновении крит. ошибки
async def notify_developer(exception_text: str):
    await bot.send_message(DEVELOPER_CHAT_ID, f"Возникла критическая ошибка: {exception_text}")


async def run_bot():
    # # предотвращение выключения бота
    # background.keep_alive()
    #
    # # запуск периодической проверки на уведомления
    # asyncio.ensure_future(send_notifications_periodically())

    try:
        logging.debug('Попытка запустить бота...')
        await dp.start_polling(bot)
    except Exception as e:
        logging.exception(e)
        await notify_developer(str(e))
