
'''
Pure-python parsing backend.
'''
import decimal
import re

from .. import common
from ..utils.aiogen import aiogen

BUFSIZE = 16 * 1024


class UnexpectedSymbol(common.JSONError):
    def __init__(self, symbol, pos):
        super(UnexpectedSymbol, self).__init__(
            'Unexpected symbol %r at %d' % (symbol, pos)
        )


class Buffer(object):
    LEXEME_RE = re.compile(r'[a-z0-9eE\.\+-]+|\S')

    def __init__(self, buf):
        self.buf = buf
        self.pos = 0
        self.discarded = 0

    def search(self):
        return self.LEXEME_RE.search(self.buf, self.pos)

    def index(self, query, start):
        return self.buf.index(query, start)

    def global_pos(self, offset):
        return self.discarded + offset

    def __len__(self):
        return len(self.buf)

    def __add__(self, new_buf):
        if not self.search():
            # nothing left in this buffer, we take the new buffer, noting offset
            new_buf.discarded = self.discarded + len(self.buf)
            return new_buf
        else:
            # TODO: do this more intelligently, dropping everything before pos
            # we need to combine the two buffers
            self.buf += new_buf.buf
            return self


def get_tokens(buffer, more_data=True):
    """
    This takes a buffer and returns an iterator on it, to returns complete
    lexical tokens one at a time.  Iterator stops when there are no more
    clear-cut lexical tokens. If the buffer ends where it could be the
    middle of a token, or the end (ex. " 19"), it will return without that
    token, waiting for more data to be present.  However, if this is really
    the last available data chunk, set more_data=False, and it will be
    more greedy about matching.

    This is to ensure two chunks cut, such as " 19" and ".4" are properly
    parsed as "19.4", not two distinct tokens "19" and ".4".
    """
    while True:
        match = buffer.search()
        if match:
            lexeme = match.group()
            if lexeme == '"':
                pos = match.start()
                start = pos + 1
                while True:
                    try:
                        end = buffer.index('"', start)
                        escpos = end - 1
                        while buffer.buf[escpos] == '\\':
                            escpos -= 1
                        if (end - escpos) % 2 == 0:
                            start = end + 1
                        else:
                            break
                    except ValueError:
                        return
                yield buffer.global_pos(pos), buffer.buf[pos:end + 1]
                buffer.pos = end + 1
            else:
                if more_data and (match.end() == len(buffer)):
                    return
                buffer.pos = match.end()
                yield buffer.global_pos(match.start()), lexeme
        else:
            return


class Lexer(object):
    """
    This takes a stream and can be used to iterator over lexical tokens from it.
    Uses Buffer and get_token to do the work on the in-memory data, and handles
    combining multiple data chunks from the network.
    """

    def __init__(self, stream, buf_size=BUFSIZE):
        self.stream = stream
        self.buf_size = buf_size
        self.stream_done = False
        self.buffer = None

    async def read_buffer(self):
        # TODO: this breaks if a utf-8 character is split in the middle of a chunk boundary
        # Need a good asyncio solution here.
        data = await self.stream.read(self.buf_size)
        if isinstance(data, (bytes, bytearray)):
            data = data.decode('utf-8')
        return Buffer(data)

    async def __aiter__(self):
        # __iter__ may be called multiple times on one object, just initialize once
        if self.buffer is None:
            self.buffer = await self.read_buffer()
            self.parser = get_tokens(self.buffer)
        return self

    async def next(self):
        # Make sure we set up the iterator once if people are calling by hand
        try:
            if self.buffer is None:
                await self.__aiter__()
            return await self.__anext__()
        except StopIteration:
            import pdb; pdb.set_trace()

    def _check_end(self):
        if self.buffer.search():
            raise common.IncompleteJSONError('Incomplete string lexeme')
        else:
            raise StopAsyncIteration

    async def __anext__(self):
        # if we hit the end of the parsing on the last call, then we must successfully finish
        # or die with the error that the json doesn't close properly
        if self.stream_done:
            self._check_end()
        try:
            return next(self.parser)
        except StopIteration:
            # try to get more data
            more_data = await self.read_buffer()
            if len(more_data) > 0:
                self.buffer = self.buffer + more_data
                self.parser = get_tokens(self.buffer)
                return await self.next()
            else:
                self.stream_done = True
                try:
                    return next(get_tokens(self.buffer, more_data=False))
                except StopIteration:
                    self._check_end()


