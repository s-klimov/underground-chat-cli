import asyncio
from pathlib import Path
from uuid import UUID

from aiofile import async_open

from common import gui, GUIArgs
from listen_minechat import listen_messages
from sender import submit_message


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

    # https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently
    await asyncio.gather(
        load_history(options.history, messages_queue),
        listen_messages(options.host, options.port, options.history, messages_queue),
    )

    await task1

    if msg := await sending_queue.get():
        task2 = loop.create_task(
            submit_message('minechat.dvmn.org', 5050, UUID('f007e00c-cd77-11ed-ad76-0242ac110002'), msg, sending_queue)
        )

        await task2


if __name__ == '__main__':

    args = GUIArgs()
    options = args.get_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, options))
    loop.close()
