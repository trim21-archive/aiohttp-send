import aiohttp.test_utils
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
import os
from os import path
import sys

sys.path.append(path.join(path.dirname(__file__), '..'))
from aiohttp_send import send
from aiohttp import web
import pathlib

fixtures_root = path.join(path.dirname(__file__), './fixtures')
fixtures_root = pathlib.Path(fixtures_root)


def abspath(file_path):
    """
    patch python3.5

    """
    return path.abspath(str(file_path))


"""
tests/fixtures/ # fixtures_root
|-- gzip.json
|-- gzip.json.br
|-- gzip.json.gz
|-- hello.txt
|-- index.txt
|-- some.path
|   `-- index.json
|-- user.json
|-- user.txt
`-- world
    `-- index.html
"""


def wrapper(*args,
            **kwargs):
    async def hello(r):
        return await send(r, *args, **kwargs)

    return hello


# no fixtures_root

async def test_no_root_absolute_path(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper(
        abspath(fixtures_root / 'fixtures' / 'hello.txt')))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_no_root_absolute_path_raise_404(aiohttp_client):
    @web.middleware
    async def middleware1(request, handler):
        try:
            resp = await handler(request)
            return resp
        except Exception as e:
            assert isinstance(e, web.HTTPNotFound)
            raise e

    app = web.Application(middlewares=[middleware1, ])
    app.router.add_get('/', wrapper(abspath(fixtures_root / 'hello.txt')))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_no_root_relative_path_200(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('tests/fixtures/hello.txt'))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert 'world' in await resp.text()


async def test_no_root_path_with_common(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/../fixtures/hello.txt'))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 403


async def test_root_absolute_path_404(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper(abspath(fixtures_root / 'hello.txt'),
                                    root='tests/fixtures'))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_root_relative_path_exist_200(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('hello.txt',
                                    root='tests/fixtures'))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert 'world' in await resp.text()


async def test_root_relative_path_not_exist_404(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('233',
                                    root='tests/fixtures'))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_root_relative_path_outside_root_403(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('../hello.txt',
                                    root='tests/fixtures/world'))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 403


async def test_root_relative_path_outside_then_inside_root_403(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('../../tests/fixtures/world/index.html',
                                    root='tests/fixtures'))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 403


async def test_root_index1(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('fixtures/world/',
                                    root='tests', index='index.html'))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert 'html index' in await resp.text()


async def test_root_index2(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/',
                                    root='tests/fixtures/world',
                                    index='index.html'))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert 'html index' in await resp.text()


async def test_path_not_file_404(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests', ))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_path_not_file_no_format_404(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests', format=False))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_path_is_dir(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures', ))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_path_not_finish_with_slash_and_format_is_disabled(
        aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('fixtures/world',
                                    root='tests',
                                    index='index.html',
                                    format=False))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_path_does_not_end_with_slash_and_format_is_true(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('fixtures/world',
                                    root='tests',
                                    index='index.html',
                                    ))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert 'html index' in await resp.text()


async def test_path_does_not_end_with_slash_and_index_empty_404(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('fixtures/world',
                                    root='tests',
                                    ))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_path_malformed_400(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/%', ))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_return_raw_file(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/gzip.json', gzip=False, brotli=False))
    client = await aiohttp_client(app)
    resp = await client.get('/', )
    assert resp.status == 200
    assert '{ "name": "tobi" }' == await resp.text()
    assert resp.headers['Content-Length'] == '18'


async def test_gz_return_raw_file(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/gzip.json', gzip=True))
    client = await aiohttp_client(app)
    resp = await client.get('/', headers={
        'Accept-Encoding': 'deflate, identity'
    })
    assert resp.status == 200
    assert '{ "name": "tobi" }' == await resp.text()
    assert resp.headers['Content-Length'] == '18'


async def test_gz_return_gz_file(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/gzip.json', gzip=True))
    client = await aiohttp_client(app)
    resp = await client.get('/', headers={
        'Accept-Encoding': 'gzip, deflate, identity'
    })
    assert resp.status == 200
    assert '{ "name": "tobi" }' == await resp.text()
    assert resp.headers['Content-Length'] == '48'


async def test_br_return_br_file(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/gzip.json', brotli=True))
    client = await aiohttp_client(app)
    resp = await client.get('/', headers={
        'Accept-Encoding': 'br, deflate, identity'
    })
    assert resp.status == 200
    assert '{ "name": "tobi" }' == await resp.text()
    assert resp.headers['Content-Length'] == '22'


async def test_br_return_raw_file(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/gzip.json', brotli=True))
    client = await aiohttp_client(app)
    resp = await client.get('/', headers={
        'Accept-Encoding': 'deflate, identity'
    })
    assert resp.status == 200
    assert '{ "name": "tobi" }' == await resp.text()
    assert resp.headers['Content-Length'] == '18'


async def test_max_age(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/gzip.json', max_age=5))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert resp.headers['Cache-Control'] == 'max-age=5'


async def test_max_age_float(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/gzip.json', max_age=5.233))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert resp.headers['Cache-Control'] == 'max-age=5'


async def test_max_age_immutable(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/gzip.json',
                                    max_age=5,
                                    immutable=True))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert resp.headers['Cache-Control'] == 'max-age=5, immutable'


async def test_only_immutable_no_cache_control(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/gzip.json',
                                    # max_age=5,
                                    immutable=True))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert not resp.headers.get('Cache-Control')


async def test_no_cache_control_when_no_file(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('2333',
                                    max_age=5,
                                    immutable=True))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404
    assert not resp.headers.get('Cache-Control')


async def test_hidden_file(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('tests/fixtures/.hidden'))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_file_in_hidden_dir(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('tests/fixtures/.private/id_rsa.txt'))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_return_hidden_file_when_hidden_false(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('tests/fixtures/.private/id_rsa.txt',
                                    hidden=False))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200


async def test_content_type(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/user.json', ))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert resp.headers['content-type'] == 'application/json'


async def test_content_length(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/user.json', ))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert resp.headers['content-length'] == '18'


async def test_last_modified(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/user.json', ))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert 'GMT' in resp.headers['last-modified']


async def test_no_ext_404(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/user', ))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_no_ext_not_match_404(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/hello',
                                    extensions=['json', 'htm', '.html']))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 404


async def test_extensions_not_list_of_str(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/hello',
                                    extensions=[{}, [], 2]))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 500


async def test_extensions_return_first(aiohttp_client):
    app = web.Application()
    app.router.add_get('/', wrapper('/tests/fixtures/user',
                                    extensions=['html', 'json', 'txt']))
    client = await aiohttp_client(app)
    resp = await client.get('/')
    assert resp.status == 200
    assert resp.headers['content-type'] == 'application/json'

# todo set_headers
