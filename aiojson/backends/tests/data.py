# -*- coding:utf-8 -*-
from decimal import Decimal


RAW_DATA = u'{"name": "string", "age": 42, "weight": 19.4, "list": [5, "b", 17, {"foo": "bar"}]}'

RAW_TOKENS = [(0, u'{'), (1, u'"name"'), (7, u':'), (9, u'"string"'), (17, u','), (19, u'"age"'), (24, u':'), (26, u'42'),
              (28, u','), (30, u'"weight"'), (38, u':'), (40, u'19.4'), (44, u','), (46, u'"list"'), (52, u':'),
              (54, u'['), (55, u'5'), (56, u','), (58, u'"b"'), (61, u','), (63, u'17'), (65, u','),
              (67, u'{'), (68, u'"foo"'), (73, u':'), (75, u'"bar"'), (80, u'}'), (81, u']'), (82, u'}')]

SIMPLE_JSON = '"hello" 45 true'

SIMPLE_EVENTS = [('string', 'hello'), ('number', 45), ('boolean', True)]

ARRAY_JSON = '[1, "is", false, 2]'

ARRAY_EVENTS = [('start_array', None), ('number', 1), ('string', 'is'), ('boolean', False), ('number', 2), ('end_array', None)]


MAP_JSON = b'''
{
  "docs": [
    {
      "null": null,
      "boolean": false,
      "true": true,
      "integer": 0,
      "double": 0.5,
      "exponent": 1.0e+2,
      "long": 10000000000,
      "string": "\\u0441\\u0442\\u0440\\u043e\\u043a\\u0430 - \xd1\x82\xd0\xb5\xd1\x81\xd1\x82"
    },
    {
      "meta": [[1], {}]
    },
    {
      "meta": {"key": "value"}
    },
    {
      "meta": null
    }
  ]
}
'''
MAP_EVENTS = [
    ('start_map', None),
        ('map_key', 'docs'),
        ('start_array', None),
            ('start_map', None),
                ('map_key', 'null'),
                ('null', None),
                ('map_key', 'boolean'),
                ('boolean', False),
                ('map_key', 'true'),
                ('boolean', True),
                ('map_key', 'integer'),
                ('number', 0),
                ('map_key', 'double'),
                ('number', Decimal('0.5')),
                ('map_key', 'exponent'),
                ('number', 100),
                ('map_key', 'long'),
                ('number', 10000000000),
                ('map_key', 'string'),
                ('string', 'строка - тест'),
            ('end_map', None),
            ('start_map', None),
                ('map_key', 'meta'),
                ('start_array', None),
                    ('start_array', None),
                        ('number', 1),
                    ('end_array', None),
                    ('start_map', None),
                    ('end_map', None),
                ('end_array', None),
            ('end_map', None),
            ('start_map', None),
                ('map_key', 'meta'),
                ('start_map', None),
                    ('map_key', 'key'),
                    ('string', 'value'),
                ('end_map', None),
            ('end_map', None),
            ('start_map', None),
                ('map_key', 'meta'),
                ('null', None),
            ('end_map', None),
        ('end_array', None),
    ('end_map', None),
]
