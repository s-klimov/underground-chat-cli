import asyncio

import aiofiles as aiofiles
from datetime import datetime as dt

import backoff as backoff

from common import get_args, cancelled_handler, logger


@backoff.on_exception(backoff.expo,
                      asyncio.exceptions.CancelledError,
                      raise_on_giveup=False,
                      giveup=cancelled_handler)
@backoff.on_exception(backoff.expo,
                      (OSError, asyncio.exceptions.TimeoutError))
async def listen_messages(minechat_host: str, minechat_port: 'int > 0', minechat_history_file: str) -> None:
    """Считывает сообщения из сайта в консоль"""

    reader, _ = await asyncio.open_connection(minechat_host, minechat_port)

    while data := await reader.readline():

        logger.info(data.decode().replace('\n', ''))  # логируем полученное сообщение

        async with aiofiles.open(minechat_history_file, 'a') as f:  # записываем полученное сообщение в файл
            await f.write(f"[{dt.now().strftime('%Y-%m-%d %H:%M')}]{data.decode()}")


if __name__ == '__main__':

    host, port, history_file, _ = get_args()

    try:
        asyncio.run(listen_messages(host, port, history_file))
    except KeyboardInterrupt:
        pass
    finally:
        logger.error('Работа сервера остановлена')
