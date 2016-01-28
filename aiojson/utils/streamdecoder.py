import codecs


class DecodingStreamReader:
    def __init__(self, stream, encoding='utf-8', errors='strict'):
        self.stream = stream
        self.decoder = codecs.getincrementaldecoder(encoding)(errors=errors)

    async def read(self, n=-1):
        data = await self.stream.read(n)
        if isinstance(data, (bytes, bytearray)):
            data = self.decoder.decode(data)
        return data

    def at_eof(self):
        return self.stream.at_eof()
