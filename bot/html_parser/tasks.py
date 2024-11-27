from datetime import datetime

import requests
from bs4 import BeautifulSoup

from classes.FileInfo import FileInfo
from classes.TaskInfo import TaskInfo
from classes.TaskSubjectInfo import TaskSubjectInfo
from misc.logger import logging

# конфигурация логгинга
logging = logging.getLogger(__name__)


def get_student_tasks(session: requests.Session) -> list[TaskInfo]:
    r"""
    :param session: :class:`Session` object with authorized user
    :return: list of every single work existing in contact work for student, no grouping
    """
    student_tasks = []

    student_portal_url = 'https://omgtu.ru/ecab/up.php?student=1'

    # сделать клик по "студенческий портал"
    response = session.get(student_portal_url, verify=False)

    if response.status_code != 200:
        error_msg = f'Ошибка соединения с сайтом {response.url}'
        logging.exception(error_msg)
        raise ConnectionError(error_msg)

    # получить название предметов + ссылки на них
    subjects_and_links: list[TaskSubjectInfo] = get_every_subject_link(session)

    # проходим по каждой ссылке и парсим
    for subject_and_link in subjects_and_links:
        response = session.get(subject_and_link.subject_url)

        if response.status_code != 200:
            error_msg = f'Ошибка соединения с сайтом {response.url}'
            logging.exception(error_msg)
            raise ConnectionError(error_msg)

        soup = BeautifulSoup(response.content, 'html.parser')

        # элементы с каждой работой
        task_elements = soup.find_all('tr')[1:]  # столбец с названиями вырезаем

        for task_element in task_elements:
            task_info = task_element.find_all('td')

            subject = subject_and_link.subject
            comment = task_info[1].text
            file_elements = task_info[2].find_all('a')  # блок с ссылкой на файл + названием
            files_info = [
                FileInfo(name=file.find("h4").text.strip(), url='https://up.omgtu.ru' + file['href'])
                for file in file_elements
            ]
            upload_date = datetime.strptime(task_info[3].text, "%Y-%m-%d %H:%M:%S")
            teacher = task_info[4].text

            student_tasks.append(
                TaskInfo(subject, comment, files_info, upload_date, teacher)
            )

    return student_tasks


def get_every_subject_link(session: requests.Session) -> list[TaskSubjectInfo]:
    r"""
    :param session: session that is **already** on contact work page
    """
    subject_links = []

    tasks_url = 'https://up.omgtu.ru/index.php?r=remote/read'

    # сделать клик по "контактная работа"
    response = session.get(tasks_url, verify=False)

    if response.status_code != 200:
        error_msg = f'Ошибка соединения с сайтом {response.url}'
        logging.exception(error_msg)
        raise ConnectionError(error_msg)

    soup = BeautifulSoup(response.content, 'html.parser')

    # элементы с каждой дисциплиной
    subject_elements = soup.find_all('tr')[1:-1]  # столбец с названиями вырезаем

    for subject_element in subject_elements:
        # берем два элемента, сырое название предмета и ссылка, спрятанная за <a href>
        subject_and_link = subject_element.find_all('td', style='padding:10px;')

        subject = subject_and_link[0].text

        link_element = subject_and_link[1].find('a')
        link = 'https://up.omgtu.ru' + link_element['href']

        subject_links.append(TaskSubjectInfo(subject, link))

    return subject_links
