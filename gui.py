import asyncio
import time
from pathlib import Path

from aiofile import async_open

from common import gui, GUIArgs, ListenArgs
from listen_minechat import listen_messages


async def load_history(filepath: str, messages_queue: asyncio.Queue):

    if not Path(filepath).is_file():
        return

    async with async_open(filepath) as f:
        while message := await f.readline():
            messages_queue.put_nowait(message.rstrip())
            # await asyncio.sleep(0)


async def main(loop, options):

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    # https://docs.python.org/3/library/asyncio-task.html#coroutines
    task1 = loop.create_task(gui.draw(messages_queue, sending_queue, status_updates_queue))

    # https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently
    await asyncio.gather(
        load_history(options.history, messages_queue),
        listen_messages(options.host, options.port, options.history, messages_queue),
    )

    await task1


if __name__ == '__main__':

    args = ListenArgs()
    options = args.get_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, options))
    loop.close()
