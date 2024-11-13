from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import misc.env


def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    # добавление нижней клавиатуры
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text='Авторизация'))
    builder.row(KeyboardButton(text='Посмотреть работы'),
                KeyboardButton(text='Посмотреть зачетку'))
    builder.row(KeyboardButton(text='Настройки'))

    if user_id == misc.env.DEVELOPER_CHAT_ID:
        builder.row(KeyboardButton(text='Панель админа'))

    return builder.as_markup(resize_keyboard=True)
