import asyncio
import logging
import re
from pathlib import Path

from aiofile import async_open

from common import gui, GUIArgs, Authorise
from common.common import InvalidToken
from listen_minechat import listen_messages


async def load_history(filepath: str, messages_queue: asyncio.Queue):

    if not Path(filepath).is_file():
        return

    async with async_open(filepath) as f:
        while message := await f.readline():
            messages_queue.put_nowait(message.rstrip())


async def main(loop, options):

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    # https://docs.python.org/3/library/asyncio-task.html#coroutines
    task1 = loop.create_task(gui.draw(messages_queue, sending_queue, status_updates_queue))

    async with Authorise(account=options.account, minechat_host=options.host, minechat_port=5050, queue=status_updates_queue) as (_, writer):

        # https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently
        await asyncio.gather(
            load_history(options.history, messages_queue),
            listen_messages(options.host, options.port, options.history, messages_queue),
            send_messages(sending_queue, writer),
        )

        await task1


async def send_messages(queue, writer):

    while message := await queue.get():
        message_line = ''.join([re.sub(r'\\n', ' ', message), '\n']).encode()
        line_feed = '\n'.encode()

        writer.writelines([message_line, line_feed])
        await writer.drain()


if __name__ == '__main__':

    args = GUIArgs()
    options = args.get_args()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(loop, options))
    except InvalidToken as e:
        logging.error(str(e))
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
        logging.info('Работа сервера остановлена')