def unescape(s):
    start = 0
    result = ''
    while start < len(s):
        pos = s.find('\\', start)
        if pos == -1:
            if start == 0:
                return s
            result += s[start:]
            break
        result += s[start:pos]
        pos += 1
        esc = s[pos]
        if esc == 'u':
            result += chr(int(s[pos + 1:pos + 5], 16))
            pos += 4
        elif esc == 'b':
            result += '\b'
        elif esc == 'f':
            result += '\f'
        elif esc == 'n':
            result += '\n'
        elif esc == 'r':
            result += '\r'
        elif esc == 't':
            result += '\t'
        else:
            result += esc
        start = pos + 1
    return result


class parse_value:
    def __init__(self, lexer, symbol=None, pos=0):
        self.lexer = lexer
        self.symbol = symbol
        self.pos = pos
        self.done = False
        self.sub_parser = None

    async def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.symbol:
            self.pos, self.symbol = await self.lexer.next()

        if self.done:
            raise StopAsyncIteration
        try:
            if self.sub_parser:
                return await self.sub_parser.next()
            if self.symbol == 'null':
                self.done = True
                return ('null', None)
            elif self.symbol == 'true':
                self.done = True
                return ('boolean', True)
            elif self.symbol == 'false':
                self.done = True
                return ('boolean', False)
            elif self.symbol == '[':
                self.sub_parser = parse_array(self.lexer)
                return ('start_array', None)
            elif self.symbol == '{':
                self.sub_parser = parse_object(self.lexer)
                return ('start_map', None)
            elif self.symbol[0] == '"':
                self.done = True
                return ('string', unescape(self.symbol[1:-1]))
            else:
                try:
                    self.done = True
                    return ('number', common.number(self.symbol))
                except decimal.InvalidOperation:
                    raise UnexpectedSymbol(self.symbol, self.pos)
        except StopIteration:
            raise common.IncompleteJSONError('Incomplete JSON data')

    async def next(self):
        # Make sure we set up the iterator once if people are calling by hand
        return await self.__anext__()


@aiogen
async def parse_array(send, lexer):
    try:
        pos, symbol = await lexer.next()
        if symbol != ']':
            while True:
                async for event in parse_value(lexer, symbol, pos):
                    await send(event)
                pos, symbol = await lexer.next()
                if symbol == ']':
                    break
                if symbol != ',':
                    raise UnexpectedSymbol(symbol, pos)
                pos, symbol = await lexer.next()
        await send('end_array', None)
    except StopIteration:
        raise common.IncompleteJSONError('Incomplete JSON data')


@aiogen
async def parse_object(send, lexer):
    try:
        pos, symbol = await lexer.next()
        if symbol != '}':
            while True:
                if symbol[0] != '"':
                    raise UnexpectedSymbol(symbol, pos)
                await send(('map_key', unescape(symbol[1:-1])))
                pos, symbol = await lexer.next()
                if symbol != ':':
                    raise UnexpectedSymbol(symbol, pos)
                async for event in parse_value(lexer, None, pos):
                    await send(event)
                pos, symbol = await lexer.next()
                if symbol == '}':
                    break
                if symbol != ',':
                    raise UnexpectedSymbol(symbol, pos)
                pos, symbol = await lexer.next()
        await send(('end_map', None))
    except StopAsyncIteration:
        raise common.IncompleteJSONError('Incomplete JSON data')


class basic_parse:
    '''
    Iterator yielding unprefixed events.

    Parameters:

    - stream: an asyncio stream with JSON input
    '''
    def __init__(self, stream, buf_size=BUFSIZE):
        self.stream = stream
        self.buf_size = buf_size
        self.lexer = None
        self.parser = None

    async def __aiter__(self):
        if self.lexer is None:
            self.lexer = await Lexer(self.stream, self.buf_size).__aiter__()
            self.parser = parse_value(self.lexer)
        return self

    async def __anext__(self):
        try:
            value = await self.parser.next()
            return value
        except StopAsyncIteration:
            # go to the next value
            self.parser = parse_value(self.lexer)
            # if next also fails, then we are at the end...
            return await self.parser.next()

    async def next(self):
        # Make sure we set up the iterator once if people are calling by hand
        if self.lexer is None:
            await self.__aiter__()
        return await self.__anext__()


def parse(stream, buf_size=BUFSIZE):
    '''
    Backend-specific wrapper for ijson.common.parse.
    '''
    return common.parse(basic_parse(stream, buf_size=buf_size))


def items(stream, prefix):
    '''
    Backend-specific wrapper for ijson.common.items.
    '''
    return common.items(parse(stream), prefix)
