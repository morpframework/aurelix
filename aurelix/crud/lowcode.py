import fastapi
import httpx
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, SecurityScopes, OAuth2AuthorizationCodeBearer
import inspect
import os
import sys
import yaml
import sqlalchemy as sa
import pydantic
import importlib
from ..utils import validate_types, snake_to_pascal, snake_to_camel
from ..crud.sqla import SQLACollection
from ..crud.base import StateMachine
from ..crud.routes import register_collection
from .dependencies import get_collection, Collection, Model
from ..exc import AurelixException
from ..settings import Settings
from .. import schema
from .. import exc
from .. import state
from typing import Any
import sqlite3
import enum
import typing
import transitions 
import glob
import databases
import datetime

PY_TYPES = {
    'string': str,
    'text': str,
    'integer': int,
    'boolean': bool
}

SA_TYPES={
    'string': sa.String,
    'text': sa.Text,
    'integer': sa.Integer,
    'boolean': sa.Boolean
}

def create_table(name, metadata, columns=None, indexes=None, constraints=None, *args):
    columns = columns or []
    indexes = indexes or []
    constraints = constraints or []

    columns = [
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('dateCreated', sa.DateTime, default=datetime.datetime.utcnow, index=True),
        sa.Column('dateModified', sa.DateTime, default=datetime.datetime.utcnow, index=True),
        sa.Column('creator', sa.String, nullable=True, index=True),
        sa.Column('editor', sa.String, nullable=True, index=True),
    ] + columns

    return sa.Table(
        name,
        metadata,
        *columns,
        *indexes,
        *args
    )


class Registry(dict):

    def __getattr__(self, __key: Any) -> Any:
        return self[__key]
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        self[__name] = __value

    def __delattr__(self, __name: str) -> None:
        del self[__name]
    
async def load_app(path: str):

    with open(path) as f:
        spec: schema.AppSpec = schema.AppSpec.model_validate(yaml.safe_load(f))

    spec_dir = os.path.dirname(path)
    init_oauth = {}
    if spec.swagger_ui_init_oauth.client_id:
        init_oauth['clientId'] = spec.swagger_ui_init_oauth.client_id
    if spec.swagger_ui_init_oauth.client_secret:
        init_oauth['clientSecret'] = spec.swagger_ui_init_oauth.client_secret
    if init_oauth.keys() and spec.title:
        init_oauth['appName'] = spec.title

    app = fastapi.FastAPI(debug=spec.debug, title=spec.title, summary=spec.summary, version=spec.version,
                          docs_url=spec.docs_url, redoc_url=spec.redoc_url, 
                          swagger_ui_oauth2_redirect_url=spec.swagger_ui_oauth2_redirect_url,
                          terms_of_service=spec.terms_of_service,
                          swagger_ui_init_oauth=init_oauth or None)
    state.APP_STATE.setdefault(app, {})
    state.APP_STATE[app]['settings'] = spec

    if spec.libs_directory:
        ld_path = os.path.join(spec_dir, spec.libs_directory)
        if os.path.exists(ld_path):
            sys.path.append(ld_path)

    for d in spec.databases:
        metadata = sa.MetaData()
        engine = sa.create_engine(
            d.url, connect_args={"check_same_thread": False}
        )
        db = databases.Database(d.url)
        state.APP_STATE[app].setdefault('databases', {})
        state.APP_STATE[app]['databases'][d.name] = {
            'metadata': metadata,
            'engine': engine,
            'db': db
        }

    if spec.model_directory:
        md_path = os.path.join(spec_dir, spec.model_directory)
        if os.path.exists(md_path):
            load_app_models(app, md_path)

    env_settings = Settings()
    oidc_discovery_endpoint = spec.oidc_discovery_endpoint or env_settings.OIDC_DISCOVERY_ENDPOINT
    if oidc_discovery_endpoint:
        async with httpx.AsyncClient() as client:
            resp = await client.get(oidc_discovery_endpoint)
            if resp.status_code != 200:
                raise exc.GatewayError("Unable to get OIDC discovery metadata")
            oidc_settings = schema.OIDCConfiguration.model_validate(resp.json())
            state.APP_STATE[app]['oidc_settings'] = oidc_settings
        
    register_views(app)

    return app

