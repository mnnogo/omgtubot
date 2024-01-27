from database import make_sql_query


def delete_all_student_works(login: str) -> None:
    r"""Deletes all works in database that user with omgtu 'login' had in database."""
    make_sql_query('DELETE FROM old_works WHERE login = %s', (login,))


def delete_all_student_grades(login: str) -> None:
    r"""Deletes all grades in database that user with omgtu 'login' had in database."""
    make_sql_query('DELETE FROM old_grades WHERE login = %s', (login,))
