import re
import time

import requests
from bs4 import BeautifulSoup
from WorkInfo import *
from misc.logger import logging


# конфигурация логгинга
logging = logging.getLogger(__name__)


def get_student_works(session: requests.Session) -> list[WorkInfo]:
    r"""Returns :class:`WorkInfo` list of ALL current works from site

    :param session: :class:`Session` object with authorized user"""
    start_time = time.time()
    logging.debug('Начался запрос к работам...')

    student_works = []

    # ссылка на GET запрос ко всем работам
    data_url = 'https://www.omgtu.ru/ecab/modules/vkr2/otherlist.php'

    response = session.get(data_url, verify=False)
    if response.status_code != 200:
        error_msg = f'Ошибка соединения с сайтом {response.url}'
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

        student_works.append(WorkInfo(work_name, subject, status))

    end_time = time.time()
    logging.debug(f'Запрос завершился за {end_time - start_time}')
    return student_works
