from . import schema
import fastapi
import typing
import databases
import sqlalchemy as sa
import jwt

class DatabaseState(typing.TypedDict):
    engine: sa.engine.Engine
    metadata: sa.MetaData
    db: databases.Database

class AppState(typing.TypedDict):
    databases: dict[str, DatabaseState]
    db_engines: dict[str, sa.engine.Engine]
    settings: schema.AppSpec
    oidc_settings: schema.OIDCConfiguration
    models: dict[str, schema.ModelSpec]
    model_collections: dict[str, typing.Any] # aurelix.crud.base.BaseCollection
    views: typing.Any # aurelix.crud.base.ExtensibleViewsApp
    oidc_jwk_client: jwt.PyJWKClient
    object_stores: dict[str, typing.Any] # aurelix.crud.base.BaseObjectStore

APP_STATE: dict[fastapi.FastAPI, AppState] = {}


