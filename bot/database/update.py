from datetime import datetime, date

import misc.utils
from GradeInfo import *
from WorkInfo import *
from database import make_sql_query
from database.get import get_user_login
from misc.logger import logging

# конфигурация логгинга
logging = logging.getLogger(__name__)


def update_user(user_id: int, login: str, password: str, notification_subscribe: bool = True,
                mailing_subscribe: bool = True, term: int = 1, max_term: int = 8,
                last_update: date = datetime.now().date()) -> None:
    r"""Adds user into database or updates based on user_id.

    :param last_update: last time system updated user's term. Only 31 jan or 31 july can be given (dates of updates)
    :param mailing_subscribe: defines if user will get mailings
    :param max_term: last user term
    :param term: current user's term that user picked
    :param user_id: user's telegram ID (not tag)
    :param login: user's login on omgtu site
    :param password: user's password on omgtu site (preferably encrypted)
    :param notification_subscribe: defines if user will get notifications about work status and grades changes"""
    if not misc.utils.is_update_date_correct(last_update):
        error_msg = (f'В базу данных не может быть занесена дата, отличная от 31 января и 31 июля. '
                     f'({last_update.strftime('%Y-%m-%d')})')
        logging.exception(error_msg)
        raise ValueError(error_msg)

    make_sql_query('INSERT OR REPLACE INTO user_info(user_id, login, password, notifications, mailing, term, max_term, '
                   'last_update) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ',
                   (user_id, login, password, notification_subscribe, mailing_subscribe, term, max_term, last_update))


def update_student_works(works: list[WorkInfo], login: str) -> None:
    r"""Updates works info in database. Creates new info, if work doesn't yet exist in database

    :param works: list of :class:`WorkInfo` objects with paramaters to be updated in database
    :param login: login of user whose works will be updated"""
    if len(works) == 0:
        return

    for work in works:
        # удаление старой записи, если она существует
        make_sql_query('DELETE from old_works WHERE login = ? AND work_name = ? AND subject = ?',
                       (login, work.work_name, work.subject))
        # создание новой записи работы в БД
        make_sql_query('INSERT INTO old_works(login, work_name, subject, status) '
                       'VALUES (?, ?, ?, ?)',
                       (login, work.work_name, work.subject, str(work.status.value)))


def update_user_notification_subscribe(user_id: int, notification_subscribe: bool) -> None:
    r"""Changes database info about notification subsсription for user"""
    make_sql_query('UPDATE user_info SET notifications = ? WHERE user_id = ?',
                   (notification_subscribe, user_id))


def update_user_mailing_subscribe(user_id: int, mailing_subscribe: bool) -> None:
    r"""Changes database info about mailing subsсription for user"""
    make_sql_query('UPDATE user_info SET mailing = ? WHERE user_id = ?',
                   (mailing_subscribe, user_id))


def update_user_term(user_id: int, term: int) -> None:
    make_sql_query('UPDATE user_info SET term = ? WHERE user_id = ?', (term, user_id))


def update_user_max_term(user_id: int, term: int) -> None:
    make_sql_query('UPDATE user_info SET max_term = ? WHERE user_id = ?', (term, user_id))


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
        make_sql_query('DELETE FROM old_grades WHERE login = ? AND subject = ? AND term = ?',
                       (login, grade_info.subject, grade_info.term))
        # создание новой записи в БД
        make_sql_query('INSERT INTO old_grades(login, subject, term, control_rating, grade_type, grade) '
                       'VALUES (?, ?, ?, ?, ?, ?)',
                       (login, grade_info.subject, grade_info.term, grade_info.control_rating,
                        grade_info.grade_type, grade_info.grade.value))


def update_user_last_update(user_id: int, date_to: date) -> None:
    if not misc.utils.is_update_date_correct(date_to):
        error_msg = (f'В базу данных не может быть занесена дата, отличная от 31 января и 31 июля. '
                     f'({date_to.strftime('%Y-%m-%d')})')
        logging.exception(error_msg)
        raise ValueError(error_msg)

    make_sql_query('UPDATE user_info SET last_update = ? WHERE user_id = ?', (date_to, user_id))
