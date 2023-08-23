import argparse
import sys
import uvicorn
import os
import asyncio
from .api import load_app
from . import schema
from alembic import command as alembic_command
from alembic import config as alembic_config
import yaml

class AlembicConfig(alembic_config.Config):

    def get_template_directory(self) -> str:
        return os.path.join(os.path.dirname(__file__), 'alembic_templates')

DEFAULT_APP_CONFIG = {
    'databases': [
        {'name': 'default',
         'url': 'sqlite:///./database.sqlite'}
    ]
}

DEFAULT_MODEL_CONFIG = {
    'name': 'mymodel',
    'storageType': {
        'name': 'sqlalchemy',
        'database': 'default',
    },
    'fields': {
        'title': {
            'title': 'Title',
            'dataType': {
                'type': 'string',
                'size': 128,
                'required': True
            }
        }
    },
}

def init_app(path: str):
    if not os.path.exists(path):
        os.mkdir(path)
    else:
        raise Exception('Path %s already exists' % path)
    appspec = schema.AppSpec.model_validate(DEFAULT_APP_CONFIG)
    app_yaml = yaml.safe_dump(appspec.model_dump(), sort_keys=False)
    with open(os.path.join(path, 'app.yaml'), 'w') as f:
        f.write(app_yaml)
    for d in ['models', 'libs']:
        os.mkdir(os.path.join(path, d))

    # create sample model yaml
    model_spec = schema.ModelSpec.model_validate(DEFAULT_MODEL_CONFIG)
    model_yaml = yaml.safe_dump(model_spec.model_dump(), sort_keys=False)
    with open(os.path.join(path, 'models', 'mymodel.yaml'), 'w') as f:
        f.write(model_yaml)

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

    run_command.add_argument('-c', '--config', default=os.environ.get('AURELIX_CONFIG'))
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
        if not args.config:
            print('AURELIX_CONFIG environment is not set, and no config specified', file=sys.stderr)
            sys.exit(1)
        os.environ['AURELIX_CONFIG'] = args.config
        app = asyncio.run(load_app(args.config))
        uvicorn.run(app, host=args.host, port=args.port)
    elif args.command == 'init':
        init_app(path=args.DIRECTORY)