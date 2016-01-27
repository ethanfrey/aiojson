# -*- coding:utf-8 -*-
from aiojson.backends.python import Buffer, get_tokens

from .data import RAW_DATA, RAW_TOKENS


def test_get_tokens_all():
    buf = Buffer(RAW_DATA)
    parser = get_tokens(buf, more_data=False)
    tokens = list(parser)
    assert len(tokens) == len(RAW_TOKENS)
    assert tokens == RAW_TOKENS


def test_get_tokens_chunks_split_in_spaces():
    chunk1 = RAW_DATA[:30]
    chunk2 = RAW_DATA[30:]
    validate_get_tokens_reentrant(Buffer(chunk1), Buffer(chunk2))


def test_get_tokens_chunks_split_in_string():
    chunk1 = RAW_DATA[:35]
    chunk2 = RAW_DATA[35:]
    validate_get_tokens_reentrant(Buffer(chunk1), Buffer(chunk2))


def test_get_tokens_chunks_split_in_number():
    chunk1 = RAW_DATA[:42]
    chunk2 = RAW_DATA[42:]
    validate_get_tokens_reentrant(Buffer(chunk1), Buffer(chunk2))


def validate_get_tokens_reentrant(*buffers):
    tokens = []
    buffer = Buffer('')
    for b in buffers:
        buffer = buffer + b
        tokens += list(get_tokens(buffer))
    tokens += list(get_tokens(buffer, False))
    unfinished = buffer.search()
    assert not unfinished
    assert len(tokens) == len(RAW_TOKENS)
    assert tokens == RAW_TOKENS
