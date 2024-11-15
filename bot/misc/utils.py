from classes.TaskInfo import TaskInfo
from classes.WorkInfo import *
from classes.GradeInfo import *
from datetime import datetime, timedelta, date


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
    msg += f'Оценка: {grade.grade}\n'
    msg += f'Тип: {grade.grade_type}'

    return msg


def format_task_message(task: TaskInfo) -> str:
    msg = f'<b>{task.subject}</b>\n\n'
    msg += f'Дата загрузки: {task.upload_date.strftime("%d-%m-%Y %H:%M:%S")}\n'
    msg += f'Преподаватель: {task.teacher}\n\n'
    msg += f'Ссылка на файл: {task.file_url}\n\n' if task.file_url is not None else ''
    msg += f'Комментарий к работе:\n{task.comment}'

    return msg


def round_down_the_date(date_to_change: date) -> date:
    r"""Rounds date down to 31 jan or 31 jul (update time)"""
    if (date_to_change.month == 1 or date_to_change.month == 7) and date_to_change.day == 31:
        return date_to_change

    if date_to_change.month > 7:
        return datetime(date_to_change.year, 7, 31)

    if date_to_change.month > 1:
        return datetime(date_to_change.year, 1, 31)

    return datetime(date_to_change.year - 1, 7, 31)


def is_update_date_correct(update_date: date) -> bool:
    return (update_date.month == 1 or update_date.month == 7) and update_date.day == 31


def was_update_skipped(current_date: date, last_update_date: date) -> bool:
    r"""Checks if length between last update and given time > 6 months. If yes, update was skipped"""
    return current_date - last_update_date > timedelta(days=186)
