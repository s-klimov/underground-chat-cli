import logging.config
import os

import configargparse as configargparse

logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


class CommonArgs:
    """Класс аргументов командной строки"""

    def __init__(self):
        """Задаем общие параметры для всех скриптов проекта"""

        self._parser = configargparse.ArgParser(default_config_files=['.env', ], ignore_unknown_config_file_keys=True)
        self._parser.add('--host', type=str, required=False, default=os.getenv('host'),
                          help='Хост сервера с чатом (default: %(default)s)')
        self._parser.add('--port', type=int, required=False, default=os.getenv('port'),
                          help='Порт сервера с чатом (default: %(default)s)')

    def get_args(self):
        return self._parser.parse_args()


class ListenArgs(CommonArgs):
    """Класс параметров скрипта прослушивания чата"""

    def __init__(self):
        """Добавляем специфические параметры командной строки для скрипта прослушивания чата"""
        super().__init__()
        self._parser.add('--history', type=str, required=False, default=os.getenv('history'),
                         help='Путь к файлу для хранения истории чата (default: %(default)s)')


class WriteArgs(CommonArgs):
    """Класс параметров скрипта написания сообщений в чат"""

    def __init__(self):
        """Добавляем специфические параметры командной строки для скрипта написания сообщений в чат"""
        super().__init__()
        self._parser.add('--account', type=str, required=False, default=os.getenv('account'),
                         help='Хэш аккаунта для написания сообщений в чат (default: %(default)s)')
        self._parser.add('--register', type=str, required=False,
                         help='Имя пользователя для регистрации')

def cancelled_handler(e) -> None:
    """Обработчик для исключения asyncio.exceptions.CancelledError"""

    logger.info("Прерываем работу сервера")  # логируем полученное сообщение
    raise
