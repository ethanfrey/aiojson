import asyncio

from .aiochannel import Channel, ChannelClosed


class aiogen:
    """
    To simulate the use of yield in async functions, to make an easy generator
    Wraps a method and makes it iterable via (async for ...)
    """

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        iterator = agenerator(self.func, *args, **kwargs)
        return iterator


class agenerator:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.output = None

    async def run_func(self):
        try:
            print('about to call self.func')
            result = await self.func(self.output.put, *self.args, **self.kwargs)
            print('done, closing channel')
            await self.output.close()
        except Exception as e:
            print('passing exception')
            await self.output.put(e)

    async def __aiter__(self):
        # make it re-entrant
        if self.output is not None:
            return
        self.output = Channel()
        self.task = asyncio.ensure_future(self.run_func())
        print('started task')
        return self

    async def __anext__(self):
        try:
            return await self.output.get()
        except ChannelClosed:
            raise StopAsyncIteration()

    async def next(self):
        if self.output is None:
            await self.__aiter__()
        return await self.__anext__()

