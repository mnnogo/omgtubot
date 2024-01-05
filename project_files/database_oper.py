from logger import logging
import pymysql
import encryption
from WorkInfo import *

# конфигурация логгинга
logging = logging.getLogger(__name__)


def make_sql_query(query: str, params: tuple):
    r"""Makes an SQL query into database.
    :return: data of SQL result

    :param query: SQL query with %s instead of variable parameters
    :param params: tuple with parameters that should be instead of %s in the exact order (empty tuple if there's no
                   variable parameters)"""
    try:
        connection = pymysql.connect(
            host='db',
            user='root',
            password='root',
            database='omgtu_bot'
        )
    except:
        error_msg = "Ошибка подключения к базе данных"
        logging.exception(error_msg)
        raise ConnectionError(error_msg)

    cursor = connection.cursor()

    cursor.execute(query, params)

    connection.commit()
    connection.close()

    return cursor.fetchall()


def update_user_in_db(user_id: int, login: str, password: str, notification_subscribe: bool = True) -> None:
    r"""Adds user into database; if 'user_id' is already in database, only updates login and password,
    keeping 'user_id' and 'notifications' the same.

    :param user_id: user's telegram ID (not tag)
    :param login: user's login on omgtu site
    :param password: user's password on omgtu site (preferably encrypted)
    :param notification_subscribe: defines if user will get notifications about work status changes"""
    make_sql_query('INSERT INTO user_info(tg_id, login, password, notifications) VALUES (%s, %s, %s, %s)'
                   'ON DUPLICATE KEY UPDATE login = %s, password = %s',
                   (user_id, login, password, notification_subscribe,
                    login, password))


def change_user_notification_subscribe(user_id: int, notification_subscribe: bool) -> None:
    r"""Changes database info about notification subsсription for user"""
    make_sql_query('UPDATE user_info SET notifications = %s WHERE tg_id = %s', (notification_subscribe, user_id))


def get_old_student_works(login: str) -> list[WorkInfo]:
    r"""Gets all user's works from database based on login.
    :param login: user login on omgtu site

    :return: :class:`WorkInfo` list"""
    # извлечение из БД всех работ по логину
    result = make_sql_query('SELECT work_name, subject, status FROM old_works WHERE login = %s', (login,))

    old_student_works = []

    # перебор по каждой работе
    for work_name, subject, status in result:
        old_student_works.append(WorkInfo(work_name, subject, WorkStatus(int(status))))

    return old_student_works


def update_student_works_db(works: list[WorkInfo], login: str) -> None:
    r"""Updates works info in database. Creates new info, if work doesn't yet exist in database

    :param works: list of :class:`WorkInfo` objects with paramaters to be updated in database
    :param login: login of user whose works will be updated"""
    if len(works) == 0:
        return

    for work in works:
        # удаление старой записи, если она существует
        make_sql_query('DELETE from old_works WHERE login = %s AND work_name = %s AND subject = %s',
                       (login, work.work_name, work.subject))
        # создание новой записи работы в БД
        make_sql_query('INSERT INTO old_works(login, work_name, subject, status) '
                       'VALUES (%s, %s, %s, %s)',
                       (login, work.work_name, work.subject, str(work.status.value)))


def is_user_authorized(user_id: int) -> bool:
    r"""Checks if user with 'user_id' has login in database. It also returns False if there's no works added into DB"""
    user_encounters = make_sql_query('SELECT COUNT(*) FROM user_info WHERE tg_id = %s', (user_id,))[0][0]

    return user_encounters != 0


def get_user_login(user_id: int) -> str | None:
    r"""Gets authorized login of user with 'user_id' telegram ID

    :return: login, if user is in database; otherwise None."""
    result = make_sql_query('SELECT login FROM user_info WHERE tg_id = %s', (user_id,))

    if len(result) == 0:
        return None

    return result[0][0]


def get_user_password(user_id: int = None, login: str = None) -> str:
    r"""At least one parameter should be given. If both are given, only 'user_id' is used.
    :return: REAL user's password from omgtu account."""
    if user_id is None and login is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ValueError(error_msg)

    if user_id is None:
        # попытка получить user_id по логину
        user_id = get_user_id(login)
        if user_id is None:
            error_msg = f'Пользователя с логином {login} нет в базе данных.'
            logging.exception(error_msg)
            raise ValueError(error_msg)

    encrypted_password = make_sql_query('SELECT password FROM user_info WHERE tg_id = %s', (user_id, ))[0][0]

    return encryption.decrypt(encrypted_password)


def get_user_id(login: str) -> int | None:
    r"""Gets user telegram ID, based on his authorized login in database, if there's any; othewise None."""
    result = make_sql_query('SELECT tg_id FROM user_info WHERE login = %s', (login,))

    if len(result) == 0:
        return None

    return result[0][0]


def delete_all_student_works(login: str) -> None:
    r"""Deletes all works in database that user with omgtu 'login' had in database."""
    make_sql_query('DELETE FROM old_works WHERE login = %s', (login,))


def get_id_notification_subscribers() -> list[int]:
    r"""Gets all telegram ID of users, whose 'notification' field is 1 (True) in database"""
    result = make_sql_query('SELECT tg_id from user_info WHERE notifications = 1', ())

    return [result[i][0] for i in range(len(result))]
