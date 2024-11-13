import asyncio

from aiogram.filters import Command
from aiogram.types import Message

from background_tasks import background
import background_tasks.notifications
import background_tasks.term_update
import keyboards.main

from bot_init import bot, dp
from handlers import authorization, works, grades, settings, errors_handler, admin_panel
from misc.logger import logging

# конфигурация логгинга
logging = logging.getLogger(__name__)

# подключение рутеров из файлов (разбито по каждой команде и кнопке)
dp.include_routers(
    authorization.router, works.router, grades.router, settings.router, errors_handler.router, admin_panel.router
)


# команда /start
@dp.message(Command('start', 'help'))
async def start_command(message: Message):
    msg = 'Привет! Этот бот позволяет отслеживать обновления статуса работ в отчетных работах и оценок на сайте ОмГТУ.\n' \
          '\n' \
          'Для начала работы нажмите <b>"Авторизация"</b>.\n' \
          'При авторизации все введенные пароли хранятся в зашифрованном виде.\n' \
          'Для настройки уведомлений, изменения семестра и т.д. нажмите <b>"Настройки"</b>\n' \
          '\n' \
          'При изменении статуса работы или оценки за <b>текущий семестр</b> бот пришлет Вам уведомление. ' \
          'Текущий семестр указывается пользователем при авторизации. Проверка происходит раз в 2 часа. ' \
          'Если вами была удалена или выложена новая работа, то об этом не придет уведомление.\n' \
          '\n' \
          'Каждые 31 января и 31 июля происходит изменение текущего семестра на +1. Семестр влияет только на ' \
          'уведомления об оценках.\n' \
          '\n' \
          'В будущем возможности бота вероятно будут расширяться.\n' \
          'При возникновении проблем или пожеланий пишите в ТГ или в ВК.\n' \
          '\n' \
          'Telegram: t.me/Mnogo1234\n' \
          'VK: vk.com/mnnogo'

    # отправка приветствия + добавление основной клавиатуры
    await message.reply(text=msg, reply_markup=keyboards.main.get_main_keyboard(message.from_user.id))


@dp.message(Command('fixkeyboard'))
async def update_keyboard_command(message: Message):
    await message.reply('Клавиатура исправлена.', reply_markup=keyboards.main.get_main_keyboard(message.from_user.id))


async def run_bot():
    # предотвращение выключения бота
    background_tasks.background.keep_alive()

    # запуск прибавления семестра 31 января и 31 июля (или позже если бот был выключен)
    asyncio.ensure_future(
        background_tasks.term_update.try_update_term()
    )

    # запуск периодических уведомлений
    asyncio.ensure_future(
        background_tasks.notifications.send_notifications_periodically()
    )

    logging.debug('Попытка запустить бота...')

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logging.exception(e)
        await errors_handler.notify_developer(str(e))
