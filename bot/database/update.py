from GradeInfo import *
from WorkInfo import *
from database import make_sql_query
from database.get import get_user_login
from logger import logging


# конфигурация логгинга
logging = logging.getLogger(__name__)


def update_user(user_id: int, login: str, password: str, notification_subscribe: bool = True, term: int = 1,
                max_term: int = 8) -> None:
    r"""Adds user into database; if 'user_id' is already in database, only updates login and password,
    keeping 'user_id' and 'notifications' the same.

    :param max_term: last user term
    :param term: current user's term that user picked
    :param user_id: user's telegram ID (not tag)
    :param login: user's login on omgtu site
    :param password: user's password on omgtu site (preferably encrypted)
    :param notification_subscribe: defines if user will get notifications about work status and grades changes"""
    make_sql_query('INSERT INTO user_info(tg_id, login, password, notifications, term, max_term) '
                   'VALUES (%s, %s, %s, %s, %s, %s) '
                   'ON DUPLICATE KEY UPDATE login = %s, password = %s, notifications = %s, term = %s, max_term = %s',
                   (user_id, login, password, notification_subscribe, term, max_term,
                    login, password, notification_subscribe, term, max_term))


def update_student_works(works: list[WorkInfo], login: str) -> None:
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


def update_user_notification_subscribe(user_id: int, notification_subscribe: bool) -> None:
    r"""Changes database info about notification subsсription for user"""
    make_sql_query('UPDATE user_info SET notifications = %s WHERE tg_id = %s',
                   (notification_subscribe, user_id))


def update_user_term(user_id: int, term: int) -> None:
    make_sql_query('UPDATE user_info SET term = %s WHERE tg_id = %s', (term, user_id))


def update_user_max_term(user_id: int, term: int) -> None:
    make_sql_query('UPDATE user_info SET max_term = %s WHERE tg_id = %s', (term, user_id))


def update_student_grades(grades_info: list[GradeInfo], login: str = None, user_id: int = None) -> None:
    r"""At least one parameter should be given. Most optimal way is to give 'login' variable.
    If both are given, only 'login' is used. Updates already existing works in database. If work doesn't exist,
    adds new work"""
    if login is None and user_id is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ValueError(error_msg)

    if login is None:
        login = get_user_login(user_id)

    for grade_info in grades_info:
        # удаление старой записи, если она существует
        make_sql_query('DELETE from old_grades WHERE login = %s AND subject = %s AND term = %s',
                       (login, grade_info.subject, grade_info.term))
        # создание новой записи в БД
        make_sql_query('INSERT INTO old_grades(login, subject, term, control_rating, grade_type, grade) '
                       'VALUES (%s, %s, %s, %s, %s, %s)',
                       (login, grade_info.subject, grade_info.term, grade_info.control_rating,
                        grade_info.grade_type, grade_info.grade.value))
