import asyncio
import time

from aiogram.filters import CommandStart
from aiogram.types import Message, KeyboardButton, ErrorEvent
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import WorkInfo
import database
import html_parser
import misc.env
import user_functions
import database.get, database.delete, database.update, database.other
from bot_routers import authorization, view_works, grades, settings, mailing
from logger import logging

from misc.bot_init import bot, dp

# конфигурация логгинга
logging = logging.getLogger(__name__)


# подключение рутеров из файлов (разбито по каждой кнопке)
dp.include_routers(authorization.router, view_works.router, grades.router, settings.router, mailing.router)


# команда /start
@dp.message(CommandStart())
async def start_command(message: Message):
    msg = 'Привет! Этот бот позволяет отслеживать обновления статуса работ в отчетных работах и оценок на сайте ОмГТУ.\n' \
          '\n' \
          'Для начала работы нажмите кнопку <b>"Авторизация"</b>.\n' \
          'При авторизации все введенные пароли хранятся в закодированном виде.\n' \
          'Для настройки уведомлений или изменения семестра нажмите <b>"Настройки"</b>\n' \
          '\n' \
          'При изменении статуса работы или оценки за <b>текущий семестр</b> бот пришлет Вам уведомление. ' \
          'Текущий семестр указывается пользователем при авторизации. Проверка происходит раз в 2 часа. ' \
          'Если вами была удалена или выложена новая работа, то об этом не придет уведомление\n' \
          '\n' \
          'Каждые 31 января и 31 августа происходит изменение текущего семестра на +1. Семестр влияет только на ' \
          'уведомления об оценках.\n' \
          '\n' \
          '<b>При исчезновении кнопок напишите /start еще раз.</b>\n' \
          '\n' \
          'В будущем возможности бота вероятно будут расширяться.\n' \
          'При возникновении проблем пишите в ТГ.\n' \
          '\n' \
          'Исходный код: https://github.com/Mnogchik/omgtubot/tree/master\n' \
          'Telegram: t.me/Mnogo1234'

    # добавление клавиатуры
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='Авторизация'))
    builder.row(KeyboardButton(text='Посмотреть список работ'))
    builder.row(KeyboardButton(text='Посмотреть зачетку'))
    builder.row(KeyboardButton(text='Настройки'))

    # админские кнопки
    if message.from_user.id == misc.env.DEVELOPER_CHAT_ID:
        builder.row(KeyboardButton(text='Сделать рассылку'))

    # отправка приветствия + добавление основной клавиатуры
    await message.reply(text=msg, reply_markup=builder.as_markup(resize_keyboard=True))


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
                login = database.get.get_user_login(user_id)
                password = database.get.get_user_password(user_id=user_id)

                # получить сессию с авторизованным пользователем
                session = html_parser.main.authorize(login, password)

                # получить список работ, которые изменились
                updated_works = user_functions.get_updated_student_works(login, password, session)

                # после получения работ, обновить базу со всеми работами пользователя
                database.update.update_student_works(updated_works, login)

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
    await bot.send_message(misc.env.DEVELOPER_CHAT_ID, f"Возникла критическая ошибка: {exception_text}")


async def run_bot():
    # # предотвращение выключения бота
    # background.keep_alive()
    #
    # # запуск периодических уведомлений
    # asyncio.ensure_future(send_notifications_periodically())

    logging.debug('Попытка запустить бота...')

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.exception(e)
        await notify_developer(str(e))
