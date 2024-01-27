from typing import Any
from logger import logging
import pymysql


# конфигурация логгинга
logging = logging.getLogger(__name__)


def make_sql_query(query: str, params: tuple = ()) -> tuple[tuple[Any, ...], ...]:
    r"""Makes an SQL query into database.
    :return: data of SQL result

    :param query: SQL query with %s instead of variable parameters
    :param params: tuple with parameters that should be instead of %s in the exact order (tuple with one parameter
    if there's only 1 parameter)"""
    logging.debug(f'Начался выполняться запрос "{query}" с параметрами {params}')

    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='root',
            database='omgtu_bot'
        )
    except Exception as e:
        error_msg = f'Ошибка подключения к базе данных: {e}'
        logging.exception(error_msg)
        raise ConnectionError(error_msg)

    cursor = connection.cursor()

    cursor.execute(query, params)

    connection.commit()
    connection.close()

    result = cursor.fetchall()

    logging.debug(f'Результат - {result}')

    return result
