import fastapi
import httpx
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, SecurityScopes, OAuth2AuthorizationCodeBearer
import inspect
import os
import sys
import yaml
import sqlalchemy as sa
import sqlalchemy_utils as sautils
import pydantic
import importlib
from ..utils import validate_types, snake_to_pascal, snake_to_camel
from .sqla import SQLACollection, EncryptedString
from .asyncsqla import AsyncSQLACollection
from .base import StateMachine, ExtensibleViewsApp, BaseCollection, FieldObjectStore
from .routes import register_collection
from .dependencies import get_collection, Collection, Model, App
from .minios3 import MinioS3
from ..dependencies import Token
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
import databases.core
import datetime
from .base import ModelValidators, ModelFieldTransformers
import jwt
import logging

logger = logging.getLogger('aurelix.lowcode')

PY_TYPES = {
    'string': str,
    'text': str,
    'integer': int,
    'biginteger': int,
    'boolean': bool,
    'float': float,
    'datetime': datetime.datetime,
    'date': datetime.date,
    'encrypted-string': str,
    'json': dict
}

SA_TYPES={
    'string': sa.String,
    'text': sa.Text,
    'integer': sa.Integer,
    'biginteger': sa.BigInteger,
    'boolean': sa.Boolean,
    'float': sa.Float,
    'datetime': sa.types.DateTime,
    'date': sa.types.Date,
    'json': sautils.types.JSONType,
}

def get_sa_type_factory(field_name: str, app_spec: schema.AppSpec, field_spec: schema.FieldSpec):
    field_type = field_spec.dataType.type
    type_factory = SA_TYPES.get(field_type, None)
    if type_factory:
        return type_factory
    if field_type == 'encrypted-string':
        return EncryptedString(field_name, app_spec, field_spec)
    
    return type_factory


def create_table(name, metadata, columns=None, indexes=None, constraints=None, *args):
    columns = columns or []
    indexes = indexes or []
    constraints = constraints or []

    columns = [
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('dateCreated', sa.DateTime, default=datetime.datetime.utcnow, index=True),
        sa.Column('dateModified', sa.DateTime, default=datetime.datetime.utcnow, index=True),
        sa.Column('creator', sa.String(128), nullable=True, index=True),
        sa.Column('editor', sa.String(128), nullable=True, index=True),
    ] + columns

    return sa.Table(
        name,
        metadata,
        *columns,
        *indexes,
        *args
    )

