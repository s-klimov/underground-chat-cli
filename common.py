import logging.config
import os

import configargparse as configargparse

logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def get_args() -> [str, int, str, str]:
    """Достает для проекта значения параметров командной строки
    :returns
    host -- хост сервера с чатом
    port -- порт сервера с чатом
    history -- путь к файлу для хранения истории чата
    account -- хэш аккаунта для написания сообщений в чат
    """

    p = configargparse.ArgParser(default_config_files=['.env', ])
    p.add('--host', type=str, required=False, default=os.getenv('host'),
          help='Хост сервера с чатом (default: %(default)s)')
    p.add('--port', type=int, required=False, default=os.getenv('port'),
          help='Порт сервера с чатом (default: %(default)s)')
    p.add('--history', type=str, required=False, default=os.getenv('history'),
          help='Путь к файлу для хранения истории чата (default: %(default)s)')
    p.add('--account', type=str, required=False, default=os.getenv('account'),
          help='Хэш аккаунта для написания сообщений в чат (default: %(default)s)')

    options = p.parse_args()
    return options.host, options.port, options.history, options.account


def cancelled_handler(e) -> None:
    """Обработчик для исключения asyncio.exceptions.CancelledError"""

    logger.info("Прерываем работу сервера")  # логируем полученное сообщение
    raise
