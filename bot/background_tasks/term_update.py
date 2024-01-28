import asyncio
from datetime import datetime

import database.get
import database.update
import misc.utils
from bot_init import bot
from handlers import errors_handler
from misc.logger import logging

# конфигурация логгинга
logging = logging.getLogger(__name__)


async def try_update_term() -> None:
    while True:
        logging.debug('Проверка на обновление семестра')
        try:
            users_list = database.get.get_users_to_update_term()

            for user_id in users_list:
                current_term = database.get.get_user_term(user_id=user_id)
                max_term = database.get.get_user_max_term(user_id=user_id)

                # семестры закончились
                if current_term > max_term:
                    continue

                # был ли скипнут апдейт для пользователя или сейчас дата обновления
                update_term: bool = True or misc.utils.was_update_skipped(
                    datetime.now().date(),
                    database.get.get_user_last_update(user_id)
                ) or misc.utils.is_update_date_correct(
                    datetime.now().date()
                )

                if update_term:
                    database.update.update_user_term(user_id, current_term + 1)

                    logging.info(f'Обновлен семестр пользователю "{user_id}" на {current_term + 1}')

                    if current_term == max_term:
                        await bot.send_message(user_id, 'Поздравляю! Вы закончили учиться!')
                    else:
                        await bot.send_message(user_id, f'Семестр автоматически обновлен на <b>{current_term + 1}</b>.')

                    database.update.update_user_last_update(
                        user_id,
                        misc.utils.round_down_the_date(datetime.now().date())
                    )

        except Exception as e:
            logging.exception(e)
            await errors_handler.notify_developer(str(e))

        # проверка каждые пол месяца (макс. пол месяца задержки некритично)
        await asyncio.sleep(60 * 60 * 24 * 15)