def db_upgrade(app: fastapi.FastAPI):
    for m in state.APP_STATE[app]['databases'].values():
        metadata = m['metadata']
        engine = m['engine']
        metadata.create_all(engine)


def load_app_models(app, directory_path):
    app.collection = Registry()
    for fn in glob.glob('*.yaml', root_dir=directory_path):
        res = load_model_spec(app, os.path.join(directory_path, fn))
        spec = res['spec']
        app.collection[snake_to_pascal(res['spec'].name)] = res['collection']
        app.collection[res['spec'].name] = res['collection']

        openapi_extra = {}
        if spec.tags:
            openapi_extra['tags'] = spec.tags

        state.APP_STATE[app].setdefault('models', {})
        state.APP_STATE[app]['models'][spec.name] = spec

        register_collection(app, res['collection'], 
            listing_enabled=spec.views.listing.enabled,
            create_enabled=spec.views.create.enabled,
            read_enabled=spec.views.read.enabled,
            update_enabled=spec.views.update.enabled,
            delete_enabled=spec.views.delete.enabled,
            openapi_extra=openapi_extra
        )

def load_model_spec(app: fastapi.FastAPI, path: str):

    with open(path) as f:
        spec: schema.ModelSpec = schema.ModelSpec.model_validate(yaml.safe_load(f))

    result = {'spec': spec}
    model_type = spec.storageType.name
    Schema = generate_pydantic_model(spec,name=snake_to_pascal(spec.name))
    result['schema'] = Schema
    if model_type == 'sqlalchemy':
        table = generate_sqlalchemy_table(app, spec)
        result['table'] = table
        Collection = generate_sqlalchemy_collection(
            app,
            spec, Schema, table, 
            name=snake_to_pascal(spec.name))
        result['collection'] = Collection
    if spec.stateMachine:
        state_machine = generate_statemachine(spec, name=snake_to_pascal(spec.name))
        Collection.StateMachine = state_machine
    if spec.views.extensions:
        views = spec.views.extensions
        for vpath, vspec in views.items():
            tags = vspec.tags
            view_opts = dict((k,v) for k,v in vspec.model_dump().items() if k not in ['handler', 'tags'])
            if tags and view_opts.get('openapi_extra', None):
                view_opts['openapi_extra']['tags'] = tags
            else:
                view_opts['openapi_extra'] = {'tags': tags}
            coderef = vspec.handler
            if coderef:
                impl = load_code_ref(coderef)
                if impl:
                    Collection.view(vpath, **view_opts)(impl)
    return result
    
def generate_statemachine(spec: schema.ModelSpec, name: str = 'StateMachine'):
    state_field = spec.stateMachine.field
    states = [s.value for s in spec.stateMachine.states]
    trans = [{'trigger': t.trigger, 
              'source': t.source, 
              'dest': t.dest} for t in spec.stateMachine.transitions]

    attrs =  {
        'field': state_field,
        'states': states,
        'transitions': trans,
    }
    for s in spec.stateMachine.states:
        for m in ['on_enter', 'on_exit']:
            coderef = getattr(m, snake_to_camel(m), None)
            if coderef:
                impl = load_code_ref(coderef)
                if impl:
                    attrs[m + '_' + s.value] = impl
    return type(name, (StateMachine, ), attrs)

def load_code_ref(spec: schema.CodeRefSpec, package=None):
    if spec.function and spec.code:
        raise AssertionError("Specify 'function' or 'code', but not both")
    if spec.function:
        mod, fn = spec.function.split(':')
        module = importlib.import_module(mod, package)
        return getattr(module, fn)
    if spec.code:
        # FIXME: make this configurable through dectate or something
        namespace = {'fastapi': fastapi,
                     'Request': fastapi.Request, 
                     'Collection': Collection, 
                     'get_collection': get_collection, 
                     'Model': Model}
        exec(spec.code, namespace)
        return namespace['function']
    return None


