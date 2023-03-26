import asyncio


async def tcp_echo_client(message):


    reader, _ = await asyncio.open_connection(
        'minechat.dvmn.org', 5000)

    while data := await reader.readline():
        print(f'Received: {data.decode()!r}')


asyncio.run(tcp_echo_client('Hello World!'))