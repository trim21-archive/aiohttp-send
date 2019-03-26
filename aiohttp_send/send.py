import datetime
import mimetypes
import os
import re
import types
from os import path
from os.path import splitdrive, normpath, join
from typing import List
from urllib.parse import unquote_plus

import aiofiles
import aiofiles.os
from aiohttp import web
from multidict import CIMultiDict


async def send(request, file_path, root='', index='', immutable=False,
               max_age=0, hidden=True, format=True, brotli=True, gzip=True,
               set_headers=None, extensions=None, read_step=1024 * 4, **kwargs):
    """
    :type max_age: int
    :type request: web.Request
    :type file_path:str
    :type root:str
    :type index: str
    :type immutable: bool
    :type hidden: bool
    :type format: bool
    :type brotli: bool
    :type gzip: bool
    :type set_headers: Union[typing.Callable, None]
    :type extensions: List[str]
    :type read_step: int
    """
    res = await _prepare(request,
                         file_path=file_path,
                         root=root,
                         index=index,
                         immutable=immutable,
                         max_age=max_age,
                         hidden=hidden,
                         format=format,
                         brotli=brotli,
                         gzip=gzip,
                         set_headers=set_headers,
                         extensions=extensions,
                         **kwargs)

    if res:
        file_path, return_headers, encoding_ext = res
        read_step = int(read_step)
        resp = web.StreamResponse(status=200,
                                  headers=return_headers)

        if not return_headers.get('content-type'):
            t = file_type(file_path, encoding_ext)
            if t:
                resp.content_type = t

        await resp.prepare(request)
        async with aiofiles.open(file_path, mode='rb', buffering=True) as f:
            while True:
                b = await f.read(read_step)
                if b:
                    await resp.write(b)
                else:
                    break
        return resp
    else:
        raise web.HTTPNotFound()


async def _prepare(request,
                   file_path,
                   root='',
                   index=None,
                   immutable=False,
                   max_age=0,
                   hidden=True,
                   format=True,
                   brotli=False,
                   gzip=False,
                   set_headers=None,
                   extensions=None,
                   **kwargs):
    """
    :type max_age: int
    :type request: web.Request
    :type file_path:str
    :type root:str
    :type index: str
    :type immutable: bool
    :type hidden: bool
    :type format: bool
    :type brotli: bool
    :type gzip: bool
    :type set_headers: Union[typing.Callable, None]
    :type extensions: List[str]
    :type read_step: int
    """

    # options
    if not file_path:
        raise ValueError('file_path can\'t be empty string')
    if set_headers:
        if not isinstance(set_headers, types.FunctionType):
            raise ValueError('argument set_headers must be function')

    root = root if root else os.getcwd()
    root = path.abspath(normpath(root))
    if '..' in file_path:
        if check_if_out_of_root(path.splitdrive(file_path)[0], file_path):
            raise web.HTTPForbidden()
    else:
        if check_if_out_of_root('/', file_path):
            raise web.HTTPForbidden()

    if path.isabs(file_path):
        file_path = remove_driver(file_path)

    file_path = join(root, file_path)

    file_path = normpath(file_path)

    trailing_slash = file_path.endswith(path.sep)
    file_path = unquote_plus(file_path)
    if check_if_out_of_root(root, file_path):
        raise web.HTTPForbidden()

    if index and trailing_slash:
        file_path = join(file_path, index)

    if hidden and is_hidden(file_path):
        return

    encoding_ext = ''
    return_headers = CIMultiDict()
    # serve brotli file when possible otherwise gzipped file when possible
    accept_encoding = request.headers.get('Accept-Encoding', False)

    if accept_encoding:
        if brotli and 'br' in accept_encoding \
                and await file_exist(file_path + '.br'):
            return_headers['Content-Encoding'] = 'br'
            file_path = file_path + '.br'
            encoding_ext = '.br'
        elif gzip and 'gzip' in accept_encoding \
                and await file_exist(file_path + '.gz'):
            return_headers['Content-Encoding'] = 'gzip'
            file_path = file_path + '.gz'
            encoding_ext = '.gz'

    if extensions and not re.findall(r'\.[^/^\\]*$', file_path):
        l = list(extensions)
        for ext in l:
            if not isinstance(ext, str):
                raise ValueError(
                    'option extensions must be array of strings or false'
                )
            if not ext.startswith('.'):
                ext = '.' + ext
            if await file_exist(file_path + ext):
                file_path = file_path + ext
                break

    try:
        stats = await file_stats(file_path)
    except OSError:
        return

    if stats.is_directory:
        if format and index:
            file_path += '/' + index
            stats = await file_stats(file_path)
        else:
            raise web.HTTPNotFound()

    if set_headers:
        set_headers(request, file_path, stats, return_headers)

    return_headers['Content-Length'] = str(stats.st_size)
    if not request.headers.get('Last-Modified'):
        return_headers['Last-Modified'] = to_UTC_string(stats.st_mtime)
    if not request.headers.get('Cache-Control'):
        max_age = int(max_age)
        if max_age:
            directives = ['max-age=' + str(max_age or 0), ]
            if immutable:
                directives.append('immutable')
            return_headers['Cache-Control'] = ', '.join(directives)

    return file_path, return_headers, encoding_ext


def file_type(file, ext):
    f = file
    if ext:
        f += ext
    t, _ = mimetypes.guess_type(f)
    return t


def is_hidden(file_path):
    file_path = file_path.split(path.sep)  # type: List[str]
    for part in file_path:
        if part.startswith('.'):
            return True
    return False


def to_UTC_string(a: float):
    return datetime.datetime.utcfromtimestamp(a).strftime(
        '%a, %d %b %Y %H:%M:%S GMT')


file_exist = aiofiles.os.wrap(os.path.exists)
is_directory = aiofiles.os.wrap(os.path.isdir)


class FileState:
    st_mtime = 0
    st_size = 0
    is_directory = False

    def __init__(self, st_mtime, st_size, is_directory):
        self.st_mtime = st_mtime
        self.st_size = st_size
        self.is_directory = is_directory


async def file_stats(path):
    r = await aiofiles.os.stat(path)
    return FileState(st_mtime=r.st_mtime,
                     is_directory=await is_directory(path),
                     st_size=r.st_size)


def remove_driver(file_path):
    if os.path.isabs(file_path):
        driver, file_path = splitdrive(file_path)
        file_path = file_path[1:]
    return file_path


def in_directory(directory, file):
    # make both absolute
    directory = os.path.abspath(directory)
    file = os.path.abspath(file)

    # return true, if the common prefix of both is equal to directory
    # e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return os.path.commonprefix([file, directory]) == directory


def check_if_out_of_root(root_path: str, file_path: str):
    return not in_directory(root_path, join(root_path, file_path))
