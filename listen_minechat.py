import asyncio
from typing import Optional

from aiofile import async_open

import backoff as backoff

from common import cancelled_handler, logger, ListenArgs

logger.name = "LISTENER"


@backoff.on_exception(backoff.expo,
                      asyncio.exceptions.CancelledError,
                      raise_on_giveup=False,
                      giveup=cancelled_handler)
@backoff.on_exception(backoff.expo,
                      (OSError, asyncio.exceptions.TimeoutError))
async def listen_messages(
        minechat_host: str,
        minechat_port: 'int > 0',
        minechat_history_file: str,
        watchdog_queue: Optional[asyncio.Queue] = None,
        queue: Optional[asyncio.Queue] = None,
) -> None:
    """Считывает сообщения из сайта в консоль"""

    reader, _ = await asyncio.open_connection(minechat_host, minechat_port)

    while data := await reader.readline():

        logger.debug(data.decode().rstrip())  # логируем полученное сообщение

        await save_messages(filepath=minechat_history_file, message=data.decode())

        if queue is not None:
            queue.put_nowait(data.decode().rstrip())

        if watchdog_queue is not None:
            watchdog_queue.put_nowait('Connection is alive. New message in chat')


async def save_messages(filepath: str, message: str):
    """Сохраняет сообщение в файл"""

    async with async_open(filepath, 'a') as afp:
        await afp.write(message)


if __name__ == '__main__':

    args = ListenArgs()
    options = args.get_args()

    try:
        asyncio.run(listen_messages(options.host, options.port, options.history))
    except KeyboardInterrupt:
        pass
    finally:
        logger.info('Работа сервера остановлена')
