import asyncio
import logging.config

logging.config.fileConfig('logging.ini', disable_existing_loggers=False)
logger = logging.getLogger(__name__)

MINECHAT_HOST = 'minechat.dvmn.org'
MINECHAT_PORT = 5000


async def tcp_echo_client():
    """считывает сообщения из сайта в консоль"""

    reader, _ = await asyncio.open_connection(
        MINECHAT_HOST, MINECHAT_PORT)

    while data := await reader.readline():
        logger.info(data.decode().replace('\n', ''))


asyncio.run(tcp_echo_client())
