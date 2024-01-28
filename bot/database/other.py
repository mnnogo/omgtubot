from database import make_sql_query


def is_user_authorized(user_id: int) -> bool:
    r"""Checks if user with 'user_id' has login in database. It also returns False if there's no works added into DB"""
    user_encounters = make_sql_query('SELECT COUNT(*) FROM user_info WHERE tg_id = %s', (user_id,))[0][0]

    return user_encounters != 0


def is_user_subscribed_notifications(user_id: int) -> bool:
    r"""Checks if user is subscribed to notifications. Returns false if user is not in database"""
    result = make_sql_query('SELECT notifications FROM user_info WHERE tg_id = %s', (user_id,))

    if len(result) == 0:
        return False

    return bool(result[0][0])


def is_user_subscribed_mailing(user_id: int) -> bool:
    r"""Checks if user is subscribed to mailings. Returns false if user is not in database"""
    result = make_sql_query('SELECT mailing FROM user_info WHERE tg_id = %s', (user_id,))

    if len(result) == 0:
        return False

    return bool(result[0][0])
