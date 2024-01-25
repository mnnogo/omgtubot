from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


TERM_COUNT = 8


def get_grades_default_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    [builder.button(text=f'Семестр {i}', callback_data=f'btn_term{i}') for i in range(1, TERM_COUNT + 1)]
    builder.adjust(2)

    btn_exit = InlineKeyboardButton(text='Выход', callback_data='btn_exit')
    builder.row(btn_exit)

    return builder.as_markup(resize_keyboard=True)
