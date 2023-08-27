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

    o.refresh()

    assert o['encodedString'] == 'hello world'

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

    o.refresh()
    assert o['encodedString'] == 'hello world'

    o.upload('fileUpload', io.BytesIO(b'hello world'))

    assert b''.join(o.download('fileUpload')) == b'hello world'

    o.refresh()

    assert o['encodedString'] == 'hello world'

    with pytest.raises(RemoteException) as excinfo:
        o.update({
            'title': 'boo'
        })
    assert excinfo.value.args[0] == 'Error 422: Invalid title'

    with pytest.raises(RemoteException) as excinfo:
        o.update(dict(
            selectionField='boo'
        ))

    assert excinfo.value.args[0].startswith('Error 422: ')
    assert "'option1' or 'option2'" in excinfo.value.args[0]

    o.update(dict(
        selectionField='option2'
    ))

    assert o['encodedString'] == 'hello world'

    assert o['selectionField'] == 'option2'
    o = aurelix['mymodel'].get_item(o['id'])
    assert o['title'] == 'prefix 1111'
    assert o['encodedString'] == 'hello world'

    o.delete()

    with pytest.raises(ClientException) as excinfo:
        o.refresh()

    with pytest.raises(ClientException) as excinfo:
        o['encodedString']