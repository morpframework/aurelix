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
- Object storage integration - Use string field as object storage referencing field, which integrates with S3/MinIO based object storage for upload and download through presigned URLs.
- State machine - Define state machine workflow chain for your model for state tracking, including custom functions to trigger on state change.
- Event hooks - Register functions to be triggered on `create`, `update` and `delete` related events.

Additionally, if you are a data engineer and need to have good management of your data model version and migration, Aurelix uses Alembic integration manage versioning of your data model. 

Aurelix also have its own client library which helps interacting with the API server easily, which you can use for writing code-generating ETLs or whatever integration processes.

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
$ export AURELIX_CONFIG=`pwd`/app.yaml
$ aurelix run 
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
spec_version: app/0.1
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
spec_version: model/0.1
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

Aurelix works around YAML configuration for composing your application and models. This allows decoupling between the framework and the apps and also can pave the way for further automation in YAML generation.

### App Configuration

`app.yaml` defines metadata about the application, which includes the FastAPI's app metadata (app title, summary, toc, swagger UI init oauth config), list of databases the application will connect to, and list of view functions to be registered at the root of the app. Following example shows some of the options can be defined on `app.yaml`

```yaml
spec_version: app/0.1
title: Application
summary: My sample app
version: 0.1.0
terms_of_service: 
model_directory: models # directory to model YAML spec, relative to app.yaml
libs_directory: libs # directory to libs directory, relative to app.yaml
databases: # sqlalchemy database connections to create for the app
  - name: default 
    type: sqlalchemy
    url: sqlite:///./database.sqlite
    # url_env: DB_URL # environment variable that stores the database url
object_stores:
  - name: default
    type: minio # type of object storage, we only support MinIO or MinIO compatible servers for now.
    endpoint_url: http://localhost:9000 
    # endpoint_url_env: S3_ENDPOINT # environment variable that stores endpoint url
    access_key: accesskey # object storage access key
    secret_key: secretkey # object storage secret key
    # access_key_env: S3_ACCESS_KEY # environment variable that stores the access key
    # secret_key_env: S3_SECRET_KEY # environment variable that stores the secret key


swagger_ui_init_oauth: # set this if you want to enable swagger UI OIDC auth
  client_id: # oidc client ID for swagger UI
  client_secret: # oidc client secret for swagger UI
oidc_discovery_endpoint: # url to .well-known/openid-configuration of OIDC provider to use as external token provider
views: 
  extensions: # view registry on the root of the app. use this place add views on your app that is not attached to a model
    '/+hello':
      method: 'GET'
      handler:
        code: |
          def function(request: Request):
              return {'message': 'boo'}
```

For more details about `app.yaml` spec, checkout `AppSpec` in [configuration options](docs/config.md).

### Model Configuration

Model configuration is where the bulk of Aurelix capability is, as Aurelix generates API on top of data model specification.

