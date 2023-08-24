# Aurelix: Low Code API Framework Based on FastAPI, Dectate and SQLAlchemy

Aurelix is a low code framework for quickly building APIs for storing data and files. It is built on top of FastAPI and SQLAlchemy, and inherit some extension capabilities from Morepath's Dectate library, and pretty much a rewrite of all core ideas from MorpFW into a new framework to address deficiency and problems of the original implementation. 

Aurelix uses YAML for define composable data models in declarative manner and interprets it into RESTful API that follows a degree of JSONAPI specification. 

Capabilities definable through the YAML includes:

- Data structure - You can define fields which will be interpreted as table columns.
- Built-in CRUD views - Save time writing RESTful CRUD views as Aurelix includes the usual `GET`, `PUT`, `PATCH`, `DELETE` operations, alongside a search URL with pagination.
- Custom views - Extend your app and model with custom views of your own, you can either reference to a function in a module, or you can just put the code in the YAML. 
- OIDC integration - If you are using OIDC provider that provides OIDC 
discoverability endpoint, you can use that OIDC provider for authentication.
- Collection-wide permission filtering - You can specify role-specific `where` filters which will be applied to different roles to allow or prevent them from seeing specific sections of you data
- Field permission filtering - You can specify role specific field permissions to limit access to fields (`readWrite`, `readOnly`, `restricted`) by role.
- Field transformation chain - You can specify input and output transformation chain for fields, for example, to encrypt and decrypt data before storing into database.
- Model transformation chain - Similar as field transformation chain, but this applies against the whole record.
- Field validation chain - Register custom functions to validate field values when create/update.
- Object storage integration - Use string field as object storage referencing field, which integrates with S3 based object storage for upload and download through presigned URLs.
- State machine - Define state machine workflow chain for your model for state tracking, including custom functions to trigger on state change.
- Event hooks - Register functions to be triggered on `create`, `update` and `delete` related events.

Additionally, if you are a data engineer and need to have good management of your data model version and migration, Aurelix uses Alembic integration manage versioning of your data model.

## Installing

Aurelix requires Python 3.11+

Install full server

```console
$ pip install aurelix[server]
```

Only install for client library use

```console
$ pip install aurelix
```

## Initializing application

To initialize and application, you can run

```console
$ aurelix init myproject
```

And start it using

```console
$ cd myproject/
$ alembic revision --autogenerate -m "initial model"
$ alembic upgrade head
$ aurelix run -c app.yaml
```

## Example app

This example shows a bit more of Aurelix capabilities. Detailed documentation is still WIP.

Project directory of this sample app looks like this:
```
myproject/
`- app.yaml
`- models/
 `- mymodel.yaml
`- libs/
 `- myviews.py
```

Contents of `app.yaml`:

```yaml
title: MyApp
databases:
  - name: default
    url: sqlite:///./database.sqlite
```

Contents of `libs/myviews.py`. Aurelix config can load views and modules from `libs/` directory:

```python
from fastapi import Request

async def myview(request: Request):
    return {
       'hello': 'world'
    }
```

Contents of `models/mymodel.yaml`. Automated API creation from model is where the bulk of Aurelix features are:


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

### Start up the service:

#### Using docker

```console
$ docker run -v /path/to/myproject:/opt/app -p 8000:8000 -ti --rm docker.io/kagesenshi/aurelix:latest
```

#### Using `aurelix` command

```console
$ export AURELIX_CONFIG='/path/to/myproject/app.yaml'
$ aurelix run -l 0.0.0.0
```

## Configuration Spec

For more details about `app.yaml` spec, checkout `AppSpec` in [configuration options](docs/config.md).

For more details about model spec for `mymodel.yaml`, check out `ModelSpec` in [configuration options](docs/config.md)

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
