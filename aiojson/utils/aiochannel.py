from asyncio import Queue


class ChannelClosed(Exception):
    pass


class Channel(Queue):
    DONE_SYMBOL = object()

    async def close(self):
        return await self.put(self.DONE_SYMBOL)

    async def get(self):
        result = await super().get()
        if result == self.DONE_SYMBOL:
            raise ChannelClosed()
        elif isinstance(result, Exception):
            # pass errors down the pipeline...
            raise result
        else:
            return result
