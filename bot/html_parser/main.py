import time

import requests
import urllib3
from logger import logging


# конфигурация логгинга
logging = logging.getLogger(__name__)


# возможность работы без SSL сертификата
urllib3.disable_warnings()


def authorize(login: str, password: str) -> requests.Session | int:
    r""":return: :class:`Session` object with authorized user, or 1 - if there's connection error,
    2 - if there's mistake in login or password"""
    start_time = time.time()
    logging.debug(f'Начался вход пользователя "{login}"')

    # ссылка на авторизацию пользователя
    login_url = 'https://www.omgtu.ru/ecab/index.php?login=yes'

    # данные в POST request
    payload = {
        'backurl': '/ecab/index.php',
        'AUTH_FORM': 'Y',
        'TYPE': 'AUTH',
        'USER_LOGIN': login,
        'USER_PASSWORD': password
    }

    # выполнение POST запроса на авторизацию
    with requests.session() as session:
        response = session.post(login_url, data=payload, verify=False)

        if response.status_code != 200:
            logging.exception(f'Ошибка выполнения POST запроса на сайт {login_url}')
            return 1

        # строка есть на сайте, только если вход был выполнен
        if 'Вы зарегистрированы в электронном кабинете как' not in response.text:
            return 2

        end_time = time.time()
        logging.debug(f'Завершено за время {end_time - start_time}.')

        return session
