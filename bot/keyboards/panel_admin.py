from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

import strings


def get_admin_panel_keyboard() -> ReplyKeyboardMarkup:
    # добавление нижней клавиатуры
    builder = ReplyKeyboardBuilder()

    builder.row(KeyboardButton(text=strings.CREATE_MAILING))
    builder.row(KeyboardButton(text=strings.FIX_ALL_KEYBOARDS))
    builder.row(KeyboardButton(text=strings.CREATE_SQL_QUERY))
    builder.row(KeyboardButton(text=strings.GO_BACK))

    return builder.as_markup(resize_keyboard=True)