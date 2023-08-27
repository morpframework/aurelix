from aurelix.client import Client, RemoteException, ClientException
from pytest_server_fixtures import s3
import os
from pathlib import Path
import fastapi
import pytest
import io
import boto3
import time

def test_load_app(aurelix: Client, s3_server: s3.MinioServer, s3_bucket):

    client = s3_server.get_s3_client()
    client.create_bucket(Bucket='mybucket')

    
    model_col = aurelix['mymodel']
    
    o = model_col.create(dict(
        title='prefix 1111',
        encodedString='hello world',
        selectionField='option1',
    ))

    with pytest.raises(RemoteException) as excinfo:
        model_col.create(dict(
            title='aaa',
        ))

    exc: RemoteException = excinfo.value
    assert exc.args[0] == 'Error 422: Invalid title'

    with pytest.raises(RemoteException) as excinfo:
        model_col.create(dict(
            title='prefix 123',
            fileUpload='hooo'
        ))

    exc: RemoteException = excinfo.value
    assert exc.args[0] == 'Error 422: Field fileUpload is protected'

    o.upload('fileUpload', io.BytesIO(b'hello world'))

    assert b''.join(o.download('fileUpload')) == b'hello world'

