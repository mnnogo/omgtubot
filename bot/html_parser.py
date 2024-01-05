import re
import requests
import urllib3
from bs4 import BeautifulSoup
from WorkInfo import *
from logger import logging

# конфигурация логгинга
logging = logging.getLogger(__name__)

# возможность работы без SSL сертификата
urllib3.disable_warnings()


def authorize(login: str, password: str) -> requests.Session | int:
    r""":return: :class:`Session` object with authorized user, or 1 - if there's connection error,
    2 - if there's mistake in login or password"""
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

        return session


def get_new_student_works(session: requests.Session) -> list[WorkInfo]:
    r"""Returns :class:`WorkInfo` list of ALL current works from site

    :param session: :class:`Session` object with authorized user"""
    new_student_works = []

    # ссылка на GET запрос ко всем работам
    data_url = 'https://www.omgtu.ru/ecab/modules/vkr2/otherlist.php'

    response = session.get(data_url, verify=False)
    if response.status_code != 200:
        error_msg = 'Ошибка соединения с сайтом'
        logging.exception(error_msg)
        raise ConnectionError(error_msg)

    soup = BeautifulSoup(response.content, 'html.parser')

    # элементы с полной информацией о каждой работе
    works_elements = soup.find_all('tr', class_='altr')

    for works_element in works_elements:
        # 0 элемент - дата работы - скип
        work_name_and_subject = works_element.find_all('td', class_='altd', limit=2)[1].text
        # убрать повторяющиеся пробельные символы + пробелы в начале и конце
        work_name_and_subject = re.sub(r'\s+', ' ', work_name_and_subject)[1:-1]

        # вся строка после номера работы, убрать статус в конце, если есть
        work_name = re.findall(r'№ \d{7}\s(.*)', work_name_and_subject)[0]
        work_name = re.sub(r' Статус:.+', '', work_name)

        # убрать все начиная с №
        subject = re.sub(r' № \d{7}.*', '', work_name_and_subject)
        # 'работа отклонена', 'работа принята' или пустой список
        status_str = re.findall(r'Статус: (\S+ \S+)', work_name_and_subject)

        status = WorkStatus.PENDING if len(status_str) == 0 \
            else WorkStatus.ACCEPTED if status_str[0] == 'работа принята' \
            else WorkStatus.DECLINED

        new_student_works.append(WorkInfo(work_name, subject, status))

    return new_student_works
