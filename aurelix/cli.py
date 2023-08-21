import argparse
import sys
import uvicorn
import os
import asyncio
from .api import load_app, db_upgrade
from . import schema
import yaml

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
    model_spec = schema.ModelSpec.model_validate(DEFAULT_MODEL_CONFIG)
    model_yaml = yaml.safe_dump(model_spec.model_dump(), sort_keys=False)
    with open(os.path.join(path, 'models', 'mymodel.yaml'), 'w') as f:
        f.write(model_yaml)
    print('Application initialized at %s' % path)
    print('Start it by running:\n    aurelix -c %s/app.yaml' % path)

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

    if argv == []:
        argv = ['--help']
    args: argparse.Namespace = parser.parse_args(argv)
    if args.command == 'run':
        if not args.config:
            print('AURELIX_CONFIG environment is not set, and no config specified', file=sys.stderr)
            sys.exit(1)
        os.environ['AURELIX_CONFIG'] = args.config
        app = asyncio.run(load_app(args.config))
        db_upgrade(app)
        uvicorn.run(app, host=args.host, port=args.port)
    elif args.command == 'init':
        init_app(path=args.DIRECTORY)