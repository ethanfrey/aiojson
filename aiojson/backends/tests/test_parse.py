from aiojson.backends.python import Buffer, get_tokens, Lexer
try:
    from io import StringIO
except:
    from StringIO import StringIO


DATA1 = u'{"name": "string", "age": 42, "weight": 19.4, "list": [5, "b", 17, {"foo": "bar"}]}'

TOKENS1 = [(0, u'{'), (1, u'"name"'), (7, u':'), (9, u'"string"'), (17, u','), (19, u'"age"'), (24, u':'), (26, u'42'),
           (28, u','), (30, u'"weight"'), (38, u':'), (40, u'19.4'), (44, u','), (46, u'"list"'), (52, u':'),
           (54, u'['), (55, u'5'), (56, u','), (58, u'"b"'), (61, u','), (63, u'17'), (65, u','),
           (67, u'{'), (68, u'"foo"'), (73, u':'), (75, u'"bar"'), (80, u'}'), (81, u']'), (82, u'}')]


def test_lexer():
    buf = StringIO(DATA1)
    lex = Lexer(buf)
    tokens = list(lex)
    assert len(tokens) == len(TOKENS1)
    assert tokens == TOKENS1


def test_get_tokens_all():
    buf = Buffer(DATA1)
    parser = get_tokens(buf)
    tokens = list(parser)
    assert len(tokens) == len(TOKENS1)
    assert tokens == TOKENS1