async def load_app(path: str) -> fastapi.FastAPI:

    with open(path) as f:
        spec: schema.AppSpec = schema.AppSpec.model_validate(yaml.safe_load(f))

    if spec.spec_version != 'app/0.1':
        raise exc.AurelixException("Unsupported spec version %s" % spec.spec_version)
    spec_dir = os.path.dirname(path)
    init_oauth = {}
    if spec.swagger_ui_init_oauth:
        if spec.swagger_ui_init_oauth.client_id:
            init_oauth['clientId'] = spec.swagger_ui_init_oauth.client_id
        if spec.swagger_ui_init_oauth.client_secret:
            init_oauth['clientSecret'] = spec.swagger_ui_init_oauth.client_secret
        if init_oauth.keys() and spec.title:
            init_oauth['appName'] = spec.title

    app = App(debug=spec.debug, title=spec.title, summary=spec.summary, version=spec.version,
                          docs_url=spec.docs_url, redoc_url=spec.redoc_url, 
                          swagger_ui_oauth2_redirect_url=spec.swagger_ui_oauth2_redirect_url,
                          terms_of_service=spec.terms_of_service,
                          swagger_ui_init_oauth=init_oauth or None)
    state.APP_STATE.setdefault(app, {})
    state.APP_STATE[app]['settings'] = spec
    state.APP_STATE[app]['views'] = ExtensibleViewsApp()

    if spec.libs_directory:
        ld_path = os.path.join(spec_dir, spec.libs_directory)
        if os.path.exists(ld_path):
            sys.path.append(ld_path)

    for d in spec.databases:
        metadata = sa.MetaData()
        if d.url:
            url = d.url
        elif d.url_env:
            url = os.environ[d.url_env]
        else:
            raise exc.AurelixException("Missing url or url_env")
        connect_args = {}

        # FIXME: this check may be flaky
        is_mssql = url.lower().startswith('mssql')
        logger.warn('MSSQL support is limited to synchronous API')
        if not is_mssql:
            connect_args["check_same_thread"] = False
        engine = sa.create_engine(
            url, connect_args=connect_args
        )
        db = None

        # FIXME: this check may be flaky
        if not is_mssql:
            db = databases.Database(url)
        state.APP_STATE[app].setdefault('databases', {})
        state.APP_STATE[app]['databases'][d.name] = {
            'metadata': metadata,
            'engine': engine,
            'db': db
        }

    for o in (spec.objectStores or []):
        if o.endpoint_url:
            endpoint_url = o.endpoint_url
        elif o.endpoint_url_env:
            endpoint_url = os.environ[o.endpoint_url_env]
        else:
            raise exc.AurelixException("Missing server endpoint")
        
        if o.access_key:
            access_key = o.access_key
        elif o.access_key_env:
            access_key = os.environ[o.access_key_env]
        else:
            raise exc.AurelixException("Missing access key")

        if o.secret_key:
            secret_key = o.secret_key
        elif o.secret_key_env:         
            secret_key = os.environ[o.secret_key_env]
        else:
            raise exc.AurelixException("Missing secret key")

        state.APP_STATE[app].setdefault('object_stores', {})
        state.APP_STATE[app]['object_stores'][o.name] = MinioS3(
            endpoint_url, access_key, secret_key
        )

    if spec.model_directory:
        md_path = os.path.join(spec_dir, spec.model_directory)
        if os.path.exists(md_path):
            load_app_models(app, md_path)

    for d in spec.databases:
        dbconf = state.APP_STATE[app]['databases'][d.name]
        if d.auto_initialize:
            dbconf['metadata'].create_all(dbconf['engine'])

    env_settings = Settings()
    oidc_discovery_endpoint = spec.oidc_discovery_endpoint or env_settings.OIDC_DISCOVERY_ENDPOINT
    if oidc_discovery_endpoint:
        async with httpx.AsyncClient() as client:
            resp = await client.get(oidc_discovery_endpoint)
            if resp.status_code != 200:
                raise exc.GatewayError("Unable to get OIDC discovery metadata")
            oidc_settings = schema.OIDCConfiguration.model_validate(resp.json())
            state.APP_STATE[app]['oidc_settings'] = oidc_settings
            if not oidc_settings.jwks_uri:
                raise exc.GatewayError("No JWKS URL provided by OIDC metadata")
            state.APP_STATE[app]['oidc_jwk_client'] = jwt.PyJWKClient(oidc_settings.jwks_uri, cache_keys=True)
        
    register_views(app, spec)

    return app

def db_upgrade(app: App):
    for m in state.APP_STATE[app]['databases'].values():
        metadata = m['metadata']
        engine = m['engine']
        metadata.create_all(engine)


def load_app_models(app: App, directory_path):
    model_specs = {}
    for fn in glob.glob('*.yaml', root_dir=directory_path):

        with open(os.path.join(directory_path, fn)) as f:
            model_spec = schema.ModelSpec.model_validate(yaml.safe_load(f))
        model_specs[model_spec.name] = model_spec
    state.APP_STATE[app]['models'] = model_specs

    for n, spec in model_specs.items():
        spec: schema.ModelSpec = spec
        res = load_model_spec(app, spec)
        app.collection[snake_to_pascal(res['spec'].name)] = res['collection']
        app.collection[res['spec'].name] = res['collection']

        openapi_extra = {}
        if spec.tags:
            openapi_extra['tags'] = spec.tags
        state.APP_STATE[app].setdefault('model_collections', {})
        state.APP_STATE[app]['model_collections'][spec.name] = res['collection']

    for name, col in state.APP_STATE[app]['model_collections'].items():
        spec = state.APP_STATE[app]['models'][name]
        register_collection(app, col, 
            listing_enabled=spec.views.listing.enabled,
            create_enabled=spec.views.create.enabled,
            read_enabled=spec.views.read.enabled,
            update_enabled=spec.views.update.enabled,
            delete_enabled=spec.views.delete.enabled,
            openapi_extra=openapi_extra,
            max_page_size=spec.views.listing.maxPageSize,
        )

