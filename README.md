Aurelix: Low Code API Framework Based on FastAPI, Dectate and SQLAlchemy
=========================================================================


Starting your first model
--------------------------

Create a directory with following structure

```
- app.yaml
- models/
`- mymodel.yaml
- libs/
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

Start up the service

```console
$ podman run -v .:/opt/app -p 8000:8000 -ti --rm docker.io/kagesenshi/aurelix:latest
```

For more details about `app.yaml` spec, checkout pydantic class `aurelix.schema:AppSpec`.

For more details about model spec for `mymodel.yaml`, check out the Pydantic model in `aurelix.schema:ModelSpec`
