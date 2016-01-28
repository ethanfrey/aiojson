# -*- coding:utf-8 -*-
import asyncio

from ..python import Lexer, basic_parse, items

from .data import *
from .server import with_reader


@with_reader(RAW_DATA)
async def test_lexer(stream):
    lex = Lexer(stream, buf_size=10)
    tokens = []
    async for chunk in lex:
        tokens.append(chunk)
    assert len(tokens) == len(RAW_TOKENS)
    assert tokens == RAW_TOKENS


@with_reader(SIMPLE_JSON)
async def test_basic_parse_simple(stream):
    """
    Make sure the basic json parsing works, using async streams
    """
    events = []
    async for evt in basic_parse(stream):
        events.append(evt)
    assert len(events) == len(SIMPLE_EVENTS)
    assert events == SIMPLE_EVENTS


@with_reader(ARRAY_JSON)
async def test_basic_parse_array(stream):
    """
    Make sure the basic json parsing works, using async streams
    """
    events = []
    async for evt in basic_parse(stream):
        events.append(evt)
    assert len(events) == len(ARRAY_EVENTS)
    assert events == ARRAY_EVENTS


@with_reader(SIMPLE_MAP_JSON)
async def test_basic_parse_simple_map(stream):
    """
    Make sure the basic json parsing works, using async streams
    """
    events = []
    async for evt in basic_parse(stream):
        events.append(evt)
    assert len(events) == len(SIMPLE_MAP_EVENTS)
    assert events == SIMPLE_MAP_EVENTS


# @with_reader(MAP_JSON)
# async def test_basic_parse_map(stream):
#     """
#     Make sure the basic json parsing works, using async streams
#     """
#     events = []
#     async for evt in basic_parse(stream):
#         events.append(evt)
#     assert len(events) == len(MAP_EVENTS)
#     assert events == MAP_EVENTS

# def test_items():
#     """Let's make sure the whole items feed still works"""
#     feed = items(BytesIO(JSON), "docs.item.meta")
#     matches = list(feed)
#     assert len(matches) == 3
#     assert matches[0] == [[1], {}]
#     assert matches[1] == {"key": "value"}
#     assert matches[2] is None
