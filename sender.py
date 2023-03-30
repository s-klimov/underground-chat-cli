import asyncio
import backoff as backoff

from common import cancelled_handler, logger, WriteArgs

logger.name = "SENDER"


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
    logger.debug(account_hash)
    writer.write(f"{account_hash}\n".encode())
    await writer.drain()

    # Приветствуем участников чата
    logger.debug(message)
    writer.writelines([f"{message}\n".encode(), '\n'.encode()])
    await writer.drain()

    logger.debug('Close the connection')
    writer.close()
    await writer.wait_closed()


if __name__ == '__main__':

    args = WriteArgs()
    options = args.get_args()

    message = input('Что напишем в чат: ').strip()

    try:
        asyncio.run(write_messages(options.host, options.port, options.account, message))
    except KeyboardInterrupt:
        pass
    finally:
        logger.info('Работа сервера остановлена')
