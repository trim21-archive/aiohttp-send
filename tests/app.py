from aiohttp import web

from aiohttp_send import send, send_stream
from aiohttp_send.send import _prepare

app = web.Application()


async def index(request: web.Request):
    res = await _prepare(request, request.path, root='..', format=True)
    print(res)
    return await send(request, request.path, root='../', extensions=['md', 'py'], format=True)


async def big(request):
    return await send_stream(request, 'a-big-file.html')


app.add_routes([
    web.get('/{tail:.*}', index),
    web.get('/big', big),
])

web.run_app(app, port=8888)