```yaml
name: mymodel # name of the model, this translates to database table name for sqlalchemy storage
storage_type:
  name: sqlalchemy # type of storage to use, for now we only have sqlalchemy
  database: default # name of storage
fields: # this contain the list of fields you want to have in your model. 
  title:
    title: Title 
    data_type:
      type: string
      size: 128
    required: true
    default: null
    indexed: false
    unique: false
    validators: # validator chain
      - code: |
          from aurelix import exc

          def function(collection, value, data):
              # collection: refers to collection object
              # value: value of the field to validate
              # data: refers to full model data to validate
              if not value.startswith('prefix'):
                 raise exc.ValidationError("Invalid title")
      - function: mypackage.mymodule:myfunction # you can also specify reference to function in python module
  encodedString: # you can transform field value before storing into db and when loading from db
    title: Encoded string 
    data_type:
      type: string
      size: 128
    required: false
    default: null
    indexed: false
    unique: false
    input_transformers: # input serialization transform chain before storing in database
      - code: |
          import base64
          def function(collection, value, data):
              return base64.b64encode(value.encode('utf8')).decode('utf8')
    output_transformers: # output deserialization transform chain before returning to user
      - code: |
          import base64
          def function(collection, value, data):
              return base64.b64decode(value.encode('utf8')).decode('utf8')
  selectionField: # you can also specify enum fields
    title: Selection field
    dataType:
      type: string
      size: 128
      enum: 
        - value: option1
          label: Option 1 Title
        - value: option2
          label: Option 2 Title
  fileUpload:  # you can create a string field for referencing to object storage data. refer to objectStore option on the model level below
    title: File Upload
    data_type:
      type: string
      size: 128
objectStore:  # this contains objectStore settings for each field
  fileUpload: 
    type: minio # type of object storage, we only support MinIO or MinIO compatible servers for now.
    endpoint_url: http://localhost:9000 
    bucket: mybucket 
    access_key_env: S3_ACCESS_KEY # environment variable that stores the access key
    secret_key_env: S3_SECRET_KEY # environment variable that stores the secret key

validators: # validation chain on the model itself
  - code: |
      from aurelix import exc
      
      def function(collection, data):
          # collection: refers to collection object
          # data: refers to full model data to validate
          pass

default_field_permission: readWrite # default permission to all fields
permission_filters: # permission filtering rules. it is evaluated from top to bottom

  # row filtering by roles
  - identities:
      - 'role:mygroup'
    where_filter: title like '%postfix' # use SQL where statement here for sqlalchemy storage
  - identities: 
      - '*' # all identities
    where_filter: 0=1 

  # column filtering by roles
  - identities:
      - 'role:group1'
    default_field_permission: restricted
    read_write_fields:
      - title
    read_only_fields:
      - fileUpload
  - identities:
      - 'role:group2'
    default_field_permission: readWrite
    restricted_fields:
      - title
  - identities:
      - '*'
    default_field_permission: restricted

views: # views registry for the model
  listing:
    enabled: true
    max_page_size: 100
  create:
    enabled: true
  read:
    enabled: true
  update:
    enabled: true
  delete:
    enabled: true
  extensions: # custom views registry. views registered here is relative to the collection
    '/+hello':
      method: 'GET'
      handler:
        code: | # you can use fastapi dependency injection here
          def function(request: Request, collection: Collection):
              return {'message': 'collection view'}
    '/{identifier}/+hello': # this view is attached to model
      method: 'GET'
      handler:
        code: | # you can use fastapi dependency injection here
          def function(request: Request, collection: Collection, model: Model):
              return {'message': 'model view'}
tags: 
  - mytag # openapi tag to group all views as
stateMachine: # if you want statemachine on +transition view, configure it here. it uses pytransition internally.
  initial_state: new
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
      on_enter: # you can trigger functions on state enter/exit
        code: |
          from aurelix.crud.base import StateMachine

          def function(sm: StateMachine):
              request = sm.request
              item = sm.item
              # do something here
      on_exit: 
        code: |
          from aurelix.crud.base import StateMachine

          def function(sm: StateMachine):
              request = sm.request
              item = sm.item              
              # do something here
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

before_create: 
  - code: |
      def function(collection, data: dict):
          # do something here
          pass
after_create: 
  - code: |
      def function(collection, item: Model):
          # do something here
          pass
before_update: 
  - code: |
      def function(collection, data: dict):
          # do something here
          pass
after_update: 
  - code: |
      def function(collection, item: Model):
          # do something here
          pass
before_delete: 
  - code: |
      def function(collection, item: Model):
          # do something here
          pass
after_delete: 
  - code: |
      def function(collection, data: dict):
          # do something here
          pass

transform_create_data: 
  - code: |
      def function(collection, data: dict):
          # do something here
          return data
  
transform_update_data: 
  - code: |
      def function(collection, data: dict):
          # do something here
          return data
transform_output_data: 
  - code: |
      def function(collection, data: dict):
          # do something here
          return data

```

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

## Community

Come join us at at https://discord.gg/yuutKdD
