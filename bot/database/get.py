from datetime import date

import encryption
from database import make_sql_query

from GradeInfo import *
from WorkInfo import *
from misc.logger import logging

# конфигурация логгинга
logging = logging.getLogger(__name__)


def get_student_works(*, login: str = None, user_id: int = None) -> list[WorkInfo]:
    r"""At least one parameter should be given.
    If both are given, only 'login' is used. Returns empty list if works doesn't exist"""
    if login is None and user_id is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ValueError(error_msg)

    # извлечение из БД всех работ (при None не ломается)
    result = make_sql_query('SELECT work_name, subject, status FROM old_works JOIN user_info '
                            'ON old_works.login = user_info.login '
                            'WHERE user_info.login = %s OR user_info.tg_id = %s', (login, user_id))

    student_works = []

    # перебор по каждой работе
    for work_name, subject, status in result:
        student_works.append(WorkInfo(work_name, subject, WorkStatus(int(status))))

    return student_works


def get_user_login(user_id: int) -> str | None:
    r"""Gets authorized login of user with 'user_id' telegram ID

    :return: login, if user is in database; otherwise None."""
    result = make_sql_query('SELECT login FROM user_info WHERE tg_id = %s', (user_id,))

    if len(result) == 0:
        return None

    return result[0][0]


def get_user_password(*, user_id: int = None, login: str = None) -> str:
    r"""At least one parameter should be given. Most optimal way is to give 'user_id' variable.
    If both are given, only 'user_id' is used.
    :return: REAL user's password from omgtu account."""
    if user_id is None and login is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ValueError(error_msg)

    result = make_sql_query('SELECT password FROM user_info WHERE tg_id = %s OR login = %s',
                            (user_id, login))

    if len(result) == 0:
        error_msg = f'Пользователя {login or user_id} нет в базе данных'
        logging.exception(error_msg)
        raise ValueError(error_msg)

    encrypted_password = result[0][0]

    return encryption.decrypt(encrypted_password)


def get_user_id(login: str) -> int | None:
    r"""Gets user telegram ID, based on his authorized login in database, if there's any; othewise None."""
    result = make_sql_query('SELECT tg_id FROM user_info WHERE login = %s', (login,))

    if len(result) == 0:
        return None

    return result[0][0]


def get_notification_subscribers_id() -> list[int]:
    r"""Gets all telegram ID of users, whose 'notification' field is 1 (True) in database"""
    result = make_sql_query('SELECT tg_id FROM user_info WHERE notifications = 1')

    return [result[i][0] for i in range(len(result))]


def get_mailing_subscribers_id() -> list[int]:
    r"""Gets all telegram ID of users, whose 'mailing' field is 1 (True) in database"""
    result = make_sql_query('SELECT tg_id FROM user_info WHERE mailing = 1')

    return [result[i][0] for i in range(len(result))]


def get_user_term(*, user_id: int = None, login: str = None) -> int:
    if user_id is None and login is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ValueError(error_msg)

    result = make_sql_query('SELECT term FROM user_info WHERE tg_id = %s OR login = %s', (user_id, login))

    return result[0][0]


def get_user_last_update(user_id: int) -> date:
    result = make_sql_query('SELECT last_update FROM user_info WHERE tg_id = %s', (user_id,))

    return result[0][0]


def get_user_max_term(*, user_id: int = None, login: str = None, based_on_works: bool = False) -> int:
    r"""
    :param login: omgtu login
    :param user_id: telegram user id
    :param based_on_works: set it to True if max_term in table user_info is still not set to correct value. Then it will check max term of all grades in old_grade table
    """
    if user_id is None and login is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ValueError(error_msg)

    if user_id is None and not based_on_works:
        user_id = get_user_id(login)

    if login is None and based_on_works:
        login = get_user_login(user_id)

    if based_on_works:
        result = make_sql_query('SELECT MAX(term) FROM old_grades WHERE login = %s', (login,))
    else:
        result = make_sql_query('SELECT max_term FROM user_info WHERE tg_id = %s', (user_id,))

    return result[0][0]


def get_user_grades(*, login: str = None, user_id: int = None, term: int = None) -> list[GradeInfo]:
    r"""At least one parameter should be given. Returns empty list if works doesn't exist"""
    if login is None and user_id is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ValueError(error_msg)

    # нужно ли выбирать по семестру или абсолютно все работы
    if term is None:
        result = make_sql_query(
            'SELECT subject, old_grades.term, control_rating, grade_type, grade FROM old_grades JOIN user_info '
            'ON old_grades.login = user_info.login WHERE user_info.login = %s OR user_info.tg_id = %s',
            (login, user_id)
        )
    else:
        result = make_sql_query(
            'SELECT subject, old_grades.term, control_rating, grade_type, grade FROM old_grades JOIN user_info '
            'ON old_grades.login = user_info.login WHERE (user_info.login = %s OR user_info.tg_id = %s) '
            'AND old_grades.term = %s',
            (login, user_id, term)
        )

    user_grades = []

    for subject, term, control_rating, grade_type, grade in result:
        user_grades.append(GradeInfo(subject, term, control_rating, grade_type, Grade(grade)))

    return user_grades


def get_users_list() -> list[int]:
    result_tuples = make_sql_query('SELECT tg_id FROM user_info')

    result = []

    for _tuple in result_tuples:
        result.append(_tuple[0])

    return result


def get_users_to_update_term() -> list[int]:
    r"""Gets users whose term > max_term"""
    # term превышает max_term на 1 в последний апдейт юзера, иначе надо обновлять
    result_tuples = make_sql_query('SELECT tg_id FROM user_info WHERE max_term >= term')

    result = []

    for _tuple in result_tuples:
        result.append(_tuple[0])

    return result
