# -*- coding:utf-8 -*-
import asyncio
from io import StringIO, BytesIO

from ..python import Lexer, basic_parse, items

from .data import RAW_DATA, RAW_TOKENS, JSON, JSON_EVENTS
from .server import DemoServer


class with_reader:
    def __init__(self, data):
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.data = data

    async def call_wrapped(self, func, server):
        async with server.get_response() as r:
            stream = r.content
            await func(stream)

    def __call__(self, func):
        loop = asyncio.get_event_loop()
        server = DemoServer(self.data)
        server.start_server(loop)
        try:
            loop.run_until_complete(self.call_wrapped(func, server))
        finally:
            server.stop_server(loop)
            loop.close()


@with_reader(RAW_DATA)
async def test_lexer(stream):
    lex = Lexer(stream, buf_size=10)
    tokens = []
    async for chunk in lex:
        tokens.append(chunk)
    assert len(tokens) == len(RAW_TOKENS)
    assert tokens == RAW_TOKENS


# def test_basic_parse():
#     """
#     Make sure the basic json parsing works
#     TODO: make this async
#     TODO: handle unicode properly
#     """
#     events = list(basic_parse(BytesIO(JSON)))
#     assert events == JSON_EVENTS


# def test_items():
#     """Let's make sure the whole items feed still works"""
#     feed = items(BytesIO(JSON), "docs.item.meta")
#     matches = list(feed)
#     assert len(matches) == 3
#     assert matches[0] == [[1], {}]
#     assert matches[1] == {"key": "value"}
#     assert matches[2] is None
