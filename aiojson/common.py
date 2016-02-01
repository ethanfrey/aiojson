'''
Backend independent higher level interfaces, common exceptions.
'''
import decimal

from .utils.aiogen import aiogen


class JSONError(Exception):
    '''
    Base exception for all parsing errors.
    '''
    pass


class IncompleteJSONError(JSONError):
    '''
    Raised when the parser can't read expected data from a stream.
    '''
    pass


class parse:
    '''
    An iterator returning parsing events with the information about their location
    with the JSON object tree. Events are tuples ``(prefix, type, value)``.

    Available types and values are:

    ('null', None)
    ('boolean', <True or False>)
    ('number', <int or Decimal>)
    ('string', <unicode>)
    ('map_key', <str>)
    ('start_map', None)
    ('end_map', None)
    ('start_array', None)
    ('end_array', None)

    Prefixes represent the path to the nested elements from the root of the JSON
    document. For example, given this document::

        {
          "array": [1, 2],
          "map": {
            "key": "value"
          }
        }

    the parser would yield events:

      ('', 'start_map', None)
      ('', 'map_key', 'array')
      ('array', 'start_array', None)
      ('array.item', 'number', 1)
      ('array.item', 'number', 2)
      ('array', 'end_array', None)
      ('', 'map_key', 'map')
      ('map', 'start_map', None)
      ('map', 'map_key', 'key')
      ('map.key', 'string', u'value')
      ('map', 'end_map', None)
      ('', 'end_map', None)

    '''

    def __init__(self, basic_events):
        self.basic_events = basic_events
        self.path = []

    async def __aiter__(self):
        return self

    async def __anext__(self):
        event, value = await self.basic_events.next()
        if event == 'map_key':
            prefix = '.'.join(self.path[:-1])
            self.path[-1] = value
        elif event == 'start_map':
            prefix = '.'.join(self.path)
            self.path.append(None)
        elif event == 'end_map':
            self.path.pop()
            prefix = '.'.join(self.path)
        elif event == 'start_array':
            prefix = '.'.join(self.path)
            self.path.append('item')
        elif event == 'end_array':
            self.path.pop()
            prefix = '.'.join(self.path)
        else: # any scalar value
            prefix = '.'.join(self.path)

        return (prefix, event, value)

    async def next(self):
        return await self.__anext__()


class ObjectBuilder(object):
    '''
    Incrementally builds an object from JSON parser events. Events are passed
    into the `event` function that accepts two parameters: event type and
    value. The object being built is available at any time from the `value`
    attribute.

    Example::

        from StringIO import StringIO
        from ijson.parse import basic_parse
        from ijson.utils import ObjectBuilder

        builder = ObjectBuilder()
        f = StringIO('{"key": "value"})
        for event, value in basic_parse(f):
            builder.event(event, value)
        print builder.value

    '''
    def __init__(self):
        def initial_set(value):
            self.value = value
        self.containers = [initial_set]

    def event(self, event, value):
        if event == 'map_key':
            self.key = value
        elif event == 'start_map':
            map = {}
            self.containers[-1](map)
            def setter(value):
                map[self.key] = value
            self.containers.append(setter)
        elif event == 'start_array':
            array = []
            self.containers[-1](array)
            self.containers.append(array.append)
        elif event == 'end_array' or event == 'end_map':
            self.containers.pop()
        else:
            self.containers[-1](value)


class items:
    '''
    An iterator returning native Python objects constructed from the events
    under a given prefix.
    '''
    def __init__(self, prefixed_events, prefix):
        self.prefixed_events = prefixed_events
        self.prefix = prefix

    async def __aiter__(self):
        return self

    async def __anext__(self):
        current = None
        # get events til we find one of interest
        while (current != self.prefix):
            current, event, value = await self.prefixed_events.next()
        # now process it
        if event in ('start_map', 'start_array'):
            builder = ObjectBuilder()
            end_event = event.replace('start', 'end')
            while (current, event) != (self.prefix, end_event):
                builder.event(event, value)
                current, event, value = await self.prefixed_events.next()
            return builder.value
        else:
            return value

    async def next(self):
        return await self.__anext__()


def number(str_value):
    '''
    Converts string with a numeric value into an int or a Decimal.
    Used in different backends for consistent number representation.
    '''
    number = decimal.Decimal(str_value)
    int_number = int(number)
    if int_number == number:
        number = int_number
    return number
