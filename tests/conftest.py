import pytest
from pytest_server_fixtures import s3
from pytest_server_fixtures.http import HTTPTestServer
import os
from fastapi.testclient import TestClient
from pathlib import Path
import sqlalchemy as sa
import asyncio


pytest_plugins = []

moddir = Path(os.path.abspath(os.path.dirname(__file__)))

class AurelixServer(HTTPTestServer):

    @property
    def run_cmd(self):
        cmdargs = [
            'aurelix',
            "run",
            "-l",
            self.hostname, 
            '-p',
            str(self.port),
        ]
        return cmdargs

@pytest.fixture(scope='session')
def aurelix(request, s3_server: s3.MinioServer):
    access_key = s3_server.aws_access_key_id
    secret_key = s3_server.aws_secret_access_key
    server = s3_server.uri

    os.environ['S3_ENDPOINT'] = server.replace('://0.0.0.0:','://127.0.0.1:')
    os.environ['S3_ACCESS_KEY'] = access_key
    os.environ['S3_SECRET_KEY'] = secret_key

    db = '/tmp/test.db'
    if os.path.exists(db):
        os.unlink(db)

    os.environ['DB_URL'] = 'sqlite:///%s' % db

    from aurelix.api import load_app
    from aurelix import state

    os.environ['AURELIX_CONFIG'] = str(moddir / 'simple_app' / 'app.yaml')

    server = AurelixServer()
    server.start()
    request.addfinalizer(server.teardown)

    from aurelix.client import Client
    return Client(server.uri)