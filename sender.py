import asyncio
import json

import aiofiles
import backoff as backoff

from common import cancelled_handler, logger, WriteArgs

logger.name = "SENDER"
USERS_FILE = "users.json"


async def register(minechat_host: str, minechat_port: 'int > 0', user_name: str) -> None:
    """Регистрирует пользователя на сервере"""
    reader, writer = await asyncio.open_connection(minechat_host, minechat_port)

    await reader.readline()  # пропускаем строку-приглашение ввода хэша аккаунта
    writer.write("\n".encode())  # вводим пустую строку, чтобы получить приглашение для регистрации
    await writer.drain()
    await reader.readline()  # пропускаем строку-приглашение ввода имени пользователя
    writer.write(f"{user_name}\n".encode())
    await writer.drain()
    response = await reader.readline()  # получаем результат регистрации

    user = json.loads(response)
    try:
        if json.loads(response) is None:  # Если результат аутентификации null, то прекращаем выполнение скрипта
            raise ValueError(f'Ошибка регистрации пользователя. Ответ сервера {response}')
        logger.debug(f'Пользователь {user} зарегистрирован')

    except ValueError as e:
        logger.debug(str(e))
    else:
        async with aiofiles.open(USERS_FILE, 'a') as f:  # записываем полученное сообщение в файл
            await f.write(json.dumps(user) + '\n')


@backoff.on_exception(backoff.expo,
                      asyncio.exceptions.CancelledError,
                      raise_on_giveup=False,
                      giveup=cancelled_handler)
@backoff.on_exception(backoff.expo,
                      (OSError, asyncio.exceptions.TimeoutError))
async def write_messages(minechat_host: str, minechat_port: 'int > 0', account_hash: str, message: str) -> None:
    """Считывает сообщения из сайта в консоль"""

    reader, writer = await asyncio.open_connection(minechat_host, minechat_port)

    # сначала логинимся в чате
    await reader.readline()  # пропускаем строку-приглашение
    logger.debug(account_hash)
    writer.write(f"{account_hash}\n".encode())
    await writer.drain()
    response = await reader.readline()  # получаем результат аутентификации

    try:
        if json.loads(response) is None:  # Если результат аутентификации null, то прекращаем выполнение скрипта
            raise ValueError('Неизвестный токен. Проверьте его или зарегистрируйте заново.')

        # Приветствуем участников чата
        logger.debug(message)
        writer.writelines([f"{message}\n".encode(), '\n'.encode()])
        await writer.drain()

    except ValueError as e:
        logger.debug(str(e))

    finally:
        logger.debug('Закрываем соединение')
        writer.close()
        await writer.wait_closed()


if __name__ == '__main__':

    args = WriteArgs()
    options = args.get_args()

    try:
        if options.register:
            asyncio.run(register(options.host, options.port, options.register))
        else:
            message = input('Что напишем в чат: ').strip()
            asyncio.run(write_messages(options.host, options.port, options.account, message))
    except KeyboardInterrupt:
        pass
    finally:
        logger.info('Работа сервера остановлена')
