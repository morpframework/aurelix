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
    settings: schema.AppSpec
    oidc_settings: schema.OIDCConfiguration
    models: dict[str, schema.ModelSpec]
    views: typing.Any # aurelix.crud.base.ExtensibleViewsApp
    oidc_jwk_client: jwt.PyJWKClient

APP_STATE: dict[fastapi.FastAPI, AppState] = {}


