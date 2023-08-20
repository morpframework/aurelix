from . import schema
import fastapi
import typing
import databases

class AppState(typing.TypedDict):
    databases: dict[str, databases.Database]
    settings: schema.AppSpec
    oidc_settings: schema.OIDCConfiguration
    models: dict[str, schema.ModelSpec]
    views: typing.Any # aurelix.crud.base.ExtensibleViewsApp

APP_STATE: dict[fastapi.FastAPI, AppState] = {}


