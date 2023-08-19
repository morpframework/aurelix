from . import schema
import fastapi
import typing
import databases

class AppState(typing.TypedDict):
    databases: dict[str, databases.Database]
    settings: schema.AppSpec
    oidc_settings: schema.OIDCConfiguration

APP_STATE: dict[fastapi.FastAPI, AppState] = {}


