from typing import Any, List
from misc.logger import logging
import sqlite3

# конфигурация логгинга
logging = logging.getLogger(__name__)


def make_sql_query(query: str, params: tuple = ()) -> list[Any]:
    r"""Makes an SQL query into database.
    :return: data of SQL result

    :param query: SQL query with ? instead of variable parameters
    :param params: tuple with parameters that should be instead of ? in the exact order (tuple with one parameter
    if there's only 1 parameter)"""
    logging.debug(f'Начался выполняться запрос "{query}" с параметрами {params}')
    try:
        connection = sqlite3.connect('/data/vkurse.db')
    except Exception as e:
        error_msg = f'Ошибка подключения к базе данных: {e}'
        logging.exception(error_msg)
        raise ConnectionError(error_msg)

    cursor = connection.cursor()

    cursor.execute(query, params)

    connection.commit()

    result = cursor.fetchall()

    logging.debug(f'Результат - {result}')

    return result