@validate_types
def generate_sqlalchemy_collection(app: fastapi.FastAPI,
                                   spec: schema.ModelSpec, 
                                   schema: type[pydantic.BaseModel], 
                                   table: sa.Table,
                                   name: str='Collection'):

    database = state.APP_STATE[app]['databases'][spec.storageType.database]['db']
    def constructor(self, request):
        SQLACollection.__init__(self, request, database=database, table=table)

    attrs = {
        'name': spec.name,
        'Schema': schema,
        '__init__': constructor       
    }
    for m in ['transform_create_data', 'transform_update_data', 
              'before_create', 'after_create', 
              'before_update', 'after_update', 
              'before_delete', 'after_delete']:
        
        coderef = getattr(spec, snake_to_camel(m), None)
        if coderef:
            impl = load_code_ref(coderef)
            if impl:
                attrs[m] = impl
    return typing.Annotated[type(name, (SQLACollection, ), attrs), fastapi.Depends(get_collection)]

@validate_types
def generate_pydantic_model(spec: schema.ModelSpec, name: str = 'Schema'):
    fields = {}
    stateMachine = spec.stateMachine
    for field_name, field_spec in spec.fields.items():
        data_type = PY_TYPES[field_spec.dataType.type]
        if field_spec.dataType.enum:
            data_type = enum.StrEnum(snake_to_pascal(field_name) + 'Enum',
                             dict(('key_%s' % i, e.value) for i, e in enumerate(field_spec.dataType.enum))
                        )
        if not field_spec.required:
            data_type = data_type | None

        if stateMachine and field_name == stateMachine.field:
            fields[field_name] = (data_type, stateMachine.initialState)
        else:
            fields[field_name] = (data_type, field_spec.default)
    
    return pydantic.create_model(
        name, 
        __base__=Model, 
        **fields
    )

@validate_types
def generate_sqlalchemy_table(app, spec: schema.ModelSpec) -> sa.Table:
    metadata = state.APP_STATE[app]['databases'][spec.storageType.database]['metadata']
    columns = []
    constraints = []
    for field_name, field_spec in spec.fields.items():
        c = get_sa_column(field_name, field_spec)
        columns.append(c)
        if field_spec.foreignKey:
            constraints.append(
                sa.ForeignKeyConstraint(
                    [field_name],
                    [field_spec.foreignKey]
                )
            )

    return create_table(
        spec.name,
        metadata,
        columns=columns,
        constraints=constraints
    )

def get_sa_column(field_name: str, field_spec: schema.FieldSpec):
    type_class = SA_TYPES[field_spec.dataType.type]
    type_args = []
    if field_spec.dataType.size:
        type_args.append(field_spec.dataType.size)
    type_kwargs = field_spec.dataType.sa_options or {}
    kwargs = {
        'nullable': not field_spec.required,
    }
    if field_spec.indexed:
        kwargs['index'] = field_spec.indexed
    if field_spec.unique:
        kwargs['unique'] = field_spec.unique
    args = [
        field_name,
        type_class(*type_args, **type_kwargs)
    ]
    return sa.Column(*args, **kwargs)


def register_views(app: fastapi.FastAPI):
    @app.exception_handler(AurelixException)
    async def search_exception_handler(request: fastapi.Request, exc: AurelixException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
    
    @app.exception_handler(sqlite3.IntegrityError)
    async def integrity_exception_handler(request: fastapi.Request, exc: Exception):
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc)},
        )
    
    @app.exception_handler(transitions.core.MachineError)
    async def sm_exception_handler(request: fastapi.Request, exc: Exception):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.value},
        )
    

    @app.get('/.well-known/aurelix-configuration', include_in_schema=False)
    async def aurelix_configuration(request: fastapi.Request) -> schema.WellKnownConfiguration:
        app = request.app
        settings = state.APP_STATE[app]['settings']
        models = state.APP_STATE[app]['models']
        oidc_settings = state.APP_STATE[app]['oidc_settings']
        cols = {}
        for name, spec in models.items():
            col = await get_collection(request, name)
            info = {
                'name': name,
                'schema': col.Schema.model_json_schema(),
                'links': {
                    'self': col.url()
                }
            }
            cols[name] = info
        return {
            'collections': cols,
            'openid-configuration': oidc_settings.model_dump()
        }