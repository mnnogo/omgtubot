from database import make_sql_query
from errors import ZeroArguementsError
from misc.logger import logging

# конфигурация логгинга
logging = logging.getLogger(__name__)


def delete_all_student_works(*, user_id: int = None, login: str = None) -> None:
    r"""Deletes all works in database that user with omgtu 'login' had in database."""
    if login is None and user_id is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ZeroArguementsError(error_msg)

    make_sql_query('DELETE FROM old_works '
                   'WHERE login IN (SELECT login FROM user_info WHERE user_id = ? OR login = ?)', (user_id, login))


def delete_all_student_grades(*, user_id: int = None, login: str = None) -> None:
    r"""Deletes all grades in database that user with omgtu 'login' had in database."""
    if login is None and user_id is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ZeroArguementsError(error_msg)

    make_sql_query('DELETE FROM old_grades '
                   'WHERE login IN (SELECT login FROM user_info WHERE user_id = ? OR login = ?)', (user_id, login))


def delete_user_account(*, user_id: int = None, login: str = None):
    if login is None and user_id is None:
        error_msg = 'Хотя бы один аргумент должен быть передан'
        logging.exception(error_msg)
        raise ZeroArguementsError(error_msg)

    make_sql_query('UPDATE user_info '
                   'SET login = NULL, password = NULL, term = NULL, max_term = NULL, last_update = NULL '
                   'WHERE user_id = ? OR login = ?', (user_id, login))
