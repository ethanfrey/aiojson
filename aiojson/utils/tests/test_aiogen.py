import asyncio

from ..aiogen import aiogen


@aiogen
async def fact(send, n):
    print('Starting fact')
    total = 1
    for i in range(1, n+1):
        total *= i
        await send(total)
        print('sent', total)
        asyncio.sleep(0.01)


async def fact_consume(n):
    print('starting consume')
    total = 0
    async for value in fact(n):
        print('got', value)
        total += value
    return total


def test_fact():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(fact_consume(4))
    assert result == 1 + 2 + 6 + 24
