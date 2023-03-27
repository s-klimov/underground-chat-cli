import asyncio
import logging.config

import aiofiles as aiofiles
from datetime import datetime as dt

import backoff as backoff

logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

MINECHAT_HOST = 'minechat.dvmn.org'
MINECHAT_PORT = 5000
HISTORY_FILE = 'chat.txt'


@backoff.on_exception(backoff.expo,
                      (OSError, asyncio.exceptions.CancelledError, asyncio.exceptions.TimeoutError))
async def tcp_echo_client():
    """Считывает сообщения из сайта в консоль"""

    reader, _ = await asyncio.open_connection(
        MINECHAT_HOST, MINECHAT_PORT)

    while data := await reader.readline():

        logger.info(data.decode().replace('\n', ''))  # логируем полученное сообщение

        async with aiofiles.open(HISTORY_FILE, 'a') as f:  # записываем полученное сообщение в файл
            await f.write(f"[{dt.now().strftime('%Y-%m-%d %H:%M')}]{data.decode()}")

if __name__ == '__main__':

    try:
        asyncio.run(tcp_echo_client())
    except KeyboardInterrupt:
        logger.info("Прерываем работу сервера")  # логируем полученное сообщение
