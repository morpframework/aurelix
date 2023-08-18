import fastapi
from fastapi.responses import JSONResponse
import os
import sys
import yaml
import sqlalchemy as sa
import pydantic
import importlib
from ..db.model import table as create_table
from ..utils import validate_types, snake_to_pascal, snake_to_camel
from ..crud.sqla import SQLACollection
from ..crud.base import StateMachine
from ..db.model import CoreModel
from ..crud.routes import register_collection
from ..exc import SearchException, AurelixException
from typing import Any
import sqlite3
import enum
import typing
import transitions 
import glob

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

class StorageTypeSpec(pydantic.BaseModel):
    name: str
    connId: str

class EnumSpec(pydantic.BaseModel):
    value: str
    label: str

class FieldTypeSpec(pydantic.BaseModel):
    type: str
    size: int | None = None
    enum: list[EnumSpec] | None = None
    sa_options: dict[str, object] | None = None

class FieldSpec(pydantic.BaseModel):
    title: str
    dataType: FieldTypeSpec
    required: bool = False
    default: Any = None
    indexed: bool = False
    unique: bool = False
    foreignKey: str | None = None

class ViewSpec(pydantic.BaseModel):
    enabled: bool = True

class RequestMethod(enum.StrEnum):
    POST = 'POST'
    GET = 'GET'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'
    OPTIONS = 'OPTIONS'

class CodeRefSpec(pydantic.BaseModel):
    function: str | None = None
    code: str | None = None

class ExtensionViewSpec(pydantic.BaseModel):
    method: RequestMethod
    summary: str | None = None
    tags: list[str] | None = None
    openapi_extra: dict[str, typing.Any] | None = None
    handler: CodeRefSpec

class ViewsSpec(pydantic.BaseModel):

    listing: ViewSpec = pydantic.Field(default_factory=ViewSpec)
    create: ViewSpec = pydantic.Field(default_factory=ViewSpec)
    read: ViewSpec = pydantic.Field(default_factory=ViewSpec)
    update: ViewSpec = pydantic.Field(default_factory=ViewSpec)
    delete: ViewSpec = pydantic.Field(default_factory=ViewSpec)
    extensions: dict[str, ExtensionViewSpec] | None = None

class StateMachineStateSpec(pydantic.BaseModel):
    value: str
    label: str

class StateMachineTransitionSpec(pydantic.BaseModel):
    trigger: str 
    label: str 
    source: str | list[str]
    dest: str
    onEnter: CodeRefSpec | None = None
    onExit: CodeRefSpec | None = None

class StateMachineSpec(pydantic.BaseModel):
    initialState: str
    field: str = 'workflowStatus'
    states: list[StateMachineStateSpec] 
    transitions: list[StateMachineTransitionSpec]

class ModelSpec(pydantic.BaseModel):

    name: str
    storageType: StorageTypeSpec
    fields: dict[str, FieldSpec]
    views: ViewsSpec = pydantic.Field(default_factory=ViewsSpec)
    tags: list[str]
    stateMachine: StateMachineSpec | None = None 
    beforeCreate: CodeRefSpec | None = None
    afterCreate: CodeRefSpec | None = None
    beforeUpdate: CodeRefSpec | None = None
    afterUpdate: CodeRefSpec | None = None 
    beforeDelete: CodeRefSpec | None = None
    afterDelete: CodeRefSpec | None = None
    transformCreateData: CodeRefSpec | None = None 
    transformUpdateData: CodeRefSpec | None = None 
    transformOutputData: CodeRefSpec | None = None

class AppSpec(pydantic.BaseModel):
    debug: bool = False
    title: str = "Aether"
    summary: str|None = None
    version: str = '0.1.0'
    docs_url: str = '/'
    redoc_url: str | None = None
    swagger_ui_oauth2_redirect_url: str = '/oauth2-redirect'
    terms_of_service: str | None = None
    model_directory: str | None = None

class Registry(dict):

    def __getattr__(self, __key: Any) -> Any:
        return self[__key]
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        self[__name] = __value

    def __delattr__(self, __name: str) -> None:
        del self[__name]
    
def load_app(path: str):
    from ..db import metadata # FIXME: should load dynamic from spec
    from ..db import engine
    with open(path) as f:
        spec: AppSpec = AppSpec.model_validate(yaml.safe_load(f))

    spec_dir = os.path.dirname(path)
    app = fastapi.FastAPI(debug=spec.debug, title=spec.title, summary=spec.summary, version=spec.version,
                          docs_url=spec.docs_url, redoc_url=spec.redoc_url, swagger_ui_oauth2_redirect_url=spec.swagger_ui_oauth2_redirect_url,
                          terms_of_service=spec.terms_of_service)
    load_app_models(app, os.path.join(spec_dir, spec.model_directory))
    register_exception_views(app)

    metadata.create_all(engine)

    return app


def load_app_models(app, directory_path):
    app.collection = Registry()
    for fn in glob.glob('*.yaml', root_dir=directory_path):
        res = load_model_spec(os.path.join(directory_path, fn))
        spec = res['spec']
        app.collection[snake_to_pascal(res['spec'].name)] = res['collection']
        app.collection[res['spec'].name] = res['collection']

        openapi_extra = {}
        if spec.tags:
            openapi_extra['tags'] = spec.tags
        register_collection(app, res['collection'], 
            listing_enabled=spec.views.listing.enabled,
            create_enabled=spec.views.create.enabled,
            read_enabled=spec.views.read.enabled,
            update_enabled=spec.views.update.enabled,
            delete_enabled=spec.views.delete.enabled,
            openapi_extra=openapi_extra
        )

def load_model_spec(path: str):

    with open(path) as f:
        spec = ModelSpec.model_validate(yaml.safe_load(f))

    result = {'spec': spec}
    model_type = spec.storageType.name
    Schema = generate_pydantic_model(spec,name=snake_to_pascal(spec.name))
    result['schema'] = Schema
    if model_type == 'sqlalchemy':
        table = generate_sqlalchemy_table(spec)
        result['table'] = table
        Collection = generate_sqlalchemy_collection(
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
    
def generate_statemachine(spec: ModelSpec, name: str = 'StateMachine'):
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

def load_code_ref(spec: CodeRefSpec, package=None):
    if spec.function and spec.code:
        raise AssertionError("Specify 'function' or 'code', but not both")
    if spec.function:
        mod, fn = spec.function.split(':')
        module = importlib.import_module(mod, package)
        return getattr(module, fn)
    if spec.code:
        namespace = {'Request': fastapi.Request}
        exec(spec.code, namespace)
        return namespace['function']
    return None


@validate_types
def generate_sqlalchemy_collection(spec: ModelSpec, 
                                   schema: type[pydantic.BaseModel], 
                                   table: sa.Table,
                                   name: str='Collection'):
    from ..db import database
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
    return type(name, (SQLACollection, ), attrs)

@validate_types
def generate_pydantic_model(spec: ModelSpec, name: str = 'Schema'):
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
        __base__=CoreModel, 
        **fields
    )

@validate_types
def generate_sqlalchemy_table(spec: ModelSpec) -> sa.Table:
    from ..db import metadata # FIXME: should load dynamic from spec
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

def get_sa_column(field_name: str, field_spec: FieldSpec):
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


def register_exception_views(app):
    @app.exception_handler(SearchException)
    async def search_exception_handler(request: fastapi.Request, exc: SearchException):
        return JSONResponse(
            status_code=422,
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
    
    