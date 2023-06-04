import asyncio
from typing import Optional

from aiofile import async_open

import backoff as backoff

from common import cancelled_handler, logger, options, drawing

logger.name = "LISTENER"


def authorize(
        minechat_host: str,
        minechat_port: 'int > 0',
):
    def wrap(func):
        async def wrapped(*args):
            _, watchdog_queue, status_queue = args
            status_queue.put_nowait(drawing.ReadConnectionStateChanged.INITIATED)
            reader, _ = await asyncio.open_connection(minechat_host, minechat_port)

            await func(*args, reader=reader)
        return wrapped
    return wrap


@backoff.on_exception(backoff.expo,
                      asyncio.exceptions.CancelledError,
                      raise_on_giveup=False,
                      giveup=cancelled_handler)
@authorize(options.host, options.listen_port)
async def listen_messages(
        queue: Optional[asyncio.Queue],
        watchdog_queue: Optional[asyncio.Queue],
        status_queue: Optional[asyncio.Queue],
        /,
        reader: Optional[asyncio.StreamReader],
) -> None:
    """Считывает сообщения из сайта в консоль"""

    status_queue.put_nowait(drawing.ReadConnectionStateChanged.ESTABLISHED)

    while data := await reader.readline():

        logger.debug(data.decode().rstrip())  # логируем полученное сообщение

        await save_messages(filepath=options.history, message=data.decode())

        if queue is not None:
            queue.put_nowait(data.decode().rstrip())

        if watchdog_queue is not None:
            watchdog_queue.put_nowait('Connection is alive. New message in chat')


async def save_messages(filepath: str, message: str):
    """Сохраняет сообщение в файл"""

    async with async_open(filepath, 'a') as afp:
        await afp.write(message)
