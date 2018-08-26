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

setup(name='aiohttp-send',
      version=version,
      description="Send file in for aiohttp.web (http server for asyncio)",
      long_description=open('README.md', 'r', encoding='utf8').read(),
      long_description_content_type='text/markdown',  # This is important!
      classifiers=[
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Development Status :: 3 - Alpha',
          'Topic :: Internet :: WWW/HTTP',
          'Framework :: AsyncIO',
      ],
      author='Trim21',
      author_email='trim21me@gmail.com',
      url='https://github.com/Trim21/aiohttp-send',
      license='MIT',
      packages=['aiohttp_send'],
      python_requires='>=3.5.3',
      install_requires=install_requires,
      include_package_data=True)
