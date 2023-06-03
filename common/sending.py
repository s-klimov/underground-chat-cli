import json
import re

import asyncio
from uuid import UUID

import backoff

from common import options, drawing
from common.etc import InvalidToken, logger, cancelled_handler


def authorize(minechat_host: str, minechat_port: 'int > 0', account: UUID):
    def wrap(func):
        async def wrapped(*args):
            _, watchdog_queue, status_queue = args
            status_queue.put_nowait(drawing.SendingConnectionStateChanged.INITIATED)

            reader, writer = await asyncio.open_connection(minechat_host, minechat_port)
            await reader.readline()  # пропускаем строку-приглашение
            writer.write(f"{account}\n".encode())
            await writer.drain()
            response = await reader.readline()  # получаем результат аутентификации

            auth = json.loads(response)

            if auth is None:  # Если результат аутентификации null, то прекращаем выполнение скрипта
                raise InvalidToken(account)

            logger.debug(f"Выполнена авторизация по токену {account}. Пользователь {auth['nickname']}")

            status_queue.put_nowait(drawing.SendingConnectionStateChanged.ESTABLISHED)
            status_queue.put_nowait(drawing.NicknameReceived(auth["nickname"]))

            watchdog_queue.put_nowait("Connection is alive. Prompt before auth")
            await func(*args, writer=writer)

            writer.close()
            status_queue.put_nowait(drawing.SendingConnectionStateChanged.CLOSED)

            await writer.wait_closed()

        return wrapped
    return wrap


@backoff.on_exception(backoff.expo,
                      asyncio.exceptions.CancelledError,
                      raise_on_giveup=False,
                      giveup=cancelled_handler)
@authorize(options.host, options.sending_port, options.account)
async def send_messages(queue, watchdog_queue, _, /, writer):

    while message := await queue.get():
        message_line = ''.join([re.sub(r'\\n', ' ', message), '\n']).encode()
        line_feed = '\n'.encode()

        writer.writelines([message_line, line_feed])
        await writer.drain()
        watchdog_queue.put_nowait('Connection is alive. Message sent')
