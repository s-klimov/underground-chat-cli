import asyncio

MINECHAT_HOST = 'minechat.dvmn.org'
MINECHAT_PORT = 5000


async def tcp_echo_client():
    """считывает сообщения из сайта в консоль"""

    reader, _ = await asyncio.open_connection(
        MINECHAT_HOST, MINECHAT_PORT)

    while data := await reader.readline():
        print(f'Received: {data.decode()!r}')


asyncio.run(tcp_echo_client())
