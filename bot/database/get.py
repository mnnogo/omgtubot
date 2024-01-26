import encryption
from database import make_sql_query

from GradeInfo import *
from WorkInfo import *
from logger import logging


# конфигурация логгинга
logging = logging.getLogger(__name__)


def get_student_works(login: str) -> list[WorkInfo]:
    r"""Gets all user's works from database based on login.
    :param login: user login on omgtu site

    :return: :class:`WorkInfo` list"""
    # извлечение из БД всех работ по логину
    result = make_sql_query('SELECT work_name, subject, status FROM old_works WHERE login = %s', (login,))

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

    if user_id is None:
        # попытка получить user_id по логину
        user_id = get_user_id(login)
        if user_id is None:
            error_msg = f'Пользователя с логином "{login}" нет в базе данных.'
            logging.exception(error_msg)
            raise ValueError(error_msg)

    encrypted_password = make_sql_query('SELECT password FROM user_info WHERE tg_id = %s', (user_id,))[0][0]

    return encryption.decrypt(encrypted_password)


def get_user_id(login: str) -> int | None:
    r"""Gets user telegram ID, based on his authorized login in database, if there's any; othewise None."""
    result = make_sql_query('SELECT tg_id FROM user_info WHERE login = %s', (login,))

    if len(result) == 0:
        return None

    return result[0][0]


def get_notification_subscribers_id() -> list[int]:
    r"""Gets all telegram ID of users, whose 'notification' field is 1 (True) in database_"""
    result = make_sql_query('SELECT tg_id from user_info WHERE notifications = 1', ())

    return [result[i][0] for i in range(len(result))]


def get_user_term(user_id: int) -> int:
    result = make_sql_query('SELECT term from user_info WHERE tg_id = %s', (user_id,))

    return result[0][0]


def get_user_grades(*, login: str = None, user_id: int = None, term: int = None) -> list[GradeInfo]:
    r"""At least one parameter should be given. Most optimal way is to give 'login' variable.
        If both are given, only 'login' is used. Returns empty list if works doesn't exist"""
    if login is None and user_id is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ValueError(error_msg)

    if login is None:
        login = get_user_login(user_id)

    # нужно ли выбирать по семестру или абсолютно все работы
    if term is None:
        result = make_sql_query('SELECT subject, term, grade from old_grades WHERE login = %s', (login, ))
    else:
        result = make_sql_query('SELECT subject, term, grade from old_grades WHERE login = %s AND term = %s',
                                (login, term))

    user_grades = []

    for subject, term, grade in result:
        user_grades.append(GradeInfo(subject, term, Grade(grade)))

    return user_grades


def get_users_list() -> list[int]:
    result_tuples = make_sql_query('SELECT tg_id from user_info')

    result = []

    for _tuple in result_tuples:
        result.append(_tuple[0])

    return result
