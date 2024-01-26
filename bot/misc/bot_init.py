from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from misc import env


# создание бота
TOKEN = env.TOKEN
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
