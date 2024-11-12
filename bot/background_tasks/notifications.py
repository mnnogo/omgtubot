import asyncio
import time
import html_parser.grades
import html_parser.main
import html_parser.works
import user_functions
from GradeInfo import GradeInfo
from WorkInfo import WorkInfo
from bot_init import bot
from handlers import errors_handler
from misc.logger import logging
import database.delete
import database.get
import database.other
import database.update
import misc.utils

# конфигурация логгинга
logging = logging.getLogger(__name__)


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
                database.delete.delete_all_student_works(
                    login=login)  # удалить все работы на случай удаления работы с сайта (это никак не отслеживается)
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
                database.delete.delete_all_student_grades(login=login)
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
            await errors_handler.notify_developer(str(e))

        # проверка каждые 2 часа
        await asyncio.sleep(7200)


async def send_works_notification(user_id: int, works_to_send: list[WorkInfo]):
    if len(works_to_send) == 0:
        await bot.send_message(user_id, 'Ошибочное уведомление.')
        return

    if len(works_to_send) == 1:
        msg = 'Работа изменила статус:\n\n'
        await bot.send_message(user_id,
                               msg + misc.utils.format_work_message(works_to_send[0]))
        return

    msg = 'Работы изменили статус:\n'
    i = 1
    for work in works_to_send:
        if i % 30 == 0:  # не больше 30 работ в сообщении
            await bot.send_message(user_id, msg)
            msg = ''

        msg += f'\n{i}. {misc.utils.format_work_message(work)}\n'
        i += 1

    await bot.send_message(user_id, msg)


async def send_grades_notification(user_id: int, grades_to_send: list[GradeInfo]):
    if len(grades_to_send) == 0:
        await bot.send_message(user_id, 'Ошибочное уведомление.')
        return

    if len(grades_to_send) == 1:
        await bot.send_message(user_id,
                               f'Новая информация о предмете:\n'
                               f'{misc.utils.format_grade_message(grades_to_send[0])}')
        return

    msg = 'Новая информация о предметах:\n'
    i = 1
    for grade in grades_to_send:
        if i % 20 == 0:  # не больше 20 оценок в сообщении
            await bot.send_message(user_id, msg)
            msg = ''

        msg += f'\n{misc.utils.format_grade_message(grade)}\n'
        i += 1

    await bot.send_message(user_id, msg)
