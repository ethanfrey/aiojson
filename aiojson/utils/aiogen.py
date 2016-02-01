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

    async def _send(self, *args):
        if len(args) == 0:
            raise Exception('Must send some data!')
        elif len(args) == 1:
            # just send the argument through
            data = args[0]
        else:
            # you can send multiple arguments, and they are automatically wrapped into a tuple.
            data = args
        return await self.output.put(data)

    async def run_func(self):
        try:
            # result = await self.func(self._send, *self.args, **self.kwargs)
            result = await self.func(self._send, *self.args, **self.kwargs)
            await self.output.close()
        except Exception as e:
            print('passing exception')
            await self.output.put(e)

    async def __aiter__(self):
        # make it idempotent
        if self.output is not None:
            return
        self.output = Channel()
        self.task = asyncio.ensure_future(self.run_func())
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

