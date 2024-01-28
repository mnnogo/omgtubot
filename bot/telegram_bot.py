import asyncio
import time

from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ErrorEvent

import WorkInfo
import background
import database
import database.delete
import database.get
import database.other
import database.update
import html_parser
import keyboards.main
import misc.env
import misc.utils
import user_functions
from GradeInfo import *
from bot_routers import authorization, works, grades, settings, mailing, fixkeyboard
from logger import logging
from misc.bot_init import bot, dp

# конфигурация логгинга
logging = logging.getLogger(__name__)


# подключение рутеров из файлов (разбито по каждой команде и кнопке)
dp.include_routers(
    authorization.router, works.router, grades.router, settings.router, mailing.router, fixkeyboard.router
)


# команда /start
@dp.message(CommandStart())
async def start_command(message: Message):
    msg = 'Привет! Этот бот позволяет отслеживать обновления статуса работ в отчетных работах и оценок на сайте ОмГТУ.\n' \
          '\n' \
          'Для начала работы нажмите <b>"Авторизация"</b>.\n' \
          'При авторизации все введенные пароли хранятся в закодированном виде.\n' \
          'Для настройки уведомлений, изменения семестра и т.д. нажмите <b>"Настройки"</b>\n' \
          '\n' \
          'При изменении статуса работы или оценки за <b>текущий семестр</b> бот пришлет Вам уведомление. ' \
          'Текущий семестр указывается пользователем при авторизации. Проверка происходит раз в 2 часа. ' \
          'Если вами была удалена или выложена новая работа, то об этом не придет уведомление\n' \
          '\n' \
          'Каждые 31 января и 31 августа происходит изменение текущего семестра на +1. Семестр влияет только на ' \
          'уведомления об оценках.\n' \
          '\n' \
          'В будущем возможности бота вероятно будут расширяться.\n' \
          'При возникновении проблем пишите в ТГ.\n' \
          '\n' \
          'Исходный код: https://github.com/Mnogchik/omgtubot/tree/master\n' \
          'Telegram: t.me/Mnogo1234'

    # отправка приветствия + добавление основной клавиатуры
    await message.reply(text=msg, reply_markup=keyboards.main.get_main_keyboard(message.from_user.id))


@dp.message(Command('fixkeyboard'))
async def update_keyboard_command(message: Message):
    await message.reply('Клавиатура исправлена.', reply_markup=keyboards.main.get_main_keyboard(message.from_user.id))


# функция, отвечающая за проверку и отправку уведомлений (неоптимизирована по нагрузке, изменить при лагах)
async def send_notifications_periodically():
    while True:
        try:
            logging.info('Началась рассылка уведомлений...')

            # запоминаем затраченное время и список юзеров, которым отправили уведомление
            user_notif_info = set()
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

                # получение старых работ из БД и новых с сайта
                old_student_works = database.get.get_student_works(login=login)
                new_student_works = html_parser.works.get_student_works(session)

                # измененные работы
                updated_works = user_functions.get_updated_student_works_by_comparing(
                    old_student_works, new_student_works
                )

                # после получения работ, обновить базу со всеми работами пользователя
                database.delete.delete_all_student_works(login)  # удалить все работы на случай удаления работы с сайта (это никак не отслеживается)
                database.update.update_student_works(new_student_works, login)  # заполнить новой информацией с нуля

                # список работ у которых ТОЛЬКО обновился статус (не их появление)
                updated_status_works = user_functions.get_updated_status_works(updated_works=updated_works)

                # если хоть одна работа изменила статус
                if len(updated_status_works) > 0:
                    await send_works_notification(user_id, updated_status_works)
                    user_notif_info.add(user_id)

                # получение старых оценок из БД и новых с сайта
                old_student_grades = database.get.get_user_grades(login=login)
                new_student_grades = html_parser.grades.get_student_grades(session)

                # измененные оценки
                updated_grades = user_functions.get_updated_student_grades_by_comparing(
                    old_student_grades, new_student_grades
                )

                # после получения оценок, обновить базу со всеми оценками пользователя
                database.delete.delete_all_student_grades(login)
                database.update.update_student_grades(new_student_grades, login)

                if len(updated_grades) > 0:
                    await send_grades_notification(user_id, updated_grades)
                    user_notif_info.add(user_id)

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


async def send_works_notification(user_id: int, works: list[WorkInfo]):
    if len(works) == 0:
        await bot.send_message(user_id, 'Ошибочное уведомление.')
        return

    if len(works) == 1:
        msg = 'Работа изменила статус:\n\n'
        await bot.send_message(user_id,
                               msg + misc.utils.format_work_message(works[0]))
        return

    msg = 'Работы изменили статус:\n'
    i = 1
    for work in works:
        if i % 30 == 0:  # не больше 20 работ в сообщении
            await bot.send_message(user_id, msg)
            msg = ''

        msg += f'\n{i}. {misc.utils.format_work_message(work)}\n'
        i += 1

    await bot.send_message(user_id, msg)


async def send_grades_notification(user_id: int, grades: list[GradeInfo]):
    if len(grades) == 0:
        await bot.send_message(user_id, 'Ошибочное уведомление.')
        return

    if len(grades) == 1:
        await bot.send_message(user_id,
                               f'Новая информация о предмете:\n'
                               f'{misc.utils.format_grade_message(grades[0])}')
        return

    msg = 'Новая информация о предметах:\n'
    i = 1
    for grade in grades:
        if i % 20 == 0:  # не больше 20 оценок в сообщении
            await bot.send_message(user_id, msg)
            msg = ''

        msg += f'\n{misc.utils.format_grade_message(grade)}\n'
        i += 1

    # отправить сообщение в пределах лимита символов
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
    # предотвращение выключения бота
    background.keep_alive()

    # запуск периодических уведомлений
    # asyncio.ensure_future(send_notifications_periodically())

    logging.debug('Попытка запустить бота...')

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.exception(e)
        await notify_developer(str(e))
