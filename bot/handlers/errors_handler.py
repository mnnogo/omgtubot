import html

from aiogram import Router
from aiogram.types import ErrorEvent

from bot_init import bot
from misc.logger import logging
import misc.env

router = Router()
r"""Router for errors handler"""

# конфигурация логгинга
logging = logging.getLogger(__name__)


@router.error()
async def errors_handler(event: ErrorEvent):
    exception_text = event.exception
    logging.exception(exception_text, exc_info=True)
    await notify_developer(str(exception_text))
    return True


# функция для уведомления разработчика о возникновении крит. ошибки
async def notify_developer(exception_text: str):
    # экранирование текста, чтобы избежать проблем с тегами
    safe_text = html.escape(f"Возникла критическая ошибка: {exception_text}")

    if len(safe_text) > 4096:
        safe_text = safe_text[-4090:]

    await bot.send_message(misc.env.DEVELOPER_CHAT_ID, safe_text)
