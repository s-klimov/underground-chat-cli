import json
import logging.config
import os
import re
import uuid

import asyncio
from pathlib import Path

import aiofiles
import configargparse as configargparse
from dotenv import load_dotenv

USERS_FILE = "users.json"

logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


class CommonArgs:
    """Класс аргументов командной строки"""

    def __init__(self):
        """Задаем общие параметры для всех скриптов проекта"""
        load_dotenv()

        self._parser = configargparse.ArgParser(default_config_files=['.env', ], ignore_unknown_config_file_keys=True)
        self._parser.add('--host', type=str, required=False, default=os.getenv('HOST'),
                         help='Хост сервера с чатом (default: %(default)s)')
        self._parser.add('--port', type=int, required=False, default=os.getenv('PORT'),
                         help='Порт сервера с чатом (default: %(default)s)')

    def get_args(self):
        return self._parser.parse_args()


class ListenArgs(CommonArgs):
    """Класс параметров скрипта прослушивания чата"""

    def __init__(self):
        """Добавляем специфические параметры командной строки для скрипта прослушивания чата"""
        super().__init__()
        self._parser.add('--history', type=str, required=False, default=os.getenv('HISTORY'),
                         help='Путь к файлу для хранения истории чата (default: %(default)s)')


class WriteArgs(CommonArgs):
    """Класс параметров скрипта написания сообщений в чат"""

    def __init__(self):
        """Добавляем специфические параметры командной строки для скрипта написания сообщений в чат"""
        super().__init__()
        self._parser.add('--account', type=uuid.UUID, required=False, default=os.getenv('account'),
                         help='Хэш аккаунта для написания сообщений в чат (default: %(default)s). '
                              'Если задан параметр register, то account игнорируется.')
        self._parser.add('--register', type=str, required=False,
                         help='Имя пользователя для регистрации')
        self._parser.add('--message', type=str, required=True,
                         help='Текст сообщения для отправки в чат')


class CommonAuth:
    """Базовый класс для аутентификации на сервере minechat"""

    def __init__(self, minechat_host: str, minechat_port: 'int >0', **kwargs):
        self.__minechat_host = minechat_host
        self.__minechat_port = minechat_port
        super().__init__(**kwargs)

    async def __aenter__(self):
        """Метод асинхронного контекстного менеджера"""

        reader, self.__writer = await asyncio.open_connection(self.__minechat_host, self.__minechat_port)
        return reader, self.__writer

    async def __aexit__(self, *exc):
        logger.info('Закрываем соедиение с чатом')
        self.__writer.close()
        await self.__writer.wait_closed()


class Authorise(CommonAuth):
    """Класс авторизации на сервере minechat"""

    def __init__(self, account: uuid.UUID, **kwargs):
        self.__account_hash = account
        super().__init__(**kwargs)

    async def __aenter__(self):
        """Метод асинхронного контекстного менеджера"""

        reader, writer = await super().__aenter__()

        await reader.readline()  # пропускаем строку-приглашение
        logger.debug(self.__account_hash)
        writer.write(f"{self.__account_hash}\n".encode())
        await writer.drain()
        response = await reader.readline()  # получаем результат аутентификации

        if json.loads(response) is None:  # Если результат аутентификации null, то прекращаем выполнение скрипта
            raise ValueError('Неизвестный токен. Проверьте его или зарегистрируйте заново.')
        return reader, writer


class Register(CommonAuth):
    """Класс регистрации на сервере minechat"""

    def __init__(self, account: str, **kwargs):
        self.__user_name = account
        super().__init__(**kwargs)

    async def __aenter__(self):
        """Метод асинхронного контекстного менеджера"""

        reader, writer = await super().__aenter__()

        await reader.readline()  # пропускаем строку-приглашение ввода хэша аккаунта
        writer.write("\n".encode())  # вводим пустую строку, чтобы получить приглашение для регистрации
        await writer.drain()
        await reader.readline()  # пропускаем строку-приглашение ввода имени пользователя
        user_name = re.sub(r'\\n', ' ', self.__user_name)
        writer.write(f"{user_name}\n".encode())
        await writer.drain()
        response = await reader.readline()  # получаем результат регистрации

        user = json.loads(response)

        if json.loads(response) is None:  # Если результат аутентификации null, то прекращаем выполнение скрипта
            raise ValueError(f'Ошибка регистрации пользователя. Ответ сервера {response}')
        logger.debug(f'Пользователь {user} зарегистрирован')

        # записываем полученное сообщение в файл
        my_file = Path(USERS_FILE)
        if my_file.is_file():
            async with aiofiles.open(USERS_FILE, 'r') as f:
                users = json.loads(await f.read())
        else:
            users = dict()

        users[user['nickname']] = user['account_hash']
        async with aiofiles.open(USERS_FILE, 'w') as f:
            await f.write(json.dumps(users))

        return reader, writer


def cancelled_handler(e) -> None:
    """Обработчик для исключения asyncio.exceptions.CancelledError"""

    logger.info("Прерываем работу сервера")  # логируем полученное сообщение
    raise
