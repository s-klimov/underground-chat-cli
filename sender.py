import asyncio
import re
import uuid

import backoff as backoff

from common import cancelled_handler, logger, WriteArgs, Authorise, Register

logger.name = "SENDER"


@backoff.on_exception(backoff.expo,
                      asyncio.exceptions.CancelledError,
                      raise_on_giveup=False,
                      giveup=cancelled_handler)
@backoff.on_exception(backoff.expo,
                      (OSError, asyncio.exceptions.TimeoutError),
                      max_tries=3)
async def submit_message(minechat_host: str, minechat_port: 'int >0', account: uuid.UUID | str, message: str) -> None:
    """Считывает сообщения из сайта в консоль
    params:
    minechat_host -- хост сервера с чатом
    minechat_port -- порт сервера с чатом
    account -- строка для регистрации или авторизации пользователя
    """

    message_line = ''.join([re.sub(r'\\n', ' ', message), '\n']).encode()
    line_feed = '\n'.encode()

    # Если на вход получена информация об аккаунте в виде UUID, то интерпретируем её как хэш аккаунта
    # Если на вход получена информация об аккаунте в виде строки, то интерпретируем её как имя пользователя
    # для регистрации в в чате
    if isinstance(account, uuid.UUID):
        action = Authorise
    elif isinstance(account, str):
        action = Register
    elif account is None:
        raise ValueError('Не получены хэш аккаунта или имя для регистрации')
    else:
        raise SyntaxError('Ошибка кода программы, обратитесь к разработчику')

    async with action(account=account, minechat_host=minechat_host, minechat_port=minechat_port) as (_, writer):
        writer.writelines([message_line, line_feed])
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
