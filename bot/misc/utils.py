from WorkInfo import *
from GradeInfo import *


def format_work_message(work: WorkInfo) -> str:
    return f'<b>{work.work_name}</b>\n' \
           f'Предмет: {work.subject}\n' \
           f'Статус: {work.status}'


def format_grade_message(grade: GradeInfo) -> str:
    msg = f'<b>{grade.subject}</b>.\n'

    control_rating_str = f'Рейтинг по КН: {grade.control_rating}\n' \
        if grade.control_rating is not None and grade.control_rating != -1 else \
        'Рейтинг по КН: -\n' if grade.control_rating == -1 else ''

    msg += control_rating_str
    msg += f'Оценка: {grade.grade}'

    return msg
