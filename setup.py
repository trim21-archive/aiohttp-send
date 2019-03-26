import os
import re

from setuptools import setup


def _get_version():
    PATH_TO_INIT_PY = \
        os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'aiohttp_send',
            '__init__.py'
        )

    with open(PATH_TO_INIT_PY, 'r', encoding='utf-8') as fp:
        try:
            for line in fp.readlines():
                if line:
                    line = line.strip()
                    _version = re.findall(r"^__version__ = '([^']+)'$", line,
                                          re.M)
                    if _version:
                        return _version[0]
        except IndexError:
            raise RuntimeError('Unable to determine version.')


version = _get_version()
if not version:
    raise ValueError('Unable to determine version.')

install_requires = [line.strip() for line in
                    open('requirements.txt', 'r', encoding='utf8').readlines()
                    if line.strip()]

setup(
    version=version,
    install_requires=install_requires,
)
