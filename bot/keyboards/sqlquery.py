from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_sqlquery_keyboard() -> InlineKeyboardMarkup:
    # добавление нижней клавиатуры
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text='❌ Отмена', callback_data='btn_cancel_query'))

    return builder.as_markup(resize_keyboard=True)
