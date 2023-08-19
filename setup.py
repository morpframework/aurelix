from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='aurelix',
      version=version,
      description="Low code API framework based on Dectate and FastAPI",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Izhar Firdaus',
      author_email='kagesenshi.87@gmail.com',
      url='',
      license='LGPLv3',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'dectate',
          'fastapi[all]',
          'uvicorn[standard]',
          'pydantic',
          'sqlalchemy',
          'databases[aiopg,aiomysql,aiosqlite]',
          'aiosqlite',
          'aiopg',
          'aiomysql',
          'pydantic-settings',
          'transitions',
          'python-multipart',
          'aiohttp',
      ],
      entry_points={
          'console_scripts': [
              'aurelix=aurelix.cli:main'
          ]
      }
      )
