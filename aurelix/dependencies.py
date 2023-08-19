from . import state
from . import schema
import fastapi
import typing
from fastapi.security import OAuth2PasswordBearer
from . import exc
from .crud.base import BaseCollection
import httpx

def get_oidc_configuration(request: fastapi.Request):
    app = request.app
    oidc_settings = state.APP_STATE[app].get('oidc_settings', None)
    return oidc_settings

OIDCConfiguration = typing.Annotated[schema.OIDCConfiguration, fastapi.Depends(get_oidc_configuration)]

async def get_token(request: fastapi.Request, oidc_settings: OIDCConfiguration):
    app = request.app
    settings: schema.AppSpec = state.APP_STATE[app]['settings']
    if oidc_settings:
        if settings.oauth2_scheme == 'password':
            scheme = OAuth2PasswordBearer(oidc_settings.token_endpoint)
            token = await scheme(request)
            return schema.Token(access_token=token)
        elif settings.oauth2_scheme:
            raise exc.AurelixException("Unknown oauth2 scheme '%s'" % settings.oauth2_scheme)
    raise exc.AurelixException('OIDC is not configured')

Token = typing.Annotated[schema.Token, fastapi.Depends(get_token)]

async def get_userinfo(token: Token, oidc_settings: OIDCConfiguration):
    async with httpx.AsyncClient() as client:
        resp = await client.get(oidc_settings.userinfo_endpoint, headers={'Authorization': 'Bearer %s' % token.access_token})
        if resp.status_code != 200:
            raise exc.GatewayError('Unable to query OIDC userinfo endpoint (%s %s)' % (resp.status_code, resp.text))
        userinfo = resp.json()
        if ('email' not in userinfo):
            raise exc.GatewayError("OIDC userinfo endpoint did not provide 'email' property")
        if 'groups' not in userinfo:
            if 'roles' in userinfo:
                userinfo['groups'] = userinfo['roles']
        return schema.OIDCUserInfoResponse.model_validate(userinfo)

UserInfo = typing.Annotated[schema.OIDCUserInfoResponse, fastapi.Depends(get_userinfo)]


async def get_collection(request: fastapi.Request, name: str = None) -> BaseCollection:
    if name is None:
        comps = request.url.path.split('/')
        if len(comps) < 2:
            raise exc.CollectionNotFoundException(request.url.path)
        name = comps[1]
    if not name in request.app.collection:
        raise exc.CollectionNotFoundException(request.url.path)
    return request.app.collection[name](request)

Collection = typing.Annotated[BaseCollection, fastapi.Depends(get_collection)]

async def get_model(request: fastapi.Request, collection: Collection):
    if not 'identifier' in request.path_params:
        raise exc.AurelixException(r'{identifier} parameter is required on this route to resolve model')
    identifier = request.path_params['identifier']
    if identifier.startswith('+'):
        raise exc.RecordNotFoundException(identifier)
    obj = await collection.get(identifier)
    if not obj:
        raise exc.RecordNotFoundException(identifier)
    return obj

Model = typing.Annotated[schema.CoreModel, fastapi.Depends(get_model)]
