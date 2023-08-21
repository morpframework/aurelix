from setuptools import setup, find_packages
import sys, os

version = '0.1'

SERVER_REQUIRES=[
    'dectate',
    'fastapi[all]',
    'uvicorn[standard]',
    'pydantic',
    'sqlalchemy',
    'sqlalchemy_utils',
    'databases[aiopg,aiomysql,aiosqlite]',
    'aiosqlite',
    'aiopg',
    'aiomysql',
    'pydantic-settings',
    'transitions',
    'python-multipart',
    'aiohttp',
    'cryptography',
]

CLIENT_REQUIRES=[
    'requests'
]

def read_file(name) -> str:
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return f.read()

setup(name='aurelix',
      version=version,
      description="Low code API framework based on Dectate and FastAPI",
      long_description='\n\n'.join([read_file('README.md'), read_file('CHANGES.md')]),
      long_description_content_type='text/markdown',
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Izhar Firdaus',
      author_email='kagesenshi.87@gmail.com',
      url='',
      license='LGPLv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=CLIENT_REQUIRES,
      extras_require={
            'server': SERVER_REQUIRES,
            'all': CLIENT_REQUIRES + SERVER_REQUIRES
      },
      entry_points={
          'console_scripts': [
              'aurelix=aurelix.cli:main'
          ]
      },
)
