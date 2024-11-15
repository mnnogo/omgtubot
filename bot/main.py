import telegram_bot
import asyncio
import html_parser.main, html_parser.tasks
import misc.utils
from datetime import datetime
import database.get

if __name__ == '__main__':
    # asyncio.run(telegram_bot.run_bot())
    update_term: bool = misc.utils.was_update_skipped(
        datetime.now().date(),
        database.get.get_user_last_update(1876123382)
    )