def load_model_spec(app: App, spec: schema.ModelSpec):

    result = {'spec': spec}
    model_type = spec.storageType.name
    Schema = generate_pydantic_model(spec,name=snake_to_pascal(spec.name))
    result['schema'] = Schema
    if model_type in ['sqlalchemy-sync', 'sqlalchemy']:
        table = generate_sqlalchemy_table(app, spec)
        result['table'] = table
        Collection = generate_sqlalchemy_collection(
            app,
            spec, Schema, table, 
            name=snake_to_pascal(spec.name))
        result['collection'] = Collection
    else:
        raise exc.AurelixException("Unknown model type %s" % model_type)
    
    Collection.spec = spec
    validators = {'model': None, 'fields': {}}
    field_transformers = {'inputTransformers': {}, 'outputTransformers': {}}
    if spec.validators:
        impl = load_multi_code_ref(spec.validators)
        validators['model'] = impl
    for field_name, field in spec.fields.items():
        if field.validators:
            impl = load_multi_code_ref(field.validators)
            validators['fields'][field_name] = impl
        if field.inputTransformers:
            impl = load_transform_code_ref(field.inputTransformers)
            field_transformers['inputTransformers'][field_name] = impl
        if field.outputTransformers:
            impl = load_transform_code_ref(field.outputTransformers)
            field_transformers['outputTransformers'][field_name] = impl
    Collection.validators = ModelValidators.model_validate(validators)
    Collection.fieldTransformers = ModelFieldTransformers.model_validate(field_transformers)

    field_object_store = {}
    if spec.objectStore:
        for k,v in spec.objectStore.items():
            impl = state.APP_STATE[app]['object_stores'][v.objectStore]
            field_object_store[k] = {
                'bucket': v.bucket,
                'objectStore': impl
            }
    
    Collection.objectStore = field_object_store
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
                impl = load_multi_code_ref(coderef)
                if impl:
                    attrs[m + '_' + s.value] = impl
    return type(name, (StateMachine, ), attrs)

def load_multi_code_ref(coderefs: list[schema.CodeRefSpec] | schema.CodeRefSpec, package=None):
    impls = []
    if type(coderefs) != list:
        coderefs = [coderefs]
    for coderef in coderefs:
        impl = load_code_ref(coderef, package)
        if impl:
            impls.append(impl)
    if impls:
        async def wrapper(*args, **kwargs):
            for i in impls:
                if inspect.iscoroutinefunction(impl):
                    await impl(*args, **kwargs) # type: ignore 
                else:
                    impl(*args, **kwargs)
        return wrapper
    return None

def load_transform_code_ref(coderefs: list[schema.CodeRefSpec] | schema.CodeRefSpec, package=None):
    impls = []
    if type(coderefs) != list:
        coderefs = [coderefs]
    for coderef in coderefs:
        impl = load_code_ref(coderef, package)
        if impl:
            impls.append(impl)
    if impls:
        async def wrapper(self, obj: dict, *args, **kwargs) -> dict:
            for i in impls:
                if inspect.iscoroutinefunction(impl):
                    obj = await impl(self, obj, *args, **kwargs) # type: ignore 
                else:
                    obj = impl(self, obj, *args, **kwargs)
            return obj
        return wrapper
    return None

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
                     'App': App,
                     'Token': Token,
                     'Collection': Collection, 
                     'get_collection': get_collection, 
                     'Model': Model}
        exec(spec.code, namespace)
        return namespace[spec.function_name]
    return None


