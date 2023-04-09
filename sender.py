import asyncio
import json
import re
import uuid
from functools import wraps
from pathlib import Path

import aiofiles
import backoff as backoff

from common import cancelled_handler, logger, WriteArgs, Authorise

logger.name = "SENDER"
USERS_FILE = "users.json"


async def register(minechat_host: str, minechat_port: 'int > 0', user_name: str) -> None:
    """Регистрирует пользователя на сервере"""
    reader, writer = await asyncio.open_connection(minechat_host, minechat_port)

    await reader.readline()  # пропускаем строку-приглашение ввода хэша аккаунта
    writer.write("\n".encode())  # вводим пустую строку, чтобы получить приглашение для регистрации
    await writer.drain()
    await reader.readline()  # пропускаем строку-приглашение ввода имени пользователя
    writer.write(f"{user_name}\n".encode())
    await writer.drain()
    response = await reader.readline()  # получаем результат регистрации

    user = json.loads(response)
    try:
        if json.loads(response) is None:  # Если результат аутентификации null, то прекращаем выполнение скрипта
            raise ValueError(f'Ошибка регистрации пользователя. Ответ сервера {response}')
        logger.debug(f'Пользователь {user} зарегистрирован')

    except ValueError as e:
        logger.debug(str(e))
    else:
        my_file = Path(USERS_FILE)
        if my_file.is_file():
            async with aiofiles.open(USERS_FILE, 'r') as f:
                users = json.loads(await f.read())
        else:
            users = dict()

        users[user['nickname']] = user['account_hash']
        async with aiofiles.open(USERS_FILE, 'w') as f:  # записываем полученное сообщение в файл
            await f.write(json.dumps(users))
    finally:
        logger.debug('Закрываем соединение')
        writer.close()
        await writer.wait_closed()


def authorise(function):
    @wraps(function)
    async def wrapper(*args):
        breakpoint()
        match args:
            case (str, int, uuid.UUID):
                minechat_host, minechat_port, account_hash = args
            case _:
                raise SyntaxError

        reader, writer = await asyncio.open_connection(minechat_host, minechat_port)

        await reader.readline()  # пропускаем строку-приглашение
        logger.debug(account_hash)
        writer.write(f"{account_hash}\n".encode())
        await writer.drain()
        response = await reader.readline()  # получаем результат аутентификации

        if json.loads(response) is None:  # Если результат аутентификации null, то прекращаем выполнение скрипта
            raise ValueError('Неизвестный токен. Проверьте его или зарегистрируйте заново.')

        await function(minechat_host, minechat_port, account_hash, reader=reader, writer=writer)

        logger.debug('Закрываем соединение')
        writer.close()
        await writer.wait_closed()

    return wrapper


@backoff.on_exception(backoff.expo,
                      asyncio.exceptions.CancelledError,
                      raise_on_giveup=False,
                      giveup=cancelled_handler)
@backoff.on_exception(backoff.expo,
                      (OSError, asyncio.exceptions.TimeoutError),
                      max_tries=3)
# @authorise
async def submit_message(minechat_host: str, minechat_port: 'int >0', account_hash: uuid.UUID, message:str) -> None:
    """Считывает сообщения из сайта в консоль
    """
    message = input('Что напишем в чат: ').strip()
    message = re.sub(r'\\n', '', message)

    async with Authorise(minechat_host, minechat_port, account_hash) as (_, writer):
        writer.writelines([f'{message}\n'.encode(), '\n'.encode()])
        await writer.drain()
        logger.debug(message)


if __name__ == '__main__':

    args = WriteArgs()
    options = args.get_args()

    try:
        asyncio.run(
            submit_message(
                options.host,
                options.port,
                options.register or options.account,
                options.message,
            )
        )

    except KeyboardInterrupt:
        pass
    except ValueError as e:
        logger.error(str(e))
    finally:
        logger.info('Работа сервера остановлена')
