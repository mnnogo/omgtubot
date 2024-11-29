from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import misc.env
import strings


def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    # добавление нижней клавиатуры
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=strings.START_AUTH))
    builder.row(KeyboardButton(text=strings.VIEW_WORKS),
                KeyboardButton(text=strings.VIEW_GRADES))
    builder.row(KeyboardButton(text=strings.OPEN_SETTINGS))

    if user_id == misc.env.DEVELOPER_CHAT_ID:
        builder.row(KeyboardButton(text=strings.OPEN_ADMIN_PANEL))

    return builder.as_markup(resize_keyboard=True)
