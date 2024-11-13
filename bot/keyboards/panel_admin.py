from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_admin_panel_keyboard() -> ReplyKeyboardMarkup:
    # добавление нижней клавиатуры
    builder = ReplyKeyboardBuilder()

    builder.row(KeyboardButton(text='Сделать рассылку'))
    builder.row(KeyboardButton(text='Обновить клавиатуру у всех'))
    builder.row(KeyboardButton(text='Выполнить SQL-запрос'))
    builder.row(KeyboardButton(text='Назад'))

    return builder.as_markup(resize_keyboard=True)