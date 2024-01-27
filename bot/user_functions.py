import requests

import database
import database.get
import database.update
import html_parser.grades
import html_parser.main
import html_parser.works
from GradeInfo import *
from WorkInfo import *
from logger import logging

# конфигурация логгинга
logging = logging.getLogger(__name__)


def get_notification_senders_list() -> list[int]:
    r""":return: users' telegram ID list of users, who should get notification"""
    return database.get.get_notification_subscribers_id()


def get_updated_student_works(login: str, password: str = None, session: requests.Session = None) -> list[WorkInfo]:
    r"""Function can be only used on student accounts. There is no check if session is actually viable.
    :param login: user login
    :param password: user password
    :param session: :class:`Session` object with authorized user (optional)

    :return: list of :class:`WorkInfo` objects of works that were changed since last check"""
    should_close_session = False

    updated_student_info = []

    if password is None:
        password = database.get.get_user_password(login=login)

    # если сессия не передана в функцию - создаем
    if session is None:
        should_close_session = True
        session = html_parser.main.authorize(login, password)

    # получение работ до проверки и после проверки
    old_student_info = database.get.get_student_works(login=login)
    new_student_info = html_parser.works.get_student_works(session)

    for workInfo in new_student_info:
        # если работа не изменилась - скип
        if workInfo in old_student_info:
            continue
        # иначе - добавить в список обновленных
        updated_student_info.append(workInfo)

    # закрытие сессии для избежания таймаута
    if should_close_session:
        session.close()

    return updated_student_info


def get_updated_student_works_by_comparing(
        old_works: list[WorkInfo],
        new_works: list[WorkInfo]) -> list[WorkInfo]:

    updated_student_info = []

    for workInfo in new_works:
        # если работа не изменилась - скип
        if workInfo in old_works:
            continue
        # иначе - добавить в список обновленных
        updated_student_info.append(workInfo)

    return updated_student_info


def get_updated_status_works(*, login: str = None, updated_works: list[WorkInfo] = None) -> list[WorkInfo]:
    r"""Requires at least one parameter. Gets updated works ONLY that have changed the status (new downloaded works
    excluded). By giving updated_works variable you reduce the running time of the program by about a minute.

    :param login: user student login on omgtu
    :param updated_works: ALL updated works, regardless of the status"""
    if login is None and updated_works is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ValueError(error_msg)

    if updated_works is None:
        updated_works = get_updated_student_works(login)

    # если статус работы PENDING - работа была только загружена
    return [work for work in updated_works if work.status != WorkStatus.PENDING]


def change_user_notification_subscribe(user_id: int, notification_subscribe: bool) -> None:
    r"""Changes info about notification subsсription for user"""
    database.update.update_user_notification_subscribe(user_id, notification_subscribe)


def update_all_user_works_list(login: str) -> None:
    r"""Updates ALL user works with new information"""
    updated_works = get_updated_student_works(login, database.get.get_user_password(login=login))
    database.update.update_student_works(updated_works, login)


def get_updated_student_grades(login: str, password: str = None, session: requests.Session = None) -> list[GradeInfo]:
    r"""Function can be only used on student accounts. There is no check if session is actually viable.
    :param login: user login
    :param password: user password
    :param session: :class:`Session` object with authorized user (optional)

    :return: list of :class:`GradeInfo` objects of works that were changed since last check"""
    should_close_session = False

    updated_student_info = []

    if password is None:
        password = database.get.get_user_password(login=login)

    # если сессия не передана в функцию - создаем и закрываем по окончанию
    if session is None:
        session = html_parser.main.authorize(login, password)
        should_close_session = True

    # получение оценок до проверки и после проверки
    old_student_grades = database.get.get_user_grades(login=login)
    new_student_grades = html_parser.grades.get_student_grades(session)

    for gradeInfo in new_student_grades:
        # если оцнеки не изменилась - скип
        if gradeInfo in old_student_grades:
            continue
        # иначе - добавить в список обновленных
        updated_student_info.append(gradeInfo)

    # закрытие сессии для избежания таймаута
    if should_close_session:
        session.close()

    return updated_student_info


def get_updated_student_grades_by_comparing(
        old_grades: list[GradeInfo],
        new_grades: list[GradeInfo]) -> list[GradeInfo]:

    updated_student_info = []

    for workInfo in new_grades:
        # если работа не изменилась - скип
        if workInfo in old_grades:
            continue
        # иначе - добавить в список обновленных
        updated_student_info.append(workInfo)

    return updated_student_info