@validate_types
def generate_sqlalchemy_collection(app: App,
                                   spec: schema.ModelSpec, 
                                   schema: type[pydantic.BaseModel], 
                                   table: sa.Table,
                                   name: str='Collection'):

    database = state.APP_STATE[app]['databases'][spec.storageType.database]['db']
    engine = state.APP_STATE[app]['databases'][spec.storageType.database]['engine']
    if spec.storageType.name == 'sqlalchemy-sync':
        BaseClass = SQLACollection
        def constructor(self, request):
            SQLACollection.__init__(self, request, engine=engine, table=table)
    elif spec.storageType.name == 'sqlalchemy':
        BaseClass = AsyncSQLACollection
        def constructor(self, request):
            AsyncSQLACollection.__init__(self, request, database=database, table=table)

    attrs = {
        'name': spec.name,
        'Schema': schema,
        'permissionFilters': spec.permissionFilters,
        'defaultFieldPermission': spec.defaultFieldPermission,
        '__init__': constructor       
    }
    for m in ['before_create', 'after_create', 
              'before_update', 'after_update', 
              'before_delete', 'after_delete']:
        
        coderef = getattr(spec, snake_to_camel(m), None)
        if coderef:
            impl = load_multi_code_ref(coderef)
            if impl:
                attrs[m] = impl

    for m in ['transform_create_data', 'transform_update_data',
              'transform_output_data']:
        coderef = getattr(spec, snake_to_camel(m), None)
        if coderef:
            impl = load_transform_code_ref(coderef)
            if impl:
                attrs['_' + m] = impl
    async def _get_collection(request: fastapi.Request):
        return await get_collection(request)
    
    return typing.Annotated[type(name, (BaseClass, ), attrs), fastapi.Depends(_get_collection)]

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
    app_spec = state.APP_STATE[app]['settings']
    columns = []
    constraints = []
    for field_name, field_spec in spec.fields.items():
        c = get_sa_column(field_name, app_spec, field_spec)
        columns.append(c)
        if field_spec.relation:
            if field_spec.relation.constraint:
                relation_spec = state.APP_STATE[app]['models'][field_spec.relation.model]
                if (relation_spec.storageType.name not in ['sqlalchemy', 'sqlalchemy-sync'] and
                    relation_spec.storageType.database != spec.storageType.database):
                    raise exc.AurelixException("Unable to set foreign key constraint across different storage type or database")
                constraints.append(
                    sa.ForeignKeyConstraint(
                        [field_name],
                        ['%s.%s' % (relation_spec.name,field_spec.relation.field)]
                    )
                )

    return create_table(
        spec.name,
        metadata,
        columns=columns,
        constraints=constraints
    )



def get_sa_column(field_name: str, app_spec: schema.AppSpec, field_spec: schema.FieldSpec):
    type_factory = get_sa_type_factory(field_name, app_spec, field_spec)
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
        type_factory(*type_args, **type_kwargs)
    ]
    return sa.Column(*args, **kwargs)


def register_views(app: App, spec: schema.AppSpec):
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
    
    if spec.views.well_known_config.enabled:
        @app.get('/.well-known/aurelix-configuration', include_in_schema=False)
        async def aurelix_configuration(request: fastapi.Request) -> schema.WellKnownConfiguration:
            app = request.app
            settings = state.APP_STATE[app]['settings']
            models = state.APP_STATE[app]['models']
            oidc_settings = state.APP_STATE[app].get('oidc_settings', None)
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
                if spec.stateMachine:
                    info['stateMachine'] = {
                        'triggers': [{'name': t.trigger, 'label': t.label, 'source': t.source} for t in spec.stateMachine.transitions], 
                        'states': [{'name': s.value, 'label': s.label} for s in spec.stateMachine.states],
                        'field': spec.stateMachine.field
                    }
                cols[name] = info
            result = {
                'collections': cols
            }
            if oidc_settings:
                result['openid-configuration'] = oidc_settings.model_dump()
            return result

    views_app: ExtensibleViewsApp = state.APP_STATE[app]['views']
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
                    views_app.view(vpath, **view_opts)(impl)
        
        _routes = views_app.routes()
        for r in _routes:
            path = r['path']
            getattr(app, r['method'])(path, **r['options'])(r['function'])

