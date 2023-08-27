import argparse
import sys
import uvicorn
import os
import asyncio
from .api import load_app
from . import schema
from .settings import Settings
from alembic import command as alembic_command
from alembic import config as alembic_config
import yaml
from pathlib import Path
import os
import shutil

pkgdir = Path(os.path.abspath(os.path.dirname(__file__)))

class AlembicConfig(alembic_config.Config):

    def get_template_directory(self) -> str:
        return os.path.join(os.path.dirname(__file__), 'alembic_templates')

with open(pkgdir / 'default_templates' / 'app.yaml') as f:
    DEFAULT_APP_CONFIG = yaml.safe_load(f)

with open(pkgdir / 'default_templates' / 'model.yaml') as f:
    DEFAULT_MODEL_CONFIG = yaml.safe_load(f)

def init_app(path: str):

    path = Path(path)
    if not os.path.exists(path):
        os.mkdir(path)
    else:
        raise Exception('Path %s already exists' % path)

    shutil.copy(pkgdir / 'default_templates' / 'app.yaml', path / 'app.yaml')

    for d in ['models', 'libs']:
        os.mkdir(os.path.join(path, d))

    # create sample model yaml
    shutil.copy(pkgdir / 'default_templates' / 'model.yaml', path / 'models' / 'app.yaml')

    # create alembic.ini
    os.chdir(path)
    aconfig = AlembicConfig(file_='alembic.ini')
    alembic_command.init(aconfig, 'migrations',  template='default')
    print('\nApplication initialized at %s/\n' % path)
    print('Start it by running:')
    print('    cd %s/' % path)
    print('    alembic revision --autogenerate -m "initial model"')
    print('    alembic upgrade head')
    print('    aurelix run -c app.yaml')


def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser()


    subparsers = parser.add_subparsers(dest='command')
    run_command = subparsers.add_parser('run')

    run_command.add_argument('-l', '--host', default='127.0.0.1')
    run_command.add_argument('-p', '--port', type=int, default=8000)

    init_command = subparsers.add_parser('init')
    init_command.add_argument('DIRECTORY')

    db_command = subparsers.add_parser('db')
    db_subcommand = db_command.add_subparsers(dest='db_command')
    db_subcommand.add_parser('init')

    if argv == []:
        argv = ['--help']
    args: argparse.Namespace = parser.parse_args(argv)


    if args.command == 'run':
        settings = Settings()
        if not settings.CONFIG:
            print('AURELIX_CONFIG environment is not set', file=sys.stderr)
            sys.exit(1)
        os.environ['AURELIX_CONFIG'] = settings.CONFIG
        app = asyncio.run(load_app(settings.CONFIG))
        uvicorn.run(app, host=args.host, port=args.port)
    elif args.command == 'init':
        init_app(path=args.DIRECTORY)