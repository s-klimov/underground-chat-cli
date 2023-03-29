import asyncio
import backoff as backoff

from common import get_args, cancelled_handler, logger


@backoff.on_exception(backoff.expo,
                      asyncio.exceptions.CancelledError,
                      raise_on_giveup=False,
                      giveup=cancelled_handler)
@backoff.on_exception(backoff.expo,
                      (OSError, asyncio.exceptions.TimeoutError))
async def write_messages(minechat_host: str, minechat_port: 'int > 0', account_hash: str, message: str) -> None:
    """Считывает сообщения из сайта в консоль"""

    _, writer = await asyncio.open_connection(minechat_host, minechat_port)

    # сначала логинимся в чате
    logger.info(f'Send: {account_hash!r}')
    writer.write(f"{account_hash}\n".encode())
    await writer.drain()

    # Приветствуем участников чата
    logger.info(f'Send: {message!r}')
    writer.writelines([f"{message}\n".encode(), '\n'.encode()])
    await writer.drain()

    logger.info('Close the connection')
    writer.close()
    await writer.wait_closed()


if __name__ == '__main__':

    host, port, _, account_hash = get_args()

    message = input('Что напишем в чат: ').strip()

    try:
        asyncio.run(write_messages(host, port, account_hash, message))
    except KeyboardInterrupt:
        pass
    finally:
        logger.error('Работа сервера остановлена')
