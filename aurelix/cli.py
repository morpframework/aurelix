import argparse
import sys
import uvicorn
import os
import asyncio
from .api import load_app, db_upgrade

def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', default=os.environ.get('AURELIX_CONFIG'))
    parser.add_argument('-l', '--host', default='127.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=8000)

    args = parser.parse_args(argv)
    if not args.config:
        print('AURELIX_CONFIG environment is not set, and no config specified', file=sys.stderr)
        sys.exit(1)
    os.environ['AURELIX_CONFIG'] = args.config
    app = asyncio.run(load_app(args.config))
    db_upgrade(app)
    uvicorn.run(app, host=args.host, port=args.port)