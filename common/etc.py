import logging.config
import os
import uuid

import asyncio

import configargparse
from aiologger import Logger
from async_timeout import timeout
from dotenv import load_dotenv

from common import drawing
from common.drawing import draw_error

TIMEOUT_MAX = 5  # NOTE 5 секунд установлено эксперементально
USERS_FILE = "users.json"

logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = Logger.with_default_handlers()

watchdog_logger = Logger.with_default_handlers()


def get_args():
    load_dotenv()

    parser = configargparse.ArgParser(default_config_files=['.env', ], ignore_unknown_config_file_keys=True)
    parser.add('--host', type=str, required=False, default=os.getenv('HOST'),
               help='Хост сервера с чатом (default: %(default)s)')
    parser.add('--listen_port', type=int, required=False, default=os.getenv('LISTEN_PORT'),
               help='Порт для чтения сообщений сервера с чатом (default: %(default)s)')
    parser.add('--sending_port', type=int, required=False, default=os.getenv('SENDING_PORT'),
               help='Порт для отправки сообщений на сервер с чатом (default: %(default)s)')
    parser.add('--history', type=str, required=False, default=os.getenv('HISTORY'),
               help='Путь к файлу для хранения истории чата (default: %(default)s)')
    parser.add('--account', type=uuid.UUID, required=False, default=os.getenv('ACCOUNT'),
               help='Хэш аккаунта для написания сообщений в чат (default: %(default)s). '
                    'Если задан параметр register, то account игнорируется.')
    parser.add('--register', type=str, required=False,
               help='Имя пользователя для регистрации')

    return parser.parse_args()


def cancelled_handler(e) -> None:
    """Обработчик для исключения asyncio.exceptions.CancelledError"""

    logger.info("Прерываем работу сервера")  # логируем полученное сообщение
    raise


class InvalidToken(Exception):
    """Исключение ошибки авторизации по токену"""

    def __init__(self, account_hash: uuid.UUID):
        # Call the base class constructor with the parameters it needs
        message = f'Проверьте токен {account_hash}, сервер его не узнал'
        super().__init__(message)

        # отрисовываем окно с тексом ошибки
        asyncio.gather(
            draw_error(message)
        )


async def watch_for_connection(watchdog_queue: asyncio.Queue, status_queue: asyncio.Queue, /):

    while True:
        try:
            async with timeout(TIMEOUT_MAX):
                message = await watchdog_queue.get()
        except asyncio.exceptions.TimeoutError:
            watchdog_logger.debug("%ss timeout is elapsed" % (TIMEOUT_MAX,))
            status_queue.put_nowait(drawing.ReadConnectionStateChanged.INITIATED)
            status_queue.put_nowait(drawing.SendingConnectionStateChanged.INITIATED)
        else:
            status_queue.put_nowait(drawing.ReadConnectionStateChanged.ESTABLISHED)
            status_queue.put_nowait(drawing.SendingConnectionStateChanged.ESTABLISHED)
            watchdog_logger.debug(message)
