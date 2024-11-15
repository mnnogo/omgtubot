import time

import requests

from classes.GradeInfo import *
from bs4 import BeautifulSoup, ResultSet
from misc.logger import logging
from errors import ParseError


# конфигурация логгинга
logging = logging.getLogger(__name__)


def get_student_grades(session: requests.Session) -> list[GradeInfo]:
    r"""Returns :class:`GradeInfo` list of ALL current grades from site

    :param session: :class:`Session` object with authorized user"""
    start_time = time.time()
    logging.debug('Начался запрос к оценкам...')

    student_grades = []

    student_portal_url = 'https://omgtu.ru/ecab/up.php?student=1'
    grades_url = 'https://up.omgtu.ru/index.php?r=student/index'

    # сделать клик по "студенческий портал"
    response = session.get(student_portal_url, verify=False)

    if response.status_code != 200:
        error_msg = f'Ошибка соединения с сайтом {response.url}'
        logging.exception(error_msg)
        raise ConnectionError(error_msg)

    # сделать клик по "зачетная книжка"
    response = session.get(grades_url, verify=False)

    if response.status_code != 200:
        error_msg = f'Ошибка соединения с сайтом {response.url}'
        logging.exception(error_msg)
        raise ConnectionError(error_msg)

    soup = BeautifulSoup(response.content, 'html.parser')

    # данные каждого семестра
    grades_term_elements = soup.find_all('div', {'role': 'tabpanel'})
    logging.debug(f'Количество семестров: {len(grades_term_elements)}.')

    term = 0
    for grades_term_element in grades_term_elements:
        term += 1

        # данные по одному из типов оценок (экзамен, зачет и т.д.)
        grade_types = grades_term_element.find_all('div', class_='col-xs-12')

        for grade_type_container in grade_types:
            # тип оценок данной секции (экзамен, зачет и т. д.)
            grade_type = grade_type_container.find('h3').text.strip()[:-1]

            # строки с предметами
            subject_rows_html = grade_type_container.find_all('tr')
            # убрать html код со строк и разделить каждый столбец на элементы
            subject_rows: list[list[str]] = _format_subject_rows(subject_rows_html)

            # нужно найти на каких местах в таблице располагаются нужные данные
            header_cells: list[str] = [cell for cell in subject_rows[0]]

            subject_cell: int = _get_subject_cell_index(header_cells)
            control_rating_cell: int | None = _get_control_rating_cell_index(header_cells)
            grade_cell: int = _get_grade_cell_index(header_cells)

            subject_rows = subject_rows[1:]

            for subject_row in subject_rows:
                subject = subject_row[subject_cell]
                term = term  # так нужно

                if control_rating_cell is None:  # нет колонки с рейтингом
                    control_rating = None
                elif not subject_row[control_rating_cell].isdigit():  # колонка с рейтингом есть, но там "-"
                    control_rating = -1
                else:
                    control_rating = int(subject_row[control_rating_cell])

                grade = subject_row[grade_cell]
                grade_enum: Grade = _get_grade_enum(grade)

                student_grades.append(GradeInfo(subject, term, control_rating, grade_type, grade_enum))

    end_time = time.time()
    logging.debug(f'Запрос завершился за {end_time - start_time}')
    return student_grades


def _get_grade_enum(grade: str) -> Grade:
    r"""Takes 'grade' message from omgtu site and transforms it into Grade enum"""
    if grade == 'н/данных':
        return Grade.NA
    elif grade in ('Неудовлетворительно', 'Не удовлетворительно', 'Неявка'):
        return Grade.TWO
    elif grade == 'Удовлетворительно':
        return Grade.THREE
    elif grade == 'Хорошо':
        return Grade.FOUR
    elif grade == 'Отлично':
        return Grade.FIVE
    elif grade == 'Зачтено':
        return Grade.PASSED
    elif grade in ('Незачтено', 'Не зачтено'):
        return Grade.FAILED
    else:
        error_msg = f'Ошибка при парсинге оценки. Описание оценки не подходит не под один enum ' \
                    f'(\'{grade}\')'
        logging.exception(error_msg)
        raise ParseError(error_msg)


def _get_subject_cell_index(header_row: list[str]) -> int:
    subject_keywords = ['Название предмета', 'Название', 'Название практики']

    for subject_keyword in subject_keywords:
        if subject_keyword in header_row:
            return header_row.index(subject_keyword)

    error_msg = f'В списке {header_row} не найден столбец с предметом'
    logging.exception(error_msg)
    raise ValueError(error_msg)


def _get_control_rating_cell_index(header_row: list[str]) -> int | None:
    control_rating_keyword = 'Рейтинг по КН'

    if control_rating_keyword in header_row:
        return header_row.index(control_rating_keyword)

    return None


def _get_grade_cell_index(header_row: list[str]) -> int:
    grade_keyword = 'Оценка'

    if grade_keyword in header_row:
        return header_row.index(grade_keyword)

    error_msg = f'В списке {header_row} не найден столбец с оценкой'
    logging.exception(error_msg)
    raise ValueError(error_msg)


def _format_subject_rows(subject_rows: ResultSet) -> list[list[str]]:
    r"""Removes all html code and extra spaces from subject rows and splits cols into elements"""
    subject_rows_formatted = []

    for row in subject_rows:
        _row = row.find_all(['td', 'th'])
        _row_formatted: list[str] = [cell.get_text(strip=True) for cell in _row]

        subject_rows_formatted.append(_row_formatted)

    return subject_rows_formatted
