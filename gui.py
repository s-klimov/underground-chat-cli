import asyncio
import logging
from pathlib import Path

from aiofile import async_open
from anyio import create_task_group

from common import drawing, options
from common.etc import InvalidToken, watch_for_connection
from common.sending import send_messages
from common.listen_minechat import listen_messages


async def load_history(messages_queue: asyncio.Queue):

    if not Path(options.history).is_file():
        return

    async with async_open(options.history) as f:
        while message := await f.readline():
            messages_queue.put_nowait(message.rstrip())


async def main(loop):

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_queue = asyncio.Queue()
    watchdog_queue = asyncio.Queue()

    async with create_task_group() as tg:
        tg.start_soon(drawing.draw, messages_queue, sending_queue, status_queue)
        tg.start_soon(load_history, messages_queue)
        tg.start_soon(listen_messages, messages_queue, watchdog_queue, status_queue)
        tg.start_soon(send_messages, sending_queue, watchdog_queue, status_queue)
        tg.start_soon(watch_for_connection, watchdog_queue, status_queue)


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(loop))
    except InvalidToken as e:
        logging.error(str(e))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
        logging.info('Работа сервера остановлена')
