
'''
Pure-python parsing backend.
'''
# import asyncio
import decimal
import re

# TODO: codecs???
from codecs import getreader
from ijson.compat import chr, bytetype
from aiojson import common


BUFSIZE = 16 * 1024
LEXEME_RE = re.compile(r'[a-z0-9eE\.\+-]+|\S')


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

    def read_buffer(self):
        data = self.stream.read(self.buf_size)
        return Buffer(data)

    def __iter__(self):
        # __iter__ may be called multiple times on one object, just initialize once
        if not self.buffer:
            if type(self.stream.read(0)) == bytetype:
                self.stream = getreader('utf-8')(self.stream)
            self.buffer = self.read_buffer()
            self.parser = get_tokens(self.buffer)
        return self

    def next(self):
        return self.__next__()

    def __next__(self):
        # if we hit the end of the parsing on the last call, then we must successfully finish
        # or die with the error that the json doesn't close properly
        if self.stream_done:
            if self.buffer.search():
                raise common.IncompleteJSONError('Incomplete string lexeme')
            else:
                raise StopIteration()

        try:
            return next(self.parser)
        except StopIteration:
            # try to get more data
            more_data = self.read_buffer()
            if len(more_data) > 0:
                self.buffer = self.buffer + more_data
                self.parser = get_tokens(self.buffer)
                return next(self)
            else:
                self.stream_done = True
                return next(get_tokens(self.buffer, more_data=False))


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


def parse_value(lexer, symbol=None, pos=0):
    try:
        if symbol is None:
            pos, symbol = next(lexer)
        if symbol == 'null':
            yield ('null', None)
        elif symbol == 'true':
            yield ('boolean', True)
        elif symbol == 'false':
            yield ('boolean', False)
        elif symbol == '[':
            for event in parse_array(lexer):
                yield event
        elif symbol == '{':
            for event in parse_object(lexer):
                yield event
        elif symbol[0] == '"':
            try:
                yield ('string', unescape(symbol[1:-1]))
            except Exception as e:
                import pdb; pdb.set_trace()
        else:
            try:
                yield ('number', common.number(symbol))
            except decimal.InvalidOperation:
                raise UnexpectedSymbol(symbol, pos)
    except StopIteration:
        raise common.IncompleteJSONError('Incomplete JSON data')


def parse_array(lexer):
    yield ('start_array', None)
    try:
        pos, symbol = next(lexer)
        if symbol != ']':
            while True:
                for event in parse_value(lexer, symbol, pos):
                    yield event
                pos, symbol = next(lexer)
                if symbol == ']':
                    break
                if symbol != ',':
                    raise UnexpectedSymbol(symbol, pos)
                pos, symbol = next(lexer)
        yield ('end_array', None)
    except StopIteration:
        raise common.IncompleteJSONError('Incomplete JSON data')


def parse_object(lexer):
    yield ('start_map', None)
    try:
        pos, symbol = next(lexer)
        if symbol != '}':
            while True:
                if symbol[0] != '"':
                    raise UnexpectedSymbol(symbol, pos)
                yield ('map_key', unescape(symbol[1:-1]))
                pos, symbol = next(lexer)
                if symbol != ':':
                    raise UnexpectedSymbol(symbol, pos)
                for event in parse_value(lexer, None, pos):
                    yield event
                pos, symbol = next(lexer)
                if symbol == '}':
                    break
                if symbol != ',':
                    raise UnexpectedSymbol(symbol, pos)
                pos, symbol = next(lexer)
        yield ('end_map', None)
    except StopIteration:
        raise common.IncompleteJSONError('Incomplete JSON data')


def basic_parse(file, buf_size=BUFSIZE):
    '''
    Iterator yielding unprefixed events.

    Parameters:

    - file: a readable file-like object with JSON input
    '''
    lexer = iter(Lexer(file, buf_size))
    for value in parse_value(lexer):
        yield value
    try:
        next(lexer)
    except StopIteration:
        pass
    else:
        raise common.JSONError('Additional data')


def parse(file, buf_size=BUFSIZE):
    '''
    Backend-specific wrapper for ijson.common.parse.
    '''
    return common.parse(basic_parse(file, buf_size=buf_size))


def items(file, prefix):
    '''
    Backend-specific wrapper for ijson.common.items.
    '''
    return common.items(parse(file), prefix)
