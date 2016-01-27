"""
Simple http server to create streams for asyncio tests
"""
import asyncio
import aiohttp
from aiohttp import web


async def get_data(host, port):
    url = 'http://{}:{}/'.format(host, port)
    async with aiohttp.get(url) as r:
        stream = r.content
        while not stream.at_eof():
            data = await stream.read(4)
            print(data.decode('utf-8'))


class UTF8Server:
    def __init__(self):
        self.app = web.Application()
        self.app.router.add_route('GET', '/', self.hello)
        self.handler = self.app.make_handler()

    async def hello(self, request):
        return web.Response(body=b'M\xc3\xa4dchen mit Bi\xc3\x9f\n')

    def start_server(self, loop, host, port):
        setup = loop.create_server(self.handler, host, port)
        self.srv = loop.run_until_complete(setup)
        return self.srv

    def stop_server(self, loop):
        self.srv.close()
        loop.run_until_complete(self.srv.wait_closed())
        loop.run_until_complete(self.handler.finish_connections(1.0))
        loop.run_until_complete(self.app.finish())


if __name__ == '__main__':
    HOST = '127.0.0.1'
    PORT = '56789'
    loop = asyncio.get_event_loop()
    server = UTF8Server()
    server.start_server(loop, HOST, PORT)
    print("serving on", server.srv.sockets[0].getsockname())

    try:
        task = asyncio.ensure_future(get_data(HOST, PORT))
        loop.run_until_complete(task)
    finally:
        server.stop_server(loop)
        loop.close()
