=====
aiojson
=====

Aiojson is a slightly-modified version of the wonderful ijson library to work with
asyncio.  I couldn't see how to support python 2.x and sync functions in the same
codebase, and needed this power for a project, so I made a new project here.
However, I give many, many thanks to the `ijson project <https://github.com/isagalaev/ijson>`_

The full power of iterative parsing of partially downloaded json streams really shines
when coupled with asyncio.  Full json parsing with no blocking, and ability to
process chunks of infinite streams of json objects (aka websockets).


Usage
=====

All usage example will be using a JSON document describing geographical
objects::

    {
      "earth": {
        "europe": [
          {"name": "Paris", "type": "city", "info": { ... }},
          {"name": "Thames", "type": "river", "info": { ... }},
          // ...
        ],
        "america": [
          {"name": "Texas", "type": "state", "info": { ... }},
          // ...
        ]
      }
    }

Most common usage is having ijson yield native Python objects out of a JSON
stream located under a prefix. Here's how to process all European cities::

    import aiojson
    import aiohttp

    f = aiohttp.request('GET', 'http://.../')
    objects = aiojson.items(f, 'earth.europe.item')
    async for obj in objects:
      if obj['type'] == 'city'
        do_something_with(obj)

.. Sometimes when dealing with a particularly large JSON payload it may worth to
.. not even construct individual Python objects and react on individual events
.. immediately producing some result::

..     import aiojson

..     parser = ijson.parse(urlopen('http://.../'))
..     stream.write('<geo>')
..     for prefix, event, value in parser:
..         if (prefix, event) == ('earth', 'map_key'):
..             stream.write('<%s>' % value)
..             continent = value
..         elif prefix.endswith('.name'):
..             stream.write('<object name="%s"/>' % value)
..         elif (prefix, event) == ('earth.%s' % continent, 'end_map'):
..             stream.write('</%s>' % continent)
..     stream.write('</geo>')


Backends
========

So far we only support a pure python backend.  In the future, it would
be interesting to try to add support for `YAJL <http://lloyd.github.com/yajl/>`_

Acknowledgements
================

Python parser in ijson is relatively simple thanks to `Douglas Crockford
<http://www.crockford.com/>`_ who invented a strict, easy to parse syntax.

The `YAJL <http://lloyd.github.com/yajl/>`_ library by `Lloyd Hilaiel
<http://lloyd.io/>`_ is the most popular and efficient way to parse JSON in an
iterative fashion.

AioJson is heavily based on the code from `Ijson <https://github.com/isagalaev/ijson>`_.
Many thanks to Ivan Sagalaev and the BSD License ;)


