# Aurelix: Low Code API Framework Based on FastAPI, Dectate and SQLAlchemy

## Installing

### Using pip

Install full server

```console
$ pip install aurelix[server]
```

Only install for client library use

```console
$ pip install aurelix
```

### Using docker

Pull docker image

```
$ docker pull docker.io/kagesenshi/aurelix:latest
```

## Starting your first model

Create a directory with following structure

```
myproject/
`- app.yaml
`- models/
 `- mymodel.yaml
`- libs/
 `- myviews.py
```

Set following contents in `app.yaml`:

```yaml
title: MyApp
databases:
  - name: default
    url: sqlite:///./database.sqlite
```

Set following contents in `myviews.py`:

```python
from fastapi import Request

async def myview(request: Request):
    return {
       'hello': 'world'
    }
```

Set following contents in `mymodel.yaml`:


```yaml
name: mymodel
storageType:
  name: sqlalchemy
  database: default
fields:
  title:
    title: Title
    dataType:
      type: string
      size: 128
    required: true

  workflowStatus:
    title: Workflow Status
    dataType:
      type: string
      size: 64
    required: true
    indexed: true

views:
  extensions:
    - '/+custom-view':
        method: GET
        handler:
          function: myviews:myview

stateMachine:
  initialState: new
  field: workflowStatus
  states:
    - value: new
      label: New
    - value: running
      label: Processing
    - value: completed
      label: Completed
    - value: failed
      label: Failed
    - value: terminated
      label: Cancelled
  transitions:
    - trigger: start
      label: Start
      source: new
      dest: running
    - trigger: stop
      label: Stop
      source: running
      dest: terminated
    - trigger: complete
      label: Mark as completed
      source: running
      dest: completed
    - trigger: fail
      label: Mark as failed
      source: runnning
      dest: failed
tags:
  - custom tag
```

## Start up the service:

### Using docker

```console
$ docker run -v /path/to/myproject:/opt/app -p 8000:8000 -ti --rm docker.io/kagesenshi/aurelix:latest
```

### Using `aurelix` command

```console
$ export AURELIX_CONFIG='/path/to/myproject/app.yaml'
$ aurelix -l 0.0.0.0
```

## Configuration Spec

For more details about `app.yaml` spec, checkout pydantic class `aurelix.schema:AppSpec`.

For more details about model spec for `mymodel.yaml`, check out the Pydantic model in `aurelix.schema:ModelSpec`

## Client Library 

Aurelix includes client library for interacting Aurelix server

```python
from aurelix.client import Client

aurelix = Client('http://localhost:8000')

# create object

item = aurelix['mymodel'].create({'title': 'Title 1'})

# update object
item.update({'title': 'Title 2'})

# delete object
item.delete()

```
