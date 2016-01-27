"""
Simple http server to create streams for asyncio tests
"""
import asyncio
import aiohttp
from aiohttp import web


async def get_data(server):
    async with server.get_response() as r:
        stream = r.content
        while not stream.at_eof():
            data = await stream.read(3)
            print(data.decode('utf-8'))


class DemoServer:
    def __init__(self, data):
        self.data = data
        self.app = web.Application()
        self.app.router.add_route('GET', '/', self.hello)
        self.handler = self.app.make_handler()
        self.url = None

    async def hello(self, request):
        return web.Response(body=self.data)

    def start_server(self, loop, host='127.0.0.1', port='56789'):
        self.url = 'http://{}:{}/'.format(host, port)
        setup = loop.create_server(self.handler, host, port)
        self.srv = loop.run_until_complete(setup)
        return self.srv

    def stop_server(self, loop):
        self.srv.close()
        loop.run_until_complete(self.srv.wait_closed())
        loop.run_until_complete(self.handler.finish_connections(1.0))
        loop.run_until_complete(self.app.finish())

    def get_response(self):
        return aiohttp.get(self.url)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    server = DemoServer(b'M\xc3\xa4dchen mit Bi\xc3\x9f\n')
    server.start_server(loop)
    try:
        task = asyncio.ensure_future(get_data(server))
        loop.run_until_complete(task)
    finally:
        server.stop_server(loop)
        loop.close()
