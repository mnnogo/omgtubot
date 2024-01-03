import WorkInfo
import config
import database_oper
import user_functions
import html_parser
import encryption
import background
from logger import logging
import asyncio
import time
import traceback
from aiogram import Bot, types, Dispatcher, executor
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# конфигурация логгинга
logging = logging.getLogger(__name__)


bot = Bot(config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# id разработчика для уведомлений о критических ошибках
DEVELOPER_CHAT_ID = 1876123382


class States(StatesGroup):
    r"""Stores which stage of the dialogue the client is at"""
    WAIT_FOR_LOGIN = State()
    WAIT_FOR_PASSWORD = State()
    WAIT_FOR_CHANGE_ACC_ANSWER = State()
    WAIT_FOR_NOTIF_MENU_ANSWER = State()


# команда /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    msg = 'Привет!\n' \
          '\n' \
          'Этот бот создан для отслеживания обновлений статуса работ в загрузке отчетных работ на сайте ОмГТУ.\n' \
          '\n' \
          'Для начала работы нажмите кнопку <b>"Авторизация"</b>.\n' \
          'При авторизации все введенные пароли хранятся в закодированном виде.\n' \
          'Для настройки частоты или отключения уведомлений нажмите <b>"Настройка уведомлений"</b>\n' \
          '\n' \
          'При изменении статуса работы бот пришлет Вам уведомление. Проверка происходит раз в 2 часа.' \
          'Если вами была выложена новая работа, то о её появлении не придет уведомление ' \
          '(в будущем будет настраиваемо)\n' \
          '\n' \
          'В будущем возможности бота вероятно будут расширяться.\n' \
          'При возникновении ошибки пишите в ТГ.\n' \
          '\n' \
          'Исходный код: https://github.com/Mnogchik/omgtubot/tree/master\n' \
          'Telegram: t.me/Mnogo1234'

    # шаблоны кнопок на главном экране
    btn_auth = KeyboardButton('Авторизация')
    btn_works_list = KeyboardButton('Посмотреть список работ')
    btn_notif_settings = KeyboardButton('Настройка уведомлений')

    # добавление кнопок на клавиатуру
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(btn_auth)
    markup.row(btn_works_list)
    markup.row(btn_notif_settings)

    # отправка приветствия + добавление клавиатуры
    await message.reply(msg, parse_mode='HTML', reply_markup=markup)


# нажатие кнопки "Авторизация"
@dp.message_handler(lambda message: message.text == 'Авторизация')
async def authorization_command(message: types.Message):
    # если пользователь уже авторизован, спросить про смену аккаунта #########
    if database_oper.is_user_authorized(message.from_user.id):
        # создание и добавление кнопок
        btn_yes = InlineKeyboardButton('✅ Да', callback_data='btn_change_account')
        btn_no = InlineKeyboardButton('❌ Нет', callback_data='btn_decline_change_account')

        markup = InlineKeyboardMarkup(resize_keyboard=True)
        markup.row(btn_yes, btn_no)

        await message.reply(f'Вы уже авторизованы под логином "{database_oper.get_user_login(message.from_user.id)}". '
                            f'Хотите <b>изменить</b> аккаунт?', reply_markup=markup, parse_mode='HTML')
        # переход в ожидание нажатия кнопки
        await States.WAIT_FOR_CHANGE_ACC_ANSWER.set()
        return
    ################################################################################

    await message.reply('Введите логин от аккаунта:')
    # ожидание ввода логина
    await States.WAIT_FOR_LOGIN.set()


# нажата кнопка '✅ Да' при смене аккаунта
@dp.callback_query_handler(lambda c: c.data == 'btn_change_account', state=States.WAIT_FOR_CHANGE_ACC_ANSWER)
async def btn_change_account_pressed(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.reply('Введите новый логин:')
    # ожидание ввода логина
    await States.WAIT_FOR_LOGIN.set()


# нажата кнопка '❌ Нет' при смене аккаунта
@dp.callback_query_handler(lambda c: c.data == 'btn_decline_change_account', state=States.WAIT_FOR_CHANGE_ACC_ANSWER)
async def btn_decline_change_pressed(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.reply('Операция отменена')
    await state.finish()


# запрос пароля после ввода логина
@dp.message_handler(state=States.WAIT_FOR_LOGIN)
async def wait_for_password(message: types.Message, state: FSMContext) -> None:
    # сохранение логина для следующих состояний
    await state.update_data(login=message.text)

    await message.answer('Введите пароль от аккаунта:')
    # ожидание ввода пароля
    await States.WAIT_FOR_PASSWORD.set()


# обработка логина и пароля после их ввода
@dp.message_handler(state=States.WAIT_FOR_PASSWORD)
async def authorization_handler(message: types.Message, state: FSMContext) -> None:
    await message.answer('Выполняется проверка на корректность данных. Процесс может занять около минуты...')

    _data = await state.get_data()

    login = _data.get('login')
    password = message.text

    # информация в логи
    logging.info(f'Началась авторизация пользователя "{message.from_user.id}", логин - "{login}"...')
    start_time = time.time()

    # попытка зайти в аккаунт
    session = html_parser.authorize(login, password)

    if session == 1:
        await message.answer('Ошибка при подключении к сайту. Попробуйте позже')
        await state.finish()
        return

    if session == 2:
        await message.answer('Данные введены некорректно. Нажмите "Авторизация" еще раз и попробуйте снова.')
        await state.finish()
        return

    await message.answer('Успешно. Анализируем информацию с сайта. Процесс может занять около 3 минут.......')

    # если пользователь уже был авторизован и меняет аккаунт, удаление старых работ из БД
    if database_oper.is_user_authorized(message.from_user.id):
        login = database_oper.get_user_login(message.from_user.id)
        database_oper.delete_all_student_works(login)

    # кодирование пароля перед занесением в БД
    encrypted_password = encryption.encrypt(password)

    # добавление/обновление пользователя в БД
    database_oper.update_user_in_db(message.from_user.id, login, encrypted_password)
    # добавление/обновление работ в БД
    all_works = html_parser.get_new_student_works(session)
    database_oper.update_student_works_db(all_works, login)

    i = 1
    msg = 'Успешно. При изменении статуса работ Вам придет уведомление.\n' \
          '\n' \
          '<b>Список Ваших работ</b>:\n'
    for work in all_works:
        msg += f'\n{i}. {str(work)}\n'
        i += 1

    await message.answer(msg, parse_mode='HTML')

    # информация в логи
    end_time = time.time()
    logging.info(f'Авторизация закончилась. Затраченное время: {end_time - start_time}')

    await state.finish()


# нажатие кнопки "Посмотреть список работ"
@dp.message_handler(lambda message: message.text == 'Посмотреть список работ')
async def view_all_works_command(message: types.Message) -> None:
    if not database_oper.is_user_authorized(message.from_user.id):
        await message.reply('Вы еще не авторизованы. Для просмотра списка работ пройдите <b>Авторизацию</b>',
                            parse_mode='HTML')
        return

    # получение логина из БД по телеграм айди
    login = database_oper.get_user_login(message.from_user.id)

    all_works = database_oper.get_old_student_works(login)

    i = 1
    msg = '<b>Список Ваших работ:</b>\n'
    for work in all_works:
        msg += f'\n{i}. {str(work)}\n'
        i += 1

    await message.reply(msg, parse_mode='HTML')


# нажатие кнопки "Настройка уведомлений"
@dp.message_handler(lambda message: message.text == 'Настройка уведомлений')
async def notifications_settings_command(message: types.Message):
    if not database_oper.is_user_authorized(message.from_user.id):
        await message.reply('Вы еще не авторизованы. Для начала пройдите <b>Авторизацию</b>',
                            parse_mode='HTML')
        return

    btn_return_notif = InlineKeyboardButton('✅ Включить уведомления', callback_data='btn_return_notif')
    btn_cancel_notif = InlineKeyboardButton('❌ Выключить уведомления', callback_data='btn_cancel_notif')
    btn_exit_notif_menu = InlineKeyboardButton('Выход', callback_data='btn_exit_notif_menu')

    markup = InlineKeyboardMarkup(resize_keyboard=True)
    markup.row(btn_return_notif)
    markup.row(btn_cancel_notif)
    markup.row(btn_exit_notif_menu)

    await message.reply('Выберите действие:', reply_markup=markup)

    await States.WAIT_FOR_NOTIF_MENU_ANSWER.set()


# нажата кнопка '✅ Включить уведомления' в меню уведомлений
@dp.callback_query_handler(lambda c: c.data == 'btn_return_notif', state=States.WAIT_FOR_NOTIF_MENU_ANSWER)
async def btn_return_notif_pressed(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.reply('Для избежания ошибок производится обновление списка Ваших работ. '
                                       'Подождите несколько минут...')
    # занесение начало события в логи
    logging.info(f'Выполняется обновление работ для "{callback_query.from_user.id}"...')

    # обновить список работ перед включением подписки
    user_functions.update_all_user_works_list(database_oper.get_user_login(callback_query.from_user.id))

    # включить подписку
    user_functions.change_user_notification_subscribe(callback_query.from_user.id, True)

    await callback_query.message.answer('Уведомления включены. Начиная с <b>данного</b> момента '
                                        'будут отслеживаться изменения', parse_mode='HTML')

    # занесение конца события в логи
    logging.info('Обновление завершено.')

    await state.finish()


# нажата кнопка '❌ Выключить уведомления' в меню уведомлений
@dp.callback_query_handler(lambda c: c.data == 'btn_cancel_notif', state=States.WAIT_FOR_NOTIF_MENU_ANSWER)
async def btn_cancel_notif_pressed(callback_query: types.CallbackQuery, state: FSMContext):
    # выключить подписку
    database_oper.change_user_notification_subscribe(callback_query.from_user.id, False)
    await callback_query.message.reply('Уведомления больше не будут приходить.')
    await state.finish()


# нажата кнопка 'Выход' в меню уведомлений
@dp.callback_query_handler(lambda c: c.data == 'btn_exit_notif_menu', state=States.WAIT_FOR_NOTIF_MENU_ANSWER)
async def btn_exit_notif_menu_pressed(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.reply('Вы вышли из меню.')
    await state.finish()


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

            # для каждого человека из списка проверить изменения
            for user_id in senders_id_list:
                # получить логин и пароль пользователя
                login = database_oper.get_user_login(user_id)
                password = database_oper.get_user_password(login=login)

                # получить авторизованную сессию для парсинга информации
                session = html_parser.authorize(login, password)

                # получить список работ, которые изменились
                updated_works = user_functions.get_updated_student_works(login, password, session)

                # после получения работ, обновить базу со всеми работами пользователя
                database_oper.update_student_works_db(updated_works, login)

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
                               f'теперь имеет статус <b>"{works[0].status}"</b>', parse_mode='HTML')
        return

    msg = 'Следующие работы изменили статус:\n'
    i = 1
    for work in works:
        msg += f'\n{i}. Работа <b>"{work.work_name}"</b> <i>({work.subject})</i> ' \
               f'теперь имеет статус <b>"{work.status}"</b>\n'
        i += 1

    await bot.send_message(user_id, msg, parse_mode='HTML')


# обработка ошибок внутри бота
@dp.errors_handler(exception=Exception)
async def errors_handler(update: types.Update, exception: Exception):
    exception_text = traceback.format_exc()
    await notify_developer(exception_text)
    return True


# функция для уведомления разработчика о возникновении крит ошибки
async def notify_developer(exception_text: str):
    await bot.send_message(DEVELOPER_CHAT_ID, f"Возникла критическая ошибка: {exception_text}")


def run_bot():
    # предотвращение выключения бота
    background.keep_alive()

    # запуск периодической проверки на уведомления
    loop = asyncio.get_event_loop()
    loop.create_task(send_notifications_periodically())

    try:
        executor.start_polling(dp)
    except Exception as e:
        logging.exception(e)
        notify_developer(str(e))

