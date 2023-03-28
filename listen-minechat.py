import asyncio
import logging.config
import os

import aiofiles as aiofiles
from datetime import datetime as dt

import backoff as backoff
import configargparse as configargparse

from dotenv import load_dotenv
load_dotenv()  # подгружаем переменные окружения из .env

logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def cancelled_handler(e) -> None:
    """Обработчик для исключения asyncio.exceptions.CancelledError"""

    logger.info("Прерываем работу сервера")  # логируем полученное сообщение
    raise


@backoff.on_exception(backoff.expo,
                      asyncio.exceptions.CancelledError,
                      raise_on_giveup=False,
                      giveup=cancelled_handler)
@backoff.on_exception(backoff.expo,
                      (OSError, asyncio.exceptions.TimeoutError))
async def tcp_echo_client(minechat_host: str, minechat_port: 'int > 0', minechat_history_file: str) -> None:
    """Считывает сообщения из сайта в консоль"""

    reader, _ = await asyncio.open_connection(minechat_host, minechat_port)

    while data := await reader.readline():

        logger.info(data.decode().replace('\n', ''))  # логируем полученное сообщение

        async with aiofiles.open(minechat_history_file, 'a') as f:  # записываем полученное сообщение в файл
            await f.write(f"[{dt.now().strftime('%Y-%m-%d %H:%M')}]{data.decode()}")


def get_args() -> [str, int, str]:
    """Достает для проекта значения параметров командной строки"""

    p = configargparse.ArgParser(default_config_files=['.env', ])
    p.add('--host', type=str, required=False, default=os.getenv('host'),
          help='Хост сервера с чатом (default: %(default)s)')

    # parser = argparse.ArgumentParser(description='Подключаемся к подпольному чату')

    p.add('--port', type=int, required=False, default=os.getenv('port'),
          help='Порт сервера с чатом (default: %(default)s)')
    p.add('--history', type=str, required=False, default=os.getenv('history'),
          help='Файл для хранения истории чата (default: %(default)s)')

    options = p.parse_args()
    return options.host, options.port, options.history


if __name__ == '__main__':

    host, port, history_file = get_args()

    try:
        asyncio.run(tcp_echo_client(host, port, history_file))
    except KeyboardInterrupt:
        pass
    finally:
        logger.error('Работа сервера остановлена')
