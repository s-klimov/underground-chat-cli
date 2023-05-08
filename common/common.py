import json
import logging.config
import os
import re
import time
import uuid

import asyncio
from aiofile import async_open
from json import JSONDecodeError
from pathlib import Path

import configargparse as configargparse
from aiologger import Logger
from async_timeout import timeout
from dotenv import load_dotenv

from common import gui
from common.gui import draw_error

USERS_FILE = "users.json"

logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)  # TODO Logger.with_default_handlers()

watchdog_logger = logging.getLogger(__name__)  # TODO Logger.with_default_handlers()


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
        self._parser.add('--account', type=uuid.UUID, required=False, default=os.getenv('ACCOUNT'),
                         help='Хэш аккаунта для написания сообщений в чат (default: %(default)s). '
                              'Если задан параметр register, то account игнорируется.')
        self._parser.add('--register', type=str, required=False,
                         help='Имя пользователя для регистрации')
        self._parser.add('--message', type=str, required=True,
                         help='Текст сообщения для отправки в чат')


class GUIArgs(CommonArgs):
    """Класс параметров скрипта графического интерфейса"""

    def __init__(self):
        """Добавляем специфические параметры командной строки для скрипта написания сообщений в чат"""
        super().__init__()
        self._parser.add('--history', type=str, required=False, default=os.getenv('HISTORY'),
                         help='Путь к файлу для хранения истории чата (default: %(default)s)')
        self._parser.add('--account', type=uuid.UUID, required=False, default=os.getenv('ACCOUNT'),
                         help='Хэш аккаунта для написания сообщений в чат (default: %(default)s).')


class CommonAuth:
    """Базовый класс для аутентификации на сервере minechat"""

    def __init__(self, minechat_host: str, minechat_port: 'int >0', watchdog_queue: asyncio.Queue = None, status_queue: asyncio.Queue = None, **kwargs):
        self.__minechat_host = minechat_host
        self.__minechat_port = minechat_port
        self._watchdog_queue = watchdog_queue
        self._queue = status_queue

        super().__init__(**kwargs)

    async def __aenter__(self):
        """Метод асинхронного контекстного менеджера"""

        if self._queue is not None:
            self._queue.put_nowait(gui.ReadConnectionStateChanged.INITIATED)
            self._queue.put_nowait(gui.SendingConnectionStateChanged.INITIATED)

        reader, self.__writer = await asyncio.open_connection(self.__minechat_host, self.__minechat_port)
        return reader, self.__writer

    async def __aexit__(self, *exc):
        logger.info('Закрываем соедиение с чатом')
        self.__writer.close()

        if self._queue is not None:
            self._queue.put_nowait(gui.ReadConnectionStateChanged.CLOSED)

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
        writer.write(f"{self.__account_hash}\n".encode())
        await writer.drain()
        response = await reader.readline()  # получаем результат аутентификации

        auth = json.loads(response)

        if auth is None:  # Если результат аутентификации null, то прекращаем выполнение скрипта
            raise InvalidToken(self.__account_hash)

        logger.debug(f'Выполнена авторизация по токену {self.__account_hash}. Пользователь {auth["nickname"]}')

        if self._queue is not None:
            self._queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)
            self._queue.put_nowait(gui.NicknameReceived(auth["nickname"]))

        if self._watchdog_queue is not None:
            self._watchdog_queue.put_nowait('Connection is alive. Prompt before auth')

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

        try:
            user = json.loads(response)
        except JSONDecodeError:
            raise ValueError(
                'Ошибка регистрации пользователя. Проверьте настройки подключения к серверу. Например порт'
            )

        if json.loads(response) is None:  # Если результат аутентификации null, то прекращаем выполнение скрипта
            raise ValueError(f'Ошибка регистрации пользователя. Ответ сервера {response}')
        logger.debug(f'Пользователь {user} зарегистрирован')

        # записываем полученное сообщение в файл
        my_file = Path(USERS_FILE)
        if my_file.is_file():
            async with async_open(USERS_FILE, 'r') as f:
                users = json.loads(await f.read())
        else:
            users = dict()

        users[user['nickname']] = user['account_hash']
        async with async_open(USERS_FILE, 'w') as f:
            await f.write(json.dumps(users))

        if self._queue is not None:
            self._queue.put_nowait(gui.ReadConnectionStateChanged.ESTABLISHED)

        return reader, writer


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


async def send_messages(queue, writer, watchdog_queue, status_queue):

    status_queue.put_nowait(gui.SendingConnectionStateChanged.ESTABLISHED)

    while message := await queue.get():
        message_line = ''.join([re.sub(r'\\n', ' ', message), '\n']).encode()
        line_feed = '\n'.encode()

        writer.writelines([message_line, line_feed])
        await writer.drain()
        watchdog_queue.put_nowait('Connection is alive. Message sent')

    status_queue.put_nowait(gui.SendingConnectionStateChanged.CLOSED)


async def watch_for_connection(watchdog_queue: asyncio.Queue):

    timer = 20  # TODO рассчитать время для первичной загрузки истории переписки
    while True:
        async with timeout(timer) as cm:  # FIXME
            message = await watchdog_queue.get()
            watchdog_logger.debug(message)
            timer = 1
