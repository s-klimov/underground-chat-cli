import asyncio
import time

from common import gui, GUIArgs


async def generate_msgs(messages_queue):
    while True:
        messages_queue.put_nowait("Ping %d" % time.time())
        await asyncio.sleep(1)


async def main(loop):

    messages_queue = asyncio.Queue()
    sending_queue = asyncio.Queue()
    status_updates_queue = asyncio.Queue()

    # https://docs.python.org/3/library/asyncio-task.html#coroutines
    task1 = loop.create_task(gui.draw(messages_queue, sending_queue, status_updates_queue))

    # https://docs.python.org/3/library/asyncio-task.html#running-tasks-concurrently
    await asyncio.gather(
        generate_msgs(messages_queue),
    )

    await task1


if __name__ == '__main__':

    args = GUIArgs()
    options = args.get_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
