# aiohttp-send

[![Pypi](https://img.shields.io/pypi/v/aiohttp-send.svg)](https://pypi.org/project/aiohttp-send/)
[![codecov](https://codecov.io/gh/Trim21/aiohttp-send/branch/master/graph/badge.svg)](https://codecov.io/gh/Trim21/aiohttp-send)

Send file in [aiohttp](https://github.com/aio-libs/aiohttp)

## Install 

Python 3.6 only now (function arguments type hint does not work in 3.5)

```bash
pip install aiohttp aiohttp-send
```

## Options

 - `max_age` Browser cache max-age in milliseconds. (defaults to `0`)
 - `immutable` Tell the browser the resource is immutable and can be cached indefinitely. (defaults to `False`)
 - `hidden` Allow transfer of hidden files. (defaults to `True`)
 - [`root`](#root-path) Root directory to restrict file access.
 - `index` Name of the index file to serve automatically when visiting the root location. (defaults to `None`)
 - `gzip` Try to serve the gzipped version of a file automatically when `gzip` is supported by a client and if the requested file with `.gz` extension exists. (defaults to `False`).
 - `brotli` Try to serve the brotli version of a file automatically when `brotli` is supported by a client and if the requested file with `.br` extension exists. (defaults to `False`).
 - `format` If not `False` (defaults to `True`), format the path to serve static file servers and not require a trailing slash for directories, so that you can do both `/directory` and `/directory/`.
 - `extensions` Try to match extensions from passed array to search for file when no extension is sufficed in URL. First found is served. (defaults to `False`)
 <!-- - [`set_headers`](#set_headers) Function to set custom headers on response. -->

### Root path

Note that `root` is required, defaults to `''` and will be resolved,
removing the leading `/` to make the path relative and this
path must not contain "..", protecting developers from
concatenating user input. If you plan on serving files based on
user input supply a `root` directory from which to serve from.

For example to serve files from `./public`:

```py
async def index(request: web.Request):
    return await send(request, request.path, root='./public', format=True)

app.add_routes([
    web.get('/{tail:.*}', index),
])
```
<!-- 
### set_headers

The function is called as `fn(res, path, stats)`, where the arguments are:
* `res`: the response object
* `path`: the resolved file path that is being sent
* `stats`: the stats object of the file that is being sent.

You should only use the `setHeaders` option when you wish to edit the `Cache-Control` or `Last-Modified` headers, because doing it before is useless (it's overwritten by `send`), and doing it after is too late because the headers are already sent.

If you want to edit any other header, simply set them before calling `send`.
 -->


## Example

```python
from aiohttp import web
from aiohttp_send import send

app = web.Application()


async def index(request):
    return await send(request, 'index.html')


app.add_routes([
    web.get('/', index),
])

web.run_app(app, port=8888)
```

 
This project comes from [koajs/send](https://github.com/koajs/send).
